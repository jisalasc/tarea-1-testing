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
    "val,expected",
    [
        ("hello", True),
        ("a", True),
        ("", False),
        ([], False),
        ([1, 2], True),
        (None, False),
        (123, False),
        (12.34, False),
    ],
)
def test_validate_string(val, expected):
    assert validate_string(val) is expected


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
        return 50

    assert dummy(None, "abc") == 0
    assert dummy("abc", None) == 0
    assert dummy(None, None) == 0


def test_check_for_none_without_none():
    @check_for_none
    def dummy(a, b):
        return 50

    assert dummy("abc", "xyz") == 50


def test_check_empty_string_empty():
    @check_empty_string
    def dummy(a, b):
        return 75

    assert dummy("", "abc") == 0
    assert dummy("abc", "") == 0
    assert dummy("", "") == 0


def test_check_empty_string_non_empty():
    @check_empty_string
    def dummy(a, b):
        return 75

    assert dummy("hello", "world") == 75


def test_asciionly():
    text = "hello äöü ß 123"
    result = asciionly(text)
    assert isinstance(result, str)
    # Characters in range 128-256 are removed by translation_table
    for c in result:
        assert ord(c) < 128


def test_asciidammit_str():
    res = asciidammit("hello")
    assert res == "hello"


def test_asciidammit_unicode():
    # In PY3, unicode is str, but let's pass a unicode-like or str with non-ascii
    res = asciidammit("café")
    assert isinstance(res, str)
    for c in res:
        assert ord(c) < 128


def test_asciidammit_other_types():
    # Pass an integer which will be converted via unicode(s)
    res = asciidammit(12345)
    assert res == "12345"


@pytest.mark.parametrize(
    "s1,s2,expected_types",
    [
        ("abc", "def", (str, str)),
        ("abc", "def", (str, str)),
    ],
)
def test_make_type_consistent_same(s1, s2, expected_types):
    r1, r2 = make_type_consistent(s1, s2)
    assert isinstance(r1, expected_types[0])
    assert isinstance(r2, expected_types[1])


def test_make_type_consistent_mixed():
    # Pass mixed types or non-strings to hit the else branch
    r1, r2 = make_type_consistent("abc", 123)
    assert isinstance(r1, str)
    assert isinstance(r2, str)
    assert r1 == "abc"
    assert r2 == "123"


def test_full_process_default():
    res = full_process("  Hello, World! 123... ")
    assert res == "hello  world  123"


def test_full_process_force_ascii():
    res = full_process("Café 123!", force_ascii=True)
    assert isinstance(res, str)
    for c in res:
        assert ord(c) < 128
    assert "caf" in res


@pytest.mark.parametrize(
    "val,expected",
    [
        (2.3, 2),
        (2.6, 3),
        (2.5, 2),
        (3.5, 4),
        (0, 0),
        (-1.2, -1),
        (-1.6, -2),
        (-2.5, -2),  # Python's round rounds half to even
    ],
)
def test_intr(val, expected):
    assert intr(val) == expected
    assert isinstance(intr(val), int)
