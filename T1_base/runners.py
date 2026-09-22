# Ejecuta pytest, coverage y cosmic-ray en subprocesos (cwd = carpeta de salida) y parsea sus salidas.
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field

_ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
PYTEST_BASE = ["-q", "--tb=short", "-rfE", "--no-header", "-p", "no:cacheprovider", "-o", "addopts="]
PYTEST_VALIDATE = ["-v", *PYTEST_BASE[1:]]
PYTEST_TIMEOUT = 20.0

_VERBOSE_LINE_RE = re.compile(r"^(\S+::\S+)(?:\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS))?", re.MULTILINE)
_SUMMARY_RE = re.compile(r"(\d+) (passed|failed|error)s?")
_SECTION_RE = re.compile(r"^_{3,} (.+?) _{3,}$", re.MULTILINE)
_SHORT_RE = re.compile(r"^(FAILED|ERROR) (\S+?)(?: - (.*))?$", re.MULTILINE)

MUTATION_TOML = '''[cosmic-ray]
module-path = "{target}"
timeout = {per_test_timeout}
excluded-modules = []
test-command = "{python} -m pytest -q -x -p no:cacheprovider -o addopts= {test_basename}"

[cosmic-ray.distributor]
name = "local"
'''


# Resultado de una corrida de pytest: conteos, fallos con traceback y estado del proceso.
@dataclass
class PytestResult:
    ok: bool
    returncode: int
    passed: int = 0
    failed: int = 0
    errors: int = 0
    failures: list[dict] = field(default_factory=list)
    collection_error: str = ""
    stdout: str = ""
    duration: float = 0.0
    timed_out: bool = False

    # Resumen de una línea para prompts y logs.
    @property
    def summary(self) -> str:
        if self.timed_out:
            return "pytest: timeout"
        if self.collection_error:
            return "pytest: error de colección (sintaxis/import)"
        return f"pytest: {self.passed} passed, {self.failed} failed, {self.errors} errors (rc={self.returncode})"


# Corre pytest -v sobre el archivo de test y devuelve el resultado parseado.
def run_pytest(test_file: str, cwd: str, timeout: float = PYTEST_TIMEOUT) -> PytestResult:
    t0 = time.monotonic()
    cmd = [sys.executable, "-m", "pytest", *PYTEST_VALIDATE, os.path.basename(test_file)]
    try:
        r = subprocess.run(cmd, cwd=cwd, env=_ENV, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return _timeout_result(out, timeout, time.monotonic() - t0)
    out = r.stdout + ("\n" + r.stderr if r.stderr.strip() else "")
    res = PytestResult(ok=(r.returncode == 0), returncode=r.returncode, stdout=out,
                       duration=time.monotonic() - t0)
    _parse_pytest(res)
    if r.returncode == 5:
        res.ok = False
        res.collection_error = res.collection_error or "pytest no recolectó ningún test"
    return res


# Con pytest colgado, cuenta lo que alcanzó a pasar y marca como TIMEOUT al test culpable.
def _timeout_result(partial_stdout: str, timeout: float, duration: float) -> PytestResult:
    res = PytestResult(ok=False, returncode=-1, stdout=partial_stdout, duration=duration, timed_out=True)
    hanging = None
    for nodeid, status in _VERBOSE_LINE_RE.findall(partial_stdout):
        if status == "PASSED":
            res.passed += 1
        elif status in ("FAILED", "ERROR"):
            res.failed += 1
            res.failures.append({"kind": status, "nodeid": nodeid, "message": "(ver salida parcial)", "traceback": ""})
        elif not status:
            hanging = nodeid
    if hanging:
        res.failed += 1
        res.failures.append({"kind": "TIMEOUT", "nodeid": hanging,
                             "message": f"el test no terminó: pytest fue cortado a los {timeout:.0f}s "
                                        f"(bucle infinito, entrada enorme o llamada bloqueante)",
                             "traceback": ""})
    return res


# Extrae del stdout los conteos, los fallos con su traceback y el error de colección si hubo.
def _parse_pytest(res: PytestResult) -> None:
    out = res.stdout
    for n, kind in _SUMMARY_RE.findall(out):
        setattr(res, {"passed": "passed", "failed": "failed", "error": "errors"}[kind], int(n))

    sections: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(out))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(out)
        body = out[m.end():end]
        body = re.split(r"^={3,} .* ={3,}$", body, maxsplit=1, flags=re.MULTILINE)[0]
        sections[m.group(1).strip()] = body.strip()

    for kind, nodeid, msg in _SHORT_RE.findall(out):
        name = nodeid.split("::")[-1]
        name_base = name.split("[")[0]
        tb = sections.get(name) or sections.get(name_base) or ""
        if not tb:
            for k, v in sections.items():
                if k.startswith(name_base):
                    tb = v
                    break
        res.failures.append({"kind": kind, "nodeid": nodeid, "message": msg or "", "traceback": tb[:1500]})

    if "error" in out.lower() and ("ERROR collecting" in out or "ImportError" in out and res.passed == 0
                                   or "SyntaxError" in out and res.passed == 0):
        m = re.search(r"={3,} ERRORS ={3,}\n(.*?)(?:\n={3,} |\Z)", out, re.DOTALL)
        res.collection_error = (m.group(1) if m else out)[:3000]


# Cobertura de líneas y ramas del archivo objetivo.
@dataclass
class CoverageResult:
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    num_statements: int = 0
    covered_lines: int = 0
    num_branches: int = 0
    covered_branches: int = 0
    missing_lines: list[int] = field(default_factory=list)
    missing_branches: list[list[int]] = field(default_factory=list)
    error: str = ""
    duration: float = 0.0

    # Resumen de una línea para prompts y logs.
    @property
    def summary(self) -> str:
        if self.error:
            return f"coverage: ERROR {self.error[:120]}"
        return (f"coverage: líneas {self.line_coverage:.1%} ({self.covered_lines}/{self.num_statements}), "
                f"ramas {self.branch_coverage:.1%} ({self.covered_branches}/{self.num_branches})")


# Corre pytest bajo coverage (con ramas) y lee las métricas del archivo objetivo desde el JSON.
def run_coverage(test_file: str, cwd: str, target_file: str, work_dir: str,
                 timeout: float = 45.0) -> CoverageResult:
    t0 = time.monotonic()
    work_dir, target_file, cwd = map(os.path.abspath, (work_dir, target_file, cwd))
    os.makedirs(work_dir, exist_ok=True)
    data_file = os.path.join(work_dir, ".coverage")
    json_path = os.path.join(work_dir, "coverage.json")
    res = CoverageResult()
    run_cmd = [sys.executable, "-m", "coverage", "run", "--branch", f"--data-file={data_file}",
               f"--include={target_file}", "-m", "pytest", *PYTEST_BASE, os.path.basename(test_file)]
    json_cmd = [sys.executable, "-m", "coverage", "json", f"--data-file={data_file}", "-o", json_path, "-q"]
    try:
        subprocess.run(run_cmd, cwd=cwd, env=_ENV, capture_output=True, text=True, timeout=timeout)
        r = subprocess.run(json_cmd, cwd=cwd, env=_ENV, capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            res.error = r.stderr.strip() or r.stdout.strip() or "coverage json falló"
            return res
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except subprocess.TimeoutExpired:
        res.error = "timeout"
        return res
    except (OSError, json.JSONDecodeError) as e:
        res.error = str(e)
        return res
    finally:
        res.duration = time.monotonic() - t0

    target_real = os.path.realpath(target_file)
    info = None
    for path, finfo in data.get("files", {}).items():
        if os.path.realpath(os.path.join(cwd, path)) == target_real or os.path.realpath(path) == target_real:
            info = finfo
            break
    if info is None:
        res.error = "el archivo objetivo no aparece en el reporte (¿los tests no lo importan?)"
        return res
    s = info["summary"]
    res.num_statements = s.get("num_statements", 0)
    res.covered_lines = s.get("covered_lines", 0)
    res.num_branches = s.get("num_branches", 0)
    res.covered_branches = s.get("covered_branches", 0)
    res.line_coverage = res.covered_lines / res.num_statements if res.num_statements else 0.0
    res.branch_coverage = res.covered_branches / res.num_branches if res.num_branches else 1.0
    res.missing_lines = info.get("missing_lines", [])
    res.missing_branches = info.get("missing_branches", [])
    return res


# Resultado de cosmic-ray: score y conteos de mutantes, con marcas de muestra y restauración.
@dataclass
class MutationResult:
    mutation_score: float = 0.0
    total_mutants: int = 0
    completed: int = 0
    killed: int = 0
    survived: int = 0
    incompetent: int = 0
    timed_out: bool = False
    file_restored: bool = False
    error: str = ""
    duration: float = 0.0

    # Resumen de una línea para prompts y logs.
    @property
    def summary(self) -> str:
        if self.error:
            return f"mutation: ERROR {self.error[:120]}"
        tag = "muestra" if self.timed_out else "completo"
        return (f"mutation: score {self.mutation_score:.1%} ({tag}: {self.completed}/{self.total_mutants} mutantes, "
                f"{self.killed} killed, {self.survived} survived, {self.incompetent} incompetent)")


# cosmic-ray init + exec acotado por tiempo (corte con SIGINT), con snapshot y restauración del objetivo.
def run_mutation(test_file: str, cwd: str, target_file: str, work_dir: str,
                 time_budget: float, per_test_timeout: float = 5.0) -> MutationResult:
    t0 = time.monotonic()
    res = MutationResult()
    work_dir, target_file, cwd = map(os.path.abspath, (work_dir, target_file, cwd))
    os.makedirs(work_dir, exist_ok=True)
    toml_path = os.path.join(work_dir, "cosmic-ray.toml")
    db_path = os.path.join(work_dir, "session.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)

    with open(target_file, "rb") as fh:
        snapshot = fh.read()
    h0 = hashlib.md5(snapshot).hexdigest()

    with open(toml_path, "w", encoding="utf-8") as fh:
        fh.write(MUTATION_TOML.format(target=target_file, per_test_timeout=per_test_timeout,
                                      python=sys.executable, test_basename=os.path.basename(test_file)))
    try:
        r = subprocess.run([sys.executable, "-m", "cosmic_ray.cli", "init", toml_path, db_path],
                           cwd=cwd, env=_ENV, capture_output=True, text=True,
                           timeout=max(5.0, min(25.0, time_budget)))
        if r.returncode != 0:
            res.error = "init falló: " + (r.stderr.strip().splitlines() or ["?"])[-1]
            return res
        from cosmic_ray.work_db import use_db, WorkDB
        with use_db(db_path, WorkDB.Mode.open) as db:
            res.total_mutants = db.num_work_items
        if res.total_mutants == 0:
            res.error = "cosmic-ray no generó mutantes"
            return res

        remaining = time_budget - (time.monotonic() - t0)
        if remaining < 3.0:
            res.error = f"sin tiempo para exec ({remaining:.1f}s)"
            return res
        proc = subprocess.Popen([sys.executable, "-m", "cosmic_ray.cli", "exec", toml_path, db_path],
                                cwd=cwd, env=_ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            res.timed_out = True
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        with use_db(db_path, WorkDB.Mode.open) as db:
            for _item, result in db.completed_work_items:
                outcome = str(result.test_outcome).split(".")[-1].lower()
                if outcome == "killed":
                    res.killed += 1
                elif outcome == "survived":
                    res.survived += 1
                else:
                    res.incompetent += 1
        res.completed = res.killed + res.survived + res.incompetent
        if res.completed:
            res.mutation_score = 1.0 - res.survived / res.completed
        else:
            res.error = "ningún mutante alcanzó a completarse"
    except subprocess.TimeoutExpired:
        res.error = "init excedió el tiempo"
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
    finally:
        with open(target_file, "rb") as fh:
            if hashlib.md5(fh.read()).hexdigest() != h0:
                with open(target_file, "wb") as fh2:
                    fh2.write(snapshot)
                res.file_restored = True
        res.duration = time.monotonic() - t0
    return res
