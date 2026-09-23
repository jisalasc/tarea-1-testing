"""prompts.py — Plantillas de prompts del agente.

Los prompts van en inglés porque el modelo genera código Python de mejor calidad
así. Cada prompt es autocontenido (llamadas stateless): incluye siempre el código
objetivo, las dependencias y las reglas, porque el modelo no recuerda nada entre
llamadas.

Por ahora solo existe el prompt de generación inicial (pieza 1). Los prompts de
reparación y de mejora de cobertura llegan con el loop (pieza 2 y 3).
"""
from __future__ import annotations

from extractor import Target


def _tests_hint(t: Target) -> int:
    # Aproximación: ~2 tests por def, acotado. Sirve para que el modelo no se quede
    # corto en archivos grandes ni infle archivos chicos.
    return max(8, min(40, 2 * t.num_defs))


def generation_prompt(t: Target) -> str:
    names = ", ".join(t.public_names) if t.public_names else "<no public names>"
    sketch = t.dependency_sketch.strip() or "(none: the module has no local dependencies)"
    sibling_example = (
        f"from {t.project_name}.utils import something"
        if t.import_style == "package"
        else "from utils import something"
    )
    return f"""You are an expert Python test engineer. Write a complete pytest test module for the target module below.

## Target module: `{t.project_name}/{t.module_name}.py`
```python
{t.source.rstrip()}
```

## Local dependencies (signatures only; importable with the same style as the target)
```python
{sketch}
```

## Environment facts (do not fight them)
- Python 3.14, pytest. Third-party libraries available: numpy, scipy, Levenshtein, rapidfuzz.
- The test file runs from a different directory. A header that we control already puts the right folders on `sys.path`. Do NOT touch `sys.path`, do NOT call `os.chdir`, do NOT create conftest files or fixtures files.
- Import the target EXACTLY like this (it is verified to work):
  `from {t.import_module} import {names}`
  or `import {t.import_module}`. Sibling modules of the project use the same style, e.g. `{sibling_example}`.
- `test_{t.module_name}.py` is the only file; everything must live in it.

## Goals, in priority order
1. Every test MUST pass against the code exactly as written above. Derive expected values by reading the code, not from how the code "should" behave. If the code has a quirk or bug, assert the actual behavior.
2. Maximize line and branch coverage of `{t.module_name}.py`: call every public function and method, hit both sides of every `if`, loops with zero/one/many items, early returns, default and non-default arguments, and every `raise` (use `pytest.raises`).
3. Make assertions strong enough to kill mutants: assert exact values, lengths, order, types and state changes. Never settle for `is not None`, `assert True` or "no exception was raised".

## Rules
- Only use names that appear in the target source or in the dependency signatures above. Never invent methods, attributes or parameters.
- Determinism: when a constructor takes `np_random`, pass `np.random.RandomState(42)`; seed `random` if used. No network, no filesystem outside `tmp_path`, no sleeping.
- Each test is small and independent. Use fixtures for shared setup and `pytest.mark.parametrize` when several inputs exercise different branches.
- Speed: the WHOLE file must run in about a second. Use tiny inputs (a handful of rows or items), the smallest iteration counts that still hit the code path (`max_iter=1` to `5`, a few epochs), and never loop until convergence on real-sized data. A hanging test is worse than a missing one.
- Prefer real objects from the project over mocks; mock only true external side effects (printing, time, randomness you cannot seed).
- Do not test private helpers directly unless it is the only way to cover a branch.
- Target about {_tests_hint(t)} tests. Quality over quantity.

## Output
Return ONLY one ```python code block containing the full test module, starting with the imports. No explanations before or after.
"""


# ---------------------------------------------------------------------------
# Reparación (pieza 2)
# ---------------------------------------------------------------------------

MAX_FAILURES_IN_PROMPT = 5
MAX_TRACEBACK_CHARS = 900


def _format_failures(pr) -> str:
    """Los primeros N fallos con traceback corto, o el error de colección."""
    if pr.collection_error:
        return ("The test module FAILED TO COLLECT (syntax error, import error, or an error at module "
                "level). Nothing ran. Error:\n```\n" + pr.collection_error.strip()[:2500] + "\n```")
    chunks = []
    if pr.timed_out:
        hung = [f["nodeid"] for f in pr.failures if f["kind"] == "TIMEOUT"]
        chunks.append("pytest TIMED OUT: the whole run was killed because a test never finished. "
                      f"Hanging test: {', '.join(hung) or 'unknown (the one after the last PASSED)'}. "
                      "Make it finish in well under a second (tiny inputs, very small iteration counts) "
                      "or delete it. Tests that PASSED before the hang must stay exactly as they are.")
    for f in pr.failures[:MAX_FAILURES_IN_PROMPT]:
        tb = f["traceback"].strip()[:MAX_TRACEBACK_CHARS]
        chunks.append(f"### {f['kind']} {f['nodeid']}\n{f['message']}\n```\n{tb}\n```")
    extra = len(pr.failures) - MAX_FAILURES_IN_PROMPT
    if extra > 0:
        chunks.append(f"(... and {extra} more failing tests not shown; fix the pattern, they are likely similar)")
    return "\n\n".join(chunks) if chunks else pr.stdout[-2500:]


def repair_prompt(t: Target, test_code: str, pr) -> str:
    names = ", ".join(t.public_names) if t.public_names else "<no public names>"
    return f"""You are an expert Python test engineer fixing a pytest module that you wrote for the target module below. Some tests fail. Your job is to make the whole file pass WITHOUT weakening the passing tests.

## Target module: `{t.project_name}/{t.module_name}.py` (this code is fixed, you cannot change it)
```python
{t.source.rstrip()}
```

## Current test module (`test_{t.module_name}.py`, without the sys.path header that we add ourselves)
```python
{test_code.rstrip()}
```

## pytest result: {pr.summary}
{_format_failures(pr)}

## How to fix
- Read each failure and decide: is the EXPECTATION wrong (most common: the test assumed ideal behavior, but the code as written does something else) or is the test CALLING the code wrong (bad arguments, a name that does not exist, missing setup)? Fix the test accordingly. Never assume the target has a method or attribute you cannot see in the source.
- If a test cannot be made meaningful and correct, delete it rather than asserting something trivial.
- DO NOT modify tests that currently pass. Keep their names, bodies and assertions exactly as they are.
- Keep imports exactly as they are: `from {t.import_module} import {names}` style. Do NOT touch `sys.path`, do NOT `os.chdir`, do NOT add conftest files.
- Keep determinism (seeded `np.random.RandomState`, no network, no sleeping).

## Output
Return ONLY one ```python code block with the COMPLETE corrected test module (all tests, passing ones included). No explanations.
"""

# ---------------------------------------------------------------------------
# Mejora de Cobertura (pieza 3)
# ---------------------------------------------------------------------------

def enhance_prompt(t: Target, test_code: str, missing_lines: list[int]) -> str:
    return f"""You are an expert Python test engineer. The following test suite works and passes, but it lacks coverage.
Your goal is to WRITE ADDITIONAL TESTS to cover the missing lines.

## Target module: `{t.project_name}/{t.module_name}.py`
```python
{t.source.rstrip()}
```

## Current test module
```python
{test_code.rstrip()}
```

## Missing Coverage
The current tests DO NOT execute the following lines in the target module: {missing_lines}.

## Instructions
- Write ONLY the NEW test functions needed to hit those missing lines.
- Do NOT rewrite the existing tests.
- Output a single python block containing ONLY the new `def test_...():` functions (and any required imports for them). We will append this to the existing file.
"""