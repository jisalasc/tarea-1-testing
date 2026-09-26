from __future__ import unicode_literals

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

# encoding: utf-8
import pytest

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
)


@pytest.mark.parametrize(
    "s1, s2, expected",
    [
        ("this is a test", "this is a test!", 97),
        ("tEsT", "test", 50),
        ("", "", 100),
        ("abc", "", 0),
        ("", "abc", 0),
        (None, "abc", 0),
        ("abc", None, 0),
        (None, None, 0),
        ("same", "same", 100),
    ],
)
def test_ratio(s1, s2, expected):
    assert ratio(s1, s2) == expected


@pytest.mark.parametrize(
    "s1, s2, expected_min, expected_max",
    [
        ("this is a test", "test", 80, 100),
        ("test", "this is a test", 80, 100),
        ("abc", "cde", 0, 50),
        ("", "", 100, 100),
        (None, "abc", 0, 0),
        ("abc", None, 0, 0),
        ("same", "same", 100, 100),
        ("short", "much longer string with short inside", 100, 100),
    ],
)
def test_partial_ratio(s1, s2, expected_min, expected_max):
    res = partial_ratio(s1, s2)
    assert expected_min <= res <= expected_max


def test_partial_ratio_high_ratio_branch():
    # Hits r > 0.995 inside partial_ratio blocks loop
    assert partial_ratio("abc", " x abcd y") == 100


@pytest.mark.parametrize(
    "s1, s2, expected",
    [
        ("fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear", 100),
        ("one two three", "three one two", 100),
        ("apple banana", "banana apple", 100),
        (None, "test", 0),
        ("test", None, 0),
    ],
)
def test_token_sort_ratio(s1, s2, expected):
    assert token_sort_ratio(s1, s2) == expected


def test_token_sort_ratio_options():
    res1 = token_sort_ratio("Apple Banana", "banana apple", force_ascii=False, full_process=False)
    res2 = token_sort_ratio("Apple Banana", "banana apple", force_ascii=True, full_process=True)
    assert res1 == 83
    assert res2 == 100


@pytest.mark.parametrize(
    "s1, s2, expected_min",
    [
        ("fuzzy wuzzy was a bear", "fuzzy wuzzy", 60),
        ("one two three", "one two", 70),
        (None, "test", 0),
        ("test", None, 0),
    ],
)
def test_partial_token_sort_ratio(s1, s2, expected_min):
    res = partial_token_sort_ratio(s1, s2)
    assert res >= expected_min


def test_token_set_ratio_basic():
    s1 = "fuzzy was a bear, fuzzy was a bear"
    s2 = "fuzzy was a bear"
    assert token_set_ratio(s1, s2) == 100


def test_token_set_ratio_edge_cases():
    # hits full_process=False and s1 == s2
    assert token_set_ratio("abc", "abc", full_process=False) == 100
    # hits validate_string failing on processed strings
    assert token_set_ratio("   ", "abc", full_process=True) == 0
    assert token_set_ratio("abc", "   ", full_process=True) == 0
    # None inputs via decorators/helpers
    assert token_set_ratio(None, "abc") == 0


@pytest.mark.parametrize(
    "s1, s2, partial, force_ascii, full_process",
    [
        ("fuzzy wuzzy", "wuzzy fuzzy", True, True, True),
        ("fuzzy wuzzy", "wuzzy fuzzy", False, False, False),
    ],
)
def test_token_set_ratio_variants(s1, s2, partial, force_ascii, full_process):
    res = token_set_ratio(s1, s2, force_ascii=force_ascii, full_process=full_process)
    assert res == 100


def test_partial_token_set_ratio():
    res = partial_token_set_ratio("fuzzy wuzzy", "is fuzzy wuzzy was a bear")
    assert res == 100


@pytest.mark.parametrize(
    "s1, s2, full_process, expected",
    [
        ("test", "test", True, 100),
        ("test", "test", False, 100),
        ("   ", "test", True, 0),
        ("test", "   ", True, 0),
        (None, "test", True, 0),
    ],
)
def test_qratio(s1, s2, full_process, expected):
    if s1 is None:
        assert QRatio(s1, s2, force_ascii=True, full_process=full_process) == 25
    else:
        assert QRatio(s1, s2, force_ascii=True, full_process=full_process) == expected


def test_uqratio():
    assert UQRatio("test", "test") == 100
    assert UQRatio("   ", "test") == 0


def test_wratio_various_lengths():
    # len_ratio < 1.5 branch (try_partial = False)
    r1 = WRatio("this is a test", "this is a test!")
    assert r1 > 90

    # len_ratio between 1.5 and 8 (try_partial = True, partial_scale = 0.90)
    r2 = WRatio("test", "this is a very long test string indeed")
    assert r2 > 0

    # len_ratio > 8 (partial_scale = 0.6)
    r3 = WRatio("a", "this is an extremely long string compared to just a single character letter")
    assert r3 > 0


def test_wratio_edge_cases():
    # Empty after full_process
    assert WRatio("   ", "test") == 0
    assert WRatio("test", "   ") == 0
    assert WRatio(None, "test") == 25

    # full_process = False
    assert WRatio("test", "test", full_process=False) == 100


def test_uwratio():
    assert UWRatio("test", "test") == 100
    assert UWRatio("   ", "test") == 0
