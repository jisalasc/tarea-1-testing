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
from fuzzywuzzy.StringMatcher import StringMatcher


def test_init_default_and_setters():
    matcher = StringMatcher()
    assert matcher._str1 == ''
    assert matcher._str2 == ''
    assert matcher.ratio() == 1.0
    assert matcher.distance() == 0

    matcher.set_seqs('abcd', 'abef')
    assert matcher._str1 == 'abcd'
    assert matcher._str2 == 'abef'

    matcher.set_seq1('xyz')
    assert matcher._str1 == 'xyz'
    assert matcher._str2 == 'abef'

    matcher.set_seq2('uvw')
    assert matcher._str1 == 'xyz'
    assert matcher._str2 == 'uvw'


def test_init_with_isjunk_warns():
    with pytest.warns(UserWarning, match="isjunk not NOT implemented, it will be ignored"):
        matcher = StringMatcher(isjunk=lambda x: False, seq1='a', seq2='b')
    assert matcher._str1 == 'a'
    assert matcher._str2 == 'b'


def test_ratios_and_distance():
    matcher = StringMatcher(seq1='apple', seq2='apply')
    
    # ratio
    r = matcher.ratio()
    assert isinstance(r, float)
    assert 0.0 <= r <= 1.0

    # cached ratio
    assert matcher.ratio() == r

    # quick_ratio (uses same cache/code path)
    qr = matcher.quick_ratio()
    assert qr == r

    # real_quick_ratio
    rqr = matcher.real_quick_ratio()
    assert isinstance(rqr, float)
    assert 0.0 <= rqr <= 1.0

    # distance
    d = matcher.distance()
    assert isinstance(d, int)
    assert d == 1
    # cached distance
    assert matcher.distance() == d


def test_real_quick_ratio_edge_cases():
    # Empty strings
    matcher = StringMatcher(seq1='', seq2='')
    # 2.0 * min(0, 0) / (0 + 0) -> division by zero in Levenshtein real_quick_ratio formula?
    # Let's check what the code computes: 2.0 * min(len1, len2) / (len1 + len2)
    # If len1=0 and len2=0, Python raises ZeroDivisionError.
    with pytest.raises(ZeroDivisionError):
        matcher.real_quick_ratio()

    matcher.set_seqs('abc', '')
    assert matcher.real_quick_ratio() == 0.0


def test_get_opcodes_and_editops_variations():
    # Test path: get_opcodes() when _opcodes is None, _editops is None
    matcher = StringMatcher(seq1='kitten', seq2='sitting')
    ops1 = matcher.get_opcodes()
    assert isinstance(ops1, list)
    assert matcher._opcodes == ops1

    # Reset cache, test getting editops first, then opcodes derived from editops
    matcher.set_seqs('kitten', 'sitting')
    eops1 = matcher.get_editops()
    assert isinstance(eops1, list)
    assert matcher._editops == eops1

    # Now call get_opcodes when _editops is already populated
    matcher._opcodes = None
    ops2 = matcher.get_opcodes()
    assert ops2 == ops1

    # Reset cache, populate opcodes, then call get_editops when _opcodes is already populated
    matcher.set_seqs('kitten', 'sitting')
    ops3 = matcher.get_opcodes()
    matcher._editops = None
    eops2 = matcher.get_editops()
    assert eops2 == eops1


def test_get_matching_blocks():
    matcher = StringMatcher(seq1='ABCD', seq2='ABCE')
    blocks = matcher.get_matching_blocks()
    assert isinstance(blocks, list)
    assert len(blocks) > 0

    # Cached matching blocks
    assert matcher.get_matching_blocks() == blocks


def test_reset_cache_directly():
    matcher = StringMatcher(seq1='test', seq2='text')
    _ = matcher.ratio()
    _ = matcher.distance()
    _ = matcher.get_opcodes()
    _ = matcher.get_editops()
    _ = matcher.get_matching_blocks()

    assert matcher._ratio is not None
    assert matcher._distance is not None
    assert matcher._opcodes is not None
    assert matcher._editops is not None
    assert matcher._matching_blocks is not None

    matcher._reset_cache()
    assert matcher._ratio is None
    assert matcher._distance is None
    assert matcher._opcodes is None
    assert matcher._editops is None
    assert matcher._matching_blocks is None
