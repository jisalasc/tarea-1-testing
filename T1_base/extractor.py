# Arma el contexto del archivo objetivo: rutas, nombres públicos, sketch de dependencias e imports.
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

MAX_SKETCH_CHARS = 3500
PROBE_TIMEOUT = 20
_NO_PYC = {"PYTHONDONTWRITEBYTECODE": "1"}


# Todo lo que el agente sabe del archivo objetivo.
@dataclass
class Target:
    file_path: str
    module_name: str
    project_name: str
    project_dir: str
    root_dir: str
    source: str
    public_names: list[str] = field(default_factory=list)
    num_defs: int = 0
    dependency_sketch: str = ""
    import_module: str = ""
    import_style: str = "unknown"
    import_error: str = ""

    # Nombre del archivo de test: test_<módulo>.py.
    @property
    def test_file_name(self) -> str:
        return f"test_{self.module_name}.py"

    # Nombre de la carpeta raíz de proyectos (Public_Proyects).
    @property
    def root_name(self) -> str:
        return os.path.basename(self.root_dir)


# Lee el archivo objetivo y completa el Target con nombres, sketch y estilo de import.
def load_target(path: str) -> Target:
    file_path = os.path.abspath(path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No existe el archivo objetivo: {path}")

    project_dir = os.path.dirname(file_path)
    with open(file_path, encoding="utf-8") as fh:
        source = fh.read()

    t = Target(
        file_path=file_path,
        module_name=os.path.splitext(os.path.basename(file_path))[0],
        project_name=os.path.basename(project_dir),
        project_dir=project_dir,
        root_dir=os.path.dirname(project_dir),
        source=source,
    )

    tree = ast.parse(source)
    t.public_names = _public_names(tree)
    t.num_defs = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     for n in ast.walk(tree))
    t.dependency_sketch = _dependency_sketch(tree, t)
    t.import_style, t.import_module, t.import_error = probe_import(t)
    return t


# Clases y funciones de nivel módulo que no empiezan con guion bajo.
def _public_names(tree: ast.Module) -> list[str]:
    names = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
    return names


# Firmas de clases, métodos, funciones y constantes de un módulo, sin cuerpos.
def _sketch_module(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
        return ""
    lines: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            lines.append(f"class {node.name}({bases}):" if bases else f"class {node.name}:")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lines.append(f"    def {sub.name}({ast.unparse(sub.args)})")
                elif isinstance(sub, ast.Assign):
                    for tgt in sub.targets:
                        if isinstance(tgt, ast.Name):
                            lines.append(f"    {tgt.id} = {ast.unparse(sub.value)[:60]}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.append(f"def {node.name}({ast.unparse(node.args)})")
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                    lines.append(f"{tgt.id} = {ast.unparse(node.value)[:60]}")
    return "\n".join(lines)


# Sketch de los módulos hermanos que el objetivo importa (plano, relativo o vía __init__).
def _dependency_sketch(tree: ast.Module, t: Target) -> str:
    siblings: dict[str, str] = {}
    init_path = os.path.join(t.project_dir, "__init__.py")
    include_init = False

    # Registra un módulo hermano si existe como archivo del proyecto.
    def add_sibling(mod: str):
        p = os.path.join(t.project_dir, mod + ".py")
        if os.path.isfile(p) and mod != t.module_name:
            siblings[mod] = p

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_sibling(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level == 1 and mod:
                add_sibling(mod.split(".")[0])
            elif mod == t.project_name:
                include_init = True
                for real_mod in _resolve_init_aliases(init_path, {a.name for a in node.names}):
                    add_sibling(real_mod)
            elif mod.startswith(t.project_name + "."):
                add_sibling(mod.split(".")[1])
            elif node.level == 0 and mod:
                add_sibling(mod.split(".")[0])

    parts: list[str] = []
    if include_init and os.path.isfile(init_path):
        with open(init_path, encoding="utf-8") as fh:
            parts.append(f"# {t.project_name}/__init__.py\n{fh.read().strip()}")
    for mod, p in sorted(siblings.items()):
        sk = _sketch_module(p)
        if sk:
            parts.append(f"# {t.project_name}/{mod}.py\n{sk}")

    text = "\n\n".join(parts)
    if len(text) > MAX_SKETCH_CHARS:
        text = text[:MAX_SKETCH_CHARS] + "\n# ... (truncated)"
    return text


# Módulos hermanos que definen los nombres re-exportados por el __init__ del paquete.
def _resolve_init_aliases(init_path: str, wanted: set[str]) -> list[str]:
    if not os.path.isfile(init_path):
        return []
    try:
        with open(init_path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
        return []
    found = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            exported = {(a.asname or a.name) for a in node.names}
            if exported & wanted:
                found.append(node.module.split(".")[-1])
    return found


HEADER_TEMPLATE = '''\
# --- cabecera generada por el agente: NO modificar ---------------------------
# Los tests se ejecutan desde Results/<proyecto>/<archivo>/. Esta cabecera busca
# hacia arriba la carpeta del proyecto y la agrega a sys.path junto con su raíz,
# porque los módulos mezclan imports por paquete y planos entre hermanos.
import os as _os
import sys as _sys


def _agent_find_project():
    starts = [_os.path.dirname(_os.path.abspath(__file__)), _os.getcwd()]
    for start in starts:
        d = start
        for _ in range(8):
            for cand in (_os.path.join(d, {root_name!r}, {project!r}), _os.path.join(d, {project!r})):
                if _os.path.isfile(_os.path.join(cand, {module_file!r})):
                    return cand
            parent = _os.path.dirname(d)
            if parent == d:
                break
            d = parent
    return None


_agent_project_dir = _agent_find_project()
if _agent_project_dir:
    for _p in (_os.path.dirname(_agent_project_dir), _agent_project_dir):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
# --- fin cabecera --------------------------------------------------------------
'''


# Cabecera de sys.path que va al inicio del test, rellenada para este objetivo.
def build_header(t: Target) -> str:
    return HEADER_TEMPLATE.format(
        root_name=t.root_name,
        project=t.project_name,
        module_file=t.module_name + ".py",
    )


# Prueba en subproceso el import como paquete y luego plano; devuelve (estilo, módulo, error).
def probe_import(t: Target) -> tuple[str, str, str]:
    candidates = [("package", f"{t.project_name}.{t.module_name}"), ("flat", t.module_name)]
    header = build_header(t)
    last_err = ""
    for style, mod in candidates:
        code = header + f"\nimport importlib\nimportlib.import_module({mod!r})\n"
        with tempfile.TemporaryDirectory() as tmp:
            probe = os.path.join(tmp, "probe_import.py")
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write(code)
            try:
                r = subprocess.run(
                    [sys.executable, probe],
                    capture_output=True, text=True, timeout=PROBE_TIMEOUT,
                    cwd=t.project_dir,
                    env={**os.environ, **_NO_PYC},
                )
            except subprocess.TimeoutExpired:
                last_err = f"{mod}: timeout al importar"
                continue
        if r.returncode == 0:
            return style, mod, ""
        last_err = f"{mod}: " + (r.stderr.strip().splitlines() or ["?"])[-1]
    return "unknown", t.module_name, last_err
