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
import warnings
from fuzzywuzzy.StringMatcher import StringMatcher
from Levenshtein import editops, opcodes


def test_init_default():
    matcher = StringMatcher()
    assert matcher._str1 == ''
    assert matcher._str2 == ''
    assert matcher._ratio is None
    assert matcher._distance is None
    assert matcher._opcodes is None
    assert matcher._editops is None
    assert matcher._matching_blocks is None


def test_init_with_seqs():
    matcher = StringMatcher(seq1='abc', seq2='abd')
    assert matcher._str1 == 'abc'
    assert matcher._str2 == 'abd'


def test_init_with_isjunk_warning():
    with pytest.warns(UserWarning, match="isjunk not NOT implemented, it will be ignored"):
        matcher = StringMatcher(isjunk=lambda x: True, seq1='a', seq2='b')
    assert matcher._str1 == 'a'
    assert matcher._str2 == 'b'


def test_set_seqs():
    matcher = StringMatcher('foo', 'bar')
    matcher.set_seqs('hello', 'world')
    assert matcher._str1 == 'hello'
    assert matcher._str2 == 'world'
    assert matcher._ratio is None


def test_set_seq1():
    matcher = StringMatcher('foo', 'bar')
    matcher.set_seq1('baz')
    assert matcher._str1 == 'baz'
    assert matcher._str2 == ''
    assert matcher._distance is None




def test_ratio():
    matcher = StringMatcher('cat', 'bat')
    r1 = matcher.ratio()
    r2 = matcher.ratio()  # hits cached branch
    assert r1 == r2
    assert 0.0 <= r1 <= 1.0


def test_quick_ratio():
    matcher = StringMatcher('cat', 'bat')
    qr = matcher.quick_ratio()
    assert 0.0 <= qr <= 1.0


def test_real_quick_ratio():
    matcher = StringMatcher('cat', 'concatenate')
    rqr = matcher.real_quick_ratio()
    assert 0.0 <= rqr <= 1.0

    # Test edge case with empty strings (division by zero handling in source)
    matcher_empty = StringMatcher('', '')
    with pytest.raises(ZeroDivisionError):
        matcher_empty.real_quick_ratio()




def test_get_opcodes_from_scratch():
    matcher = StringMatcher('abc', 'abd')
    opcodes = matcher.get_opcodes()
    assert isinstance(opcodes, list)
    assert matcher._opcodes is not None


def test_get_opcodes_from_editops():
    matcher = StringMatcher('abc', 'abd')
    # Force _editops first to test the branch in get_opcodes
    matcher._editops = editops(matcher._str1, matcher._str2)
    matcher._opcodes = None
    opcodes = matcher.get_opcodes()
    assert isinstance(opcodes, list)


def test_get_editops_from_scratch():
    matcher = StringMatcher('abc', 'abd')
    editops_res = matcher.get_editops()
    assert isinstance(editops_res, list)
    assert matcher._editops is not None


def test_get_editops_from_opcodes():
    matcher = StringMatcher('abc', 'abd')
    # Force _opcodes first to test the branch in get_editops
    matcher._opcodes = opcodes(matcher._str1, matcher._str2)
    matcher._editops = None
    editops_res = matcher.get_editops()
    assert isinstance(editops_res, list)


def test_get_matching_blocks():
    matcher = StringMatcher('abcdef', 'abxdef')
    blocks = matcher.get_matching_blocks()
    assert isinstance(blocks, list)
    assert matcher._matching_blocks is not None
    # Subsequent call hits cached branch
    blocks_cached = matcher.get_matching_blocks()
    assert blocks == blocks_cached


def test_reset_cache_clears_all():
    matcher = StringMatcher('abc', 'abc')
    matcher.ratio()
    matcher.distance()
    matcher.get_opcodes()
    matcher.get_editops()
    matcher.get_matching_blocks()

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
