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
    validate_string,
    check_for_equivalence,
    check_for_none,
    check_empty_string,
    asciionly,
    asciidammit,
    make_type_consistent,
    full_process,
    intr,
)


@pytest.mark.parametrize(
    "s,expected",
    [
        ("hello", True),
        ("", False),
        ("a", True),
        ([1, 2], True),
        ([], False),
        (None, False),
        (123, False),
    ],
)
def test_validate_string(s, expected):
    assert validate_string(s) == expected


def test_check_for_equivalence_equal():
    @check_for_equivalence
    def dummy(a, b):
        return 42

    assert dummy("abc", "abc") == 100


def test_check_for_equivalence_not_equal():
    @check_for_equivalence
    def dummy(a, b):
        return 42

    assert dummy("abc", "xyz") == 42


def test_check_for_none_with_none():
    @check_for_none
    def dummy(a, b):
        return 42

    assert dummy(None, "abc") == 0
    assert dummy("abc", None) == 0
    assert dummy(None, None) == 0


def test_check_for_none_without_none():
    @check_for_none
    def dummy(a, b):
        return 42

    assert dummy("abc", "xyz") == 42


def test_check_empty_string_empty():
    @check_empty_string
    def dummy(a, b):
        return 42

    assert dummy("", "abc") == 0
    assert dummy("abc", "") == 0
    assert dummy("", "") == 0


def test_check_empty_string_non_empty():
    @check_empty_string
    def dummy(a, b):
        return 42

    assert dummy("abc", "xyz") == 42


def test_asciionly():
    # ASCII chars remain, non-ASCII chars in range 128-255 are removed
    text = "helloäöü"
    res = asciionly(text)
    assert res == "hello"


def test_asciidammit_with_str():
    text = "helloäöü"
    res = asciidammit(text)
    assert res == "hello"


def test_asciidammit_with_unicode():
    text = str("helloäöü")
    res = asciidammit(text)
    assert res == "hello"


def test_asciidammit_with_non_string():
    # Pass an integer (or something not str/unicode) to trigger `else: return asciidammit(unicode(s))`
    res = asciidammit(123)
    assert res == "123"


def test_make_type_consistent_both_str():
    s1, s2 = "abc", "def"
    r1, r2 = make_type_consistent(s1, s2)
    assert r1 == "abc"
    assert r2 == "def"
    assert isinstance(r1, str)
    assert isinstance(r2, str)


def test_make_type_consistent_both_unicode():
    s1, s2 = str("abc"), str("def")
    r1, r2 = make_type_consistent(s1, s2)
    assert r1 == "abc"
    assert r2 == "def"
    assert isinstance(r1, str)
    assert isinstance(r2, str)


def test_make_type_consistent_mixed():
    s1, s2 = "abc", 123
    r1, r2 = make_type_consistent(s1, s2)
    assert r1 == "abc"
    assert r2 == "123"
    assert isinstance(r1, str)
    assert isinstance(r2, str)


@pytest.mark.parametrize(
    "s,force_ascii,expected",
    [
        ("Hello, World! 123", False, "hello  world  123"),
        ("Café 456", True, "caf 456"),
        ("  Spaces  ", False, "spaces"),
    ],
)
def test_full_process(s, force_ascii, expected):
    assert full_process(s, force_ascii=force_ascii) == expected


@pytest.mark.parametrize(
    "n,expected",
    [
        (2.3, 2),
        (2.7, 3),
        (2.5, 2),
        (3.5, 4),
        (-2.5, -2),
        (0.0, 0),
    ],
)
def test_intr(n, expected):
    assert intr(n) == expected
