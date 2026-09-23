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

import pytest
from fuzzywuzzy.fuzz import (
    ratio, partial_ratio, token_sort_ratio, partial_token_sort_ratio,
    token_set_ratio, partial_token_set_ratio, QRatio, UQRatio, WRatio, UWRatio
)

def test_ratio():
    assert ratio("test", "test") == 100
    assert ratio("test", "tent") == 75
    assert ratio("", "a") == 0
    assert ratio(None, "a") == 0



def test_partial_token_sort_ratio():
    assert partial_token_sort_ratio("fuzzy wuzzy", "wuzzy fuzzy") == 100
    assert partial_token_sort_ratio("fuzzy wuzzy", "wuzzy") == 100
    assert partial_token_sort_ratio("a b c", "c") == 100

def test_token_set_ratio():
    assert token_set_ratio("fuzzy wuzzy", "wuzzy fuzzy") == 100
    assert token_set_ratio("fuzzy wuzzy", "wuzzy fuzzy fuzzy") == 100
    assert token_set_ratio("a b c", "a b") == 100
    assert token_set_ratio(None, "a") == 0

def test_partial_token_set_ratio():
    assert partial_token_set_ratio("fuzzy wuzzy", "wuzzy") == 100
    assert partial_token_set_ratio("a b c", "c") == 100


def test_uqratio():
    assert UQRatio("test", "test") == 100
    assert UQRatio("test", "TEST") == 100


def test_uwratio():
    assert UWRatio("test", "test") == 100
    assert UWRatio("test", "TEST") == 100

@pytest.mark.parametrize("func", [ratio, partial_ratio, token_sort_ratio, token_set_ratio])
def test_none_handling(func):
    assert func(None, "test") == 0
    assert func("test", None) == 0

def test_token_set_full_process_false():
    # Testing the specific branch in _token_set where full_process=False and s1==s2
    assert token_set_ratio("a b", "a b", full_process=False) == 100

def test_partial_ratio_threshold():
    # Trigger the > .995 branch
    assert partial_ratio("abc", "abc") == 100

def test_wratio_logic_branches():
    # len_ratio < 1.5
    assert WRatio("abc", "abd") == 67
    # 1.5 < len_ratio < 8
    assert WRatio("abc", "abcde") > 0
    # len_ratio > 8
    assert WRatio("a", "abcdefghi") > 0


def test_token_set_invalid_string():
    # Trigger validation failure
    assert token_set_ratio("   ", "test") == 0

def test_qratio_full_process_false():
    assert QRatio("test", "test", full_process=False) == 100

def test_partial_ratio_empty_shorter():
    assert partial_ratio("", "test") == 0

def test_token_sort_empty():
    assert token_sort_ratio("", "") == 100


def test_wratio_empty_after_process():
    assert WRatio("   ", "   ") == 0

def test_partial_token_sort_ratio_empty():
    assert partial_token_sort_ratio("", "") == 100
