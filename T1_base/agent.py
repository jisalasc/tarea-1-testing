# Orquestador del agente: python agent.py <ruta_archivo_objetivo> <carpeta_salida>.
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

import extractor
import prompts
import runners
from llm import LLMClient, LLMError, extract_code

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

BUDGET_SECONDS = 240.0
FINALIZE_RESERVE = 8.0
MIN_SECONDS_FOR_LLM_CYCLE = 20.0
MAX_REPAIR_ROUNDS = 2
MAX_MUTATION_SECONDS = 40.0
MIN_MUTATION_SECONDS = 8.0
REPAIR_TEMPERATURES = [0.3, 0.6]
CHAOS = os.getenv("AGENT_CHAOS", "")


# ---------------------------------------------------------------------------
# Bitácora
# ---------------------------------------------------------------------------
# Registra eventos con marca de tiempo y los guarda en run_log.json.
class RunLog:

    # Fija el instante cero de la corrida.
    def __init__(self, t0: float):
        self.t0 = t0
        self.events: list[dict] = []
        self.summary: dict = {}

    # Agrega un evento y lo imprime en consola.
    def add(self, kind: str, **data):
        t = round(time.monotonic() - self.t0, 2)
        self.events.append({"t": t, "kind": kind, **data})
        extra = " ".join(f"{k}={v}" for k, v in data.items() if k != "detail")
        print(f"[{t:6.1f}s] {kind:<12} {extra}")
        if "detail" in data:
            print(f"           {str(data['detail'])[:300]}")

    # Escribe resumen y eventos a un archivo JSON.
    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"summary": self.summary, "events": self.events}, fh,
                      indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Ensamblaje y manipulación del archivo de test
# ---------------------------------------------------------------------------
_SYS_PATH_LINE = re.compile(r"^\s*(sys\.path\.(insert|append)\(|os\.chdir\()")
_FUTURE_LINE = re.compile(r"^from __future__ import ")


# Une la cabecera de sys.path con el código del LLM, quitando líneas prohibidas.
def assemble_test_file(header: str, code: str) -> str:
    futures, body = [], []
    for line in code.splitlines():
        if _FUTURE_LINE.match(line):
            futures.append(line)
        elif _SYS_PATH_LINE.match(line):
            body.append("# (línea eliminada por el agente: no se permite tocar sys.path)")
        else:
            body.append(line)
    parts = []
    if futures:
        parts.append("\n".join(futures) + "\n")
    parts.append(header)
    parts.append("\n".join(body).rstrip() + "\n")
    return "\n".join(parts)


# Nombres de función de los tests que fallaron, sin el sufijo de parametrización.
def _failing_test_names(pr: runners.PytestResult) -> set[str]:
    names = set()
    for f in pr.failures:
        last = f["nodeid"].split("::")[-1]
        names.add(last.split("[")[0])
    return names


# Borra por AST las funciones de test que fallan; devuelve (código podado, nombres).
def prune_failing_tests(code: str, pr: runners.PytestResult) -> tuple[str | None, list[str]]:
    failing = _failing_test_names(pr)
    if not failing:
        return None, []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None, []
    lines = code.splitlines()
    to_delete: list[tuple[int, int]] = []
    removed: list[str] = []
    remaining_tests = 0

    # Recorre funciones de test a nivel módulo y dentro de clases.
    def visit_body(body):
        nonlocal remaining_tests
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                if node.name in failing:
                    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
                    to_delete.append((start, node.end_lineno))
                    removed.append(node.name)
                else:
                    remaining_tests += 1
            elif isinstance(node, ast.ClassDef):
                visit_body(node.body)

    visit_body(tree.body)
    if not removed or remaining_tests == 0:
        return None, removed
    for start, end in sorted(to_delete, reverse=True):
        del lines[start - 1:end]
    pruned = "\n".join(lines).rstrip() + "\n"
    try:
        ast.parse(pruned)
    except SyntaxError:
        return None, removed
    return pruned, removed


# Test mínimo de respaldo: importa el módulo y verifica que existen los nombres públicos.
def emergency_test(t: extractor.Target) -> str:
    names = t.public_names or []
    body = [f"import {t.import_module} as target_module", "", "",
            "def test_module_imports():", "    assert target_module is not None", ""]
    for n in names:
        body += [f"def test_{n}_exists():", f"    assert hasattr(target_module, {n!r})", ""]
    return "\n".join(body)


# Escribe metrics.json con las tres métricas exigidas.
def write_metrics(output_folder: str, line_cov: float, branch_cov: float, mutation: float):
    with open(os.path.join(output_folder, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump({"line_coverage": round(line_cov, 4), "branch_coverage": round(branch_cov, 4),
                   "mutation_score": round(mutation, 4)}, fh, indent=2)


# Decide si un resultado de pytest es mejor que otro: verde, luego sano, luego más passed.
def _better(new: runners.PytestResult, old: runners.PytestResult) -> bool:
    if new.ok != old.ok:
        return new.ok
    new_broken = bool(new.collection_error) or new.timed_out
    old_broken = bool(old.collection_error) or old.timed_out
    if new_broken != old_broken:
        return not new_broken
    return new.passed > old.passed


# Agrega dos tests rotos al código generado (solo desarrollo, AGENT_CHAOS).
def _inject_chaos(code: str, t: extractor.Target) -> str:
    return code.rstrip() + f"""


def test_chaos_wrong_expectation():
    assert 1 + 1 == 3


def test_chaos_missing_attr():
    import {t.import_module} as _m
    _m.this_method_does_not_exist()
"""


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
# Corre la máquina de estados completa y devuelve 0 si el test final quedó verde.
def main(ruta_archivo: str, output_folder: str) -> int:
    t0 = time.monotonic()
    deadline = t0 + BUDGET_SECONDS
    llm_deadline = deadline - FINALIZE_RESERVE
    log = RunLog(t0)
    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    work_dir = os.path.join(output_folder, ".agent_work")
    os.makedirs(work_dir, exist_ok=True)

    # Segundos que quedan para usar el LLM.
    def remaining() -> float:
        return llm_deadline - time.monotonic()

    # ---- SETUP -----------------------------------------------------------
    target = extractor.load_target(ruta_archivo)
    test_path = os.path.join(output_folder, target.test_file_name)
    header = extractor.build_header(target)
    log.add("setup", project=target.project_name, module=target.module_name,
            import_style=target.import_style, import_module=target.import_module,
            public=len(target.public_names), sketch_chars=len(target.dependency_sketch))
    if target.import_style == "unknown":
        log.add("warning", detail=f"ningún estilo de import funcionó: {target.import_error}")

    # Escribe el test en disco y lo corre con pytest.
    def write_and_validate(code: str, tag: str) -> runners.PytestResult:
        with open(test_path, "w", encoding="utf-8") as fh:
            fh.write(assemble_test_file(header, code))
        pr = runners.run_pytest(test_path, cwd=output_folder)
        log.add("validate", stage=tag, ok=pr.ok, passed=pr.passed, failed=pr.failed, errors=pr.errors,
                collection_error=bool(pr.collection_error), secs=round(pr.duration, 1))
        if not pr.ok:
            for f in pr.failures[:5]:
                print(f"             - {f['kind']} {f['nodeid'].split('::')[-1]}: {f['message'][:90]}")
            if pr.collection_error:
                print("             " + pr.collection_error.strip().splitlines()[-1][:150])
        return pr

    # Manda un prompt al LLM, guarda prompt y respuesta, y devuelve el código extraído.
    def call_llm(prompt: str, tag: str, temperature: float) -> str | None:
        with open(os.path.join(work_dir, f"prompt_{tag}.md"), "w", encoding="utf-8") as fh:
            fh.write(prompt)
        log.add(tag, prompt_chars=len(prompt), temperature=temperature)
        try:
            res = llm.generate(prompt, deadline=llm_deadline, temperature=temperature)
        except LLMError as e:
            log.add("llm_error", stage=tag, detail=str(e))
            return None
        log.add("llm_done", stage=tag, attempts=res.attempts, latency=round(res.latency, 1),
                first_token=round(res.first_token_latency or 0, 1), out_tokens=res.output_tokens,
                finish=res.finish_reason, events=res.events)
        with open(os.path.join(work_dir, f"response_{tag}.md"), "w", encoding="utf-8") as fh:
            fh.write(res.text)
        return extract_code(res.text)

    llm = LLMClient()
    outcome = "emergency"
    rounds_used = 0
    pruned_names: list[str] = []

# ---- GENERATE ----------------------------------------------------------
    code = call_llm(prompts.generation_prompt(target), "generate", temperature=0.3)
    if code is None:
        # Extraer el detalle del error desde el último evento registrado en el log
        last_err = log.events[-1].get("detail", "") if log.events else ""
        
        # Si el error contiene 503 o 504, imprimimos en consola, escribimos el JSON y abortamos
        if "503" in last_err or "504" in last_err or "Timeout" in last_err:
            print(f"\n[!] ERROR CRÍTICO DE API: {last_err}")
            with open(os.path.join(output_folder, "metrics.json"), "w", encoding="utf-8") as fh:
                json.dump({"error": "High demand"}, fh, indent=2)
            return 2
        
        # Si falló por otro motivo ajeno a la API, recurre al test de emergencia
        code = emergency_test(target)
        pr = write_and_validate(code, "emergency")
    else:
        if CHAOS:
            code = _inject_chaos(code, target)
            log.add("chaos", detail="se inyectaron 2 tests rotos (AGENT_CHAOS)")
        pr = write_and_validate(code, "generate")
        if pr.ok:
            outcome = "green_first_shot"

        # ---- REPAIR loop -----------------------------------------------------
        max_rounds = 0 if CHAOS == "prune" else MAX_REPAIR_ROUNDS
        while not pr.ok and rounds_used < max_rounds:
            if remaining() < MIN_SECONDS_FOR_LLM_CYCLE:
                log.add("repair_skip", detail=f"quedan {remaining():.0f}s; no alcanza para otra ronda")
                break
            rounds_used += 1
            temp = REPAIR_TEMPERATURES[min(rounds_used, len(REPAIR_TEMPERATURES)) - 1]
            new_code = call_llm(prompts.repair_prompt(target, code, pr), f"repair{rounds_used}", temp)
            if new_code is None:
                break
            new_pr = write_and_validate(new_code, f"repair{rounds_used}")
            if _better(new_pr, pr):
                code, pr = new_code, new_pr
            else:
                log.add("repair_worse", detail="la reparación no mejoró; se conserva la versión anterior")
                with open(test_path, "w", encoding="utf-8") as fh:
                    fh.write(assemble_test_file(header, code))
        if pr.ok and rounds_used:
            outcome = "green_after_repair"

        # ---- PRUNE -------------------------------------------------------------
        if not pr.ok:
            pruned, pruned_names = prune_failing_tests(code, pr)
            if pruned is not None:
                log.add("prune", removed=len(pruned_names), detail=", ".join(pruned_names))
                pr2 = write_and_validate(pruned, "prune")
                if pr2.ok:
                    code, pr = pruned, pr2
                    outcome = "green_after_prune"
            if not pr.ok:
                log.add("emergency", detail="ni reparar ni podar dejó el archivo verde; se escribe test de emergencia")
                code = emergency_test(target)
                pr = write_and_validate(code, "emergency")
                outcome = "emergency"

    # ---- MEASURE & ENHANCE -------------------------------------------------
    cov = runners.run_coverage(test_path, cwd=output_folder, target_file=target.file_path, work_dir=work_dir)
    log.add("measure_initial", lines=f"{cov.line_coverage:.1%}", branches=f"{cov.branch_coverage:.1%}",
            missing_lines=len(cov.missing_lines), secs=round(cov.duration, 1),
            error=cov.error[:80] if cov.error else "")

    # Si no cumple el umbral y queda tiempo, pedimos tests adicionales
    if (cov.line_coverage < 0.80 or cov.branch_coverage < 0.50) and remaining() > MIN_SECONDS_FOR_LLM_CYCLE:
        log.add("enhance", detail="Cobertura bajo umbral. Solicitando nuevos tests al LLM...")
        new_tests = call_llm(prompts.enhance_prompt(target, code, cov.missing_lines), "enhance", temperature=0.4)
        
        if new_tests:
            enhanced_code = code.rstrip() + "\n\n" + new_tests.strip() + "\n"
            pr_enhance = write_and_validate(enhanced_code, "enhance_validate")
            
            if pr_enhance.ok:
                code, pr = enhanced_code, pr_enhance
                outcome = "green_after_enhance"
                # Volvemos a medir para actualizar metrics.json con el resultado mejorado
                cov = runners.run_coverage(test_path, cwd=output_folder, target_file=target.file_path, work_dir=work_dir)
                log.add("measure_final", lines=f"{cov.line_coverage:.1%}", branches=f"{cov.branch_coverage:.1%}")
            else:
                log.add("enhance_reject", detail="Los tests adicionales fallaron. Revirtiendo cambios.")
                write_and_validate(code, "rollback")

    # ---- MUTATE ------------------------------------------------------------
    mut = runners.MutationResult()
    mut_budget = min(MAX_MUTATION_SECONDS, deadline - FINALIZE_RESERVE - time.monotonic())
    if mut_budget < MIN_MUTATION_SECONDS:
        mut.error = f"sin presupuesto para cosmic-ray ({mut_budget:.0f}s)"
        log.add("mutate_skip", detail=mut.error)
    else:
        log.add("mutate", budget=f"{mut_budget:.0f}s")
        mut = runners.run_mutation(test_path, cwd=output_folder, target_file=target.file_path,
                                   work_dir=work_dir, time_budget=mut_budget)
        log.add("mutate_done", score=f"{mut.mutation_score:.1%}", completed=f"{mut.completed}/{mut.total_mutants}",
                killed=mut.killed, survived=mut.survived, incompetent=mut.incompetent,
                sampled=mut.timed_out, secs=round(mut.duration, 1), error=mut.error[:80] if mut.error else "")
        if mut.file_restored:
            log.add("warning", detail="cosmic-ray dejó el objetivo mutado; se restauró desde el snapshot")

    # ---- FINALIZE ------------------------------------------------------------
    write_metrics(output_folder, cov.line_coverage, cov.branch_coverage, mut.mutation_score)
    with open(os.path.join(work_dir, "metrics_detail.json"), "w", encoding="utf-8") as fh:
        json.dump({"coverage": cov.__dict__, "mutation": mut.__dict__}, fh, indent=2, default=str)
    total = time.monotonic() - t0
    log.summary = {
        "outcome": outcome, "green": pr.ok, "repair_rounds": rounds_used,
        "pruned_tests": pruned_names, "tests_passed": pr.passed,
        "line_coverage": cov.line_coverage, "branch_coverage": cov.branch_coverage,
        "mutation_score": mut.mutation_score, "mutants_completed": mut.completed,
        "mutants_total": mut.total_mutants, "mutation_sampled": mut.timed_out,
        "total_seconds": round(total, 1),
        "llm_calls": sum(1 for e in log.events if e["kind"] == "llm_done"),
    }
    log.add("finalize", outcome=outcome, tests=pr.passed, rounds=rounds_used, total=f"{total:.1f}s")
    log.save(os.path.join(work_dir, "run_log.json"))
    return 0 if pr.ok else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente basado en LLM para generación iterativa de tests.")
    parser.add_argument("ruta_archivo", type=str, help="Ruta al archivo objetivo (ej. Public_Proyects/blackjack/dealer.py)")
    parser.add_argument("output_folder", type=str, help="Carpeta de salida (ej. Results/blackjack/dealer)")
    args = parser.parse_args()
    sys.exit(main(args.ruta_archivo, args.output_folder))
