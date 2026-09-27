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
                if _os.path.isfile(_os.path.join(cand, 'fuzz.py')):
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

from fuzzywuzzy.fuzz import (
    ratio,
    partial_ratio,
    token_sort_ratio,
    partial_token_sort_ratio,
    token_set_ratio,
    partial_token_set_ratio,
    QRatio,
    UQRatio,
    WRatio,
    UWRatio,
    _process_and_sort,
    _token_sort,
    _token_set,
)
import pytest


def test_ratio_basic():
    assert ratio("myscript.py", "myscript.py") == 100
    assert ratio("abc", "cba") == 33
    assert ratio("", "") == 100


def test_ratio_decorators_none():
    assert ratio(None, "abc") == 0
    assert ratio("abc", None) == 0
    assert ratio(None, None) == 0


def test_ratio_decorators_equivalence():
    assert ratio("abc", "abc") == 100


def test_ratio_decorators_empty_string():
    assert ratio("", "abc") == 0
    assert ratio("abc", "") == 0


def test_partial_ratio_basic():
    assert partial_ratio("this", "this is a test") == 100
    assert partial_ratio("test", "this is a test") == 100
    assert partial_ratio("abc", "xyz") == 0


def test_partial_ratio_shorter_longer_branches():
    # len(s1) > len(s2) branch
    assert partial_ratio("this is a test", "test") == 100
    # len(s1) <= len(s2) branch
    assert partial_ratio("test", "this is a test") == 100


def test_partial_ratio_high_ratio_early_return():
    # triggers r > 0.995 inside blocks loop
    assert partial_ratio("abc", "XabcY") == 100


def test_partial_ratio_decorators():
    assert partial_ratio(None, "abc") == 0
    assert partial_ratio("abc", None) == 0
    assert partial_ratio(None, None) == 0
    assert partial_ratio("", "abc") == 0
    assert partial_ratio("abc", "") == 0
    assert partial_ratio("abc", "abc") == 100


def test_process_and_sort():
    res = _process_and_sort("beta alpha gamma", force_ascii=True, full_process=True)
    assert res == "alpha beta gamma"
    res_no_full = _process_and_sort("beta alpha gamma", force_ascii=True, full_process=False)
    assert res_no_full == "alpha beta gamma"


def test_token_sort_ratio():
    assert token_sort_ratio("fuzzy was a bear", "bear fuzzy was") == 93
    assert token_sort_ratio(None, "abc") == 0
    assert token_sort_ratio("abc", None) == 0


def test_partial_token_sort_ratio():
    assert partial_token_sort_ratio("fuzzy was", "bear was fuzzy was") == 100
    assert partial_token_sort_ratio(None, "abc") == 0
    assert partial_token_sort_ratio("abc", None) == 0


def test_token_set_ratio():
    assert token_set_ratio("fuzzy was a bear", "fuzzy fuzzy fuzzy bear") == 100
    assert token_set_ratio("abc", "abc", full_process=False) == 100
    assert token_set_ratio(None, "abc") == 0
    assert token_set_ratio("abc", None) == 0
    assert token_set_ratio("", "abc") == 0
    assert token_set_ratio("abc", "") == 0


def test_token_set_ratio_invalid_processed():
    # If full_process produces invalid/empty string
    assert token_set_ratio("   ", "abc") == 0
    assert token_set_ratio("abc", "   ") == 0


def test_partial_token_set_ratio():
    assert partial_token_set_ratio("fuzzy was", "fuzzy was a bear") == 100
    assert partial_token_set_ratio(None, "abc") == 0
    assert partial_token_set_ratio("abc", None) == 0


def test_qratio():
    assert QRatio("abc", "abc") == 100
    assert QRatio("abc", "abc", full_process=False) == 100
    assert QRatio("", "abc") == 0
    assert QRatio("abc", "") == 0
    assert QRatio(None, "abc") == 0
    assert QRatio("abc", None) == 0
    assert QRatio("   ", "abc") == 0
    assert QRatio("abc", "   ") == 0


def test_uqratio():
    assert UQRatio("abc", "abc") == 100
    assert UQRatio("abc", "abc", full_process=False) == 100
    assert UQRatio("", "abc") == 0


def test_wratio_branches():
    # len_ratio < 1.5 branch (try_partial = False)
    res_close = WRatio("apple banana", "banana apple")
    assert res_close > 90

    # len_ratio >= 1.5 and <= 8 branch (try_partial = True, partial_scale = 0.90)
    res_mid = WRatio("apple", "apple banana orange grape")
    assert res_mid > 0

    # len_ratio > 8 branch (partial_scale = 0.6)
    res_long = WRatio("a", "abcdefghijklmnopqrstuvwxyz")
    assert res_long >= 0

    # full_process = False
    assert WRatio("abc", "abc", full_process=False) == 100

    # invalid processed strings
    assert WRatio("   ", "abc") == 0
    assert WRatio("abc", "   ") == 0
    assert WRatio(None, "abc") == 0
    assert WRatio("abc", None) == 0


def test_uwratio():
    assert UWRatio("abc", "abc") == 100
    assert UWRatio("abc", "abc", full_process=False) == 100
    assert UWRatio(None, "abc", full_process=False) == 0


@pytest.mark.parametrize(
    "func, s1, s2",
    [
        (ratio, None, "test"),
        (ratio, "test", None),
        (partial_ratio, None, "test"),
        (partial_ratio, "test", None),
        (token_sort_ratio, None, "test"),
        (token_sort_ratio, "test", None),
        (partial_token_sort_ratio, None, "test"),
        (partial_token_sort_ratio, "test", None),
        (token_set_ratio, None, "test"),
        (token_set_ratio, "test", None),
        (partial_token_set_ratio, None, "test"),
        (partial_token_set_ratio, "test", None),
        (QRatio, None, "test"),
        (QRatio, "test", None),
        (WRatio, None, "test"),
        (WRatio, "test", None),
    ],
)
def test_none_handling_across_all(func, s1, s2):
    # Should safely return 0 or 100 without raising an exception
    val = func(s1, s2)
    assert isinstance(val, int)
