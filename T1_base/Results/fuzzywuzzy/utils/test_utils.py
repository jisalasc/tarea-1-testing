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
            for cand in (_os.path.join(d, 'Public_Projects', 'fuzzywuzzy'), _os.path.join(d, 'fuzzywuzzy')):
                if _os.path.isfile(_os.path.join(cand, 'utils.py')):
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

import pytest
from fuzzywuzzy.utils import (
    validate_string, check_for_equivalence, check_for_none, 
    check_empty_string, asciionly, asciidammit, 
    make_type_consistent, full_process, intr
)

def test_validate_string():
    assert validate_string("abc") is True
    assert validate_string(" ") is True
    assert validate_string("") is False
    assert validate_string(None) is False
    assert validate_string(123) is False

def test_decorators():
    # Mock function for decorators
    def dummy(a, b): return 50

    # check_for_equivalence
    decorated_eq = check_for_equivalence(dummy)
    assert decorated_eq("a", "a") == 100
    assert decorated_eq("a", "b") == 50

    # check_for_none
    decorated_none = check_for_none(dummy)
    assert decorated_none(None, "b") == 0
    assert decorated_none("a", None) == 0
    assert decorated_none("a", "b") == 50

    # check_empty_string
    decorated_empty = check_empty_string(dummy)
    assert decorated_empty("", "b") == 0
    assert decorated_empty("a", "") == 0
    assert decorated_empty("a", "b") == 50

def test_asciionly():
    # bad_chars are 128-255
    input_str = "abc" + chr(150)
    assert asciionly(input_str) == "abc"

def test_asciidammit():
    assert asciidammit("abc") == "abc"
    assert asciidammit("abc" + chr(150)) == "abc"
    # Test non-string input (int)
    assert asciidammit(123) == "123"

def test_make_type_consistent():
    # Both str
    s1, s2 = make_type_consistent("a", "b")
    assert isinstance(s1, str) and isinstance(s2, str)
    
    # Mixed types (int, str) -> forces to unicode (str in Py3)
    s1, s2 = make_type_consistent(1, "b")
    assert s1 == "1" and s2 == "b"
    assert isinstance(s1, str) and isinstance(s2, str)

def test_full_process():
    # Basic processing
    assert full_process("  A!B 123  ") == "a b 123"
    # Force ascii
    assert full_process("A" + chr(150) + "B", force_ascii=True) == "ab"

def test_intr():
    assert intr(1.4) == 1
    assert intr(1.6) == 2
    assert intr(1.5) == 2  # Python 3 round rounds to nearest even, but 1.5 -> 2
    assert intr(2.5) == 2  # 2.5 rounds to 2 (even)

@pytest.mark.parametrize("input_val, expected", [
    ("test", True),
    ("", False),
    ([], False),
    (None, False)
])
def test_validate_string_parametrized(input_val, expected):
    assert validate_string(input_val) == expected

def test_asciidammit_unicode_path():
    # Simulate unicode object in Py3 (which is str)
    # The code checks `type(s) is unicode`. In Py3, unicode is str.
    assert asciidammit("café") == "caf"

def test_full_process_edge_cases():
    assert full_process("") == ""
    assert full_process("!!!") == ""
    assert full_process("123", force_ascii=True) == "123"

def test_decorators_wraps():
    def dummy(a, b): return 50
    assert check_for_equivalence(dummy).__name__ == "dummy"
    assert check_for_none(dummy).__name__ == "dummy"
    assert check_empty_string(dummy).__name__ == "dummy"

def test_make_type_consistent_same_type():
    # Ensure it returns original objects if types match
    s1, s2 = "a", "b"
    res1, res2 = make_type_consistent(s1, s2)
    assert res1 is s1
    assert res2 is s2

def test_intr_types():
    assert isinstance(intr(1.0), int)
    assert isinstance(intr(1), int)

def test_asciionly_empty():
    assert asciionly("") == ""

def test_full_process_whitespace_handling():
    # Ensure internal whitespace is preserved but non-alphanumeric is removed
    assert full_process("a!b  c") == "a b  c"
