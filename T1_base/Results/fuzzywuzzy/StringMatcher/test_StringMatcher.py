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
                if _os.path.isfile(_os.path.join(cand, 'StringMatcher.py')):
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
from warnings import catch_warnings
from fuzzywuzzy.StringMatcher import StringMatcher

def test_init_and_setters():
    sm = StringMatcher(seq1="apple", seq2="apply")
    assert sm._str1 == "apple"
    assert sm._str2 == "apply"
    
    sm.set_seq1("banana")
    assert sm._str1 == "banana"
    
    sm.set_seq2("bandana")
    assert sm._str2 == "bandana"
    
    sm.set_seqs("cat", "dog")
    assert sm._str1 == "cat"
    assert sm._str2 == "dog"

def test_isjunk_warning():
    with catch_warnings(record=True) as w:
        StringMatcher(isjunk=lambda x: True)
        assert len(w) == 1
        assert "isjunk not NOT implemented" in str(w[-1].message)

def test_ratio():
    sm = StringMatcher(seq1="test", seq2="tent")
    # Levenshtein.ratio("test", "tent") is 0.75
    assert sm.ratio() == 0.75
    assert sm._ratio == 0.75
    # Verify cache usage
    assert sm.quick_ratio() == 0.75

def test_real_quick_ratio():
    sm = StringMatcher(seq1="abc", seq2="abcdef")
    # 2 * min(3, 6) / (3 + 6) = 6 / 9 = 0.666...
    assert sm.real_quick_ratio() == pytest.approx(0.6666666666666666)

def test_distance():
    sm = StringMatcher(seq1="kitten", seq2="sitting")
    assert sm.distance() == 3
    assert sm._distance == 3

def test_get_opcodes_from_scratch():
    sm = StringMatcher(seq1="a", seq2="b")
    opcodes = sm.get_opcodes()
    assert len(opcodes) > 0
    assert sm._opcodes == opcodes

def test_get_opcodes_from_editops():
    sm = StringMatcher(seq1="a", seq2="b")
    sm.get_editops()
    opcodes = sm.get_opcodes()
    assert opcodes == [('replace', 0, 1, 0, 1)]



def test_get_matching_blocks():
    sm = StringMatcher(seq1="abc", seq2="axc")
    blocks = sm.get_matching_blocks()
    # Should find 'a' and 'c'
    assert (0, 0, 1) in blocks
    assert (2, 2, 1) in blocks
    assert (3, 3, 0) in blocks # Sentinel

def test_reset_cache():
    sm = StringMatcher("a", "b")
    sm.ratio()
    sm.distance()
    sm.get_opcodes()
    sm._reset_cache()
    assert sm._ratio is None
    assert sm._distance is None
    assert sm._opcodes is None

@pytest.mark.parametrize("s1, s2, expected_dist", [
    ("", "", 0),
    ("a", "", 1),
    ("", "a", 1),
    ("abc", "abc", 0),
])
def test_distance_variations(s1, s2, expected_dist):
    sm = StringMatcher(seq1=s1, seq2=s2)
    assert sm.distance() == expected_dist

def test_empty_strings_ratio():
    sm = StringMatcher("", "")
    assert sm.ratio() == 1.0

def test_real_quick_ratio_zero_len():
    sm = StringMatcher("", "a")
    assert sm.real_quick_ratio() == 0.0

def test_opcodes_structure():
    sm = StringMatcher("abc", "ac")
    # 'b' is deleted at index 1
    opcodes = sm.get_opcodes()
    assert any(op[0] == 'delete' for op in opcodes)


def test_caching_consistency():
    sm = StringMatcher("hello", "world")
    r1 = sm.ratio()
    r2 = sm.ratio()
    assert r1 == r2
    assert sm._ratio is not None

def test_set_seqs_resets_cache():
    sm = StringMatcher("a", "b")
    sm.ratio()
    assert sm._ratio is not None
    sm.set_seqs("c", "d")
    assert sm._ratio is None

def test_set_seq1_resets_cache():
    sm = StringMatcher("a", "b")
    sm.ratio()
    sm.set_seq1("c")
    assert sm._ratio is None

def test_set_seq2_resets_cache():
    sm = StringMatcher("a", "b")
    sm.ratio()
    sm.set_seq2("c")
    assert sm._ratio is None

def test_get_opcodes_type():
    sm = StringMatcher("a", "b")
    assert isinstance(sm.get_opcodes(), list)

def test_get_editops_type():
    sm = StringMatcher("a", "b")
    assert isinstance(sm.get_editops(), list)

def test_get_matching_blocks_type():
    sm = StringMatcher("a", "b")
    assert isinstance(sm.get_matching_blocks(), list)

def test_quick_ratio_is_ratio():
    sm = StringMatcher("test", "tent")
    assert sm.quick_ratio() == sm.ratio()
