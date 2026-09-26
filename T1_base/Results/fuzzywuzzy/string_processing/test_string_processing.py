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
                if _os.path.isfile(_os.path.join(cand, 'string_processing.py')):
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
from fuzzywuzzy.string_processing import StringProcessor


def test_replace_non_letters_non_numbers_with_whitespace():
    input_str = "Hello, World! 123-456_789."
    result = StringProcessor.replace_non_letters_non_numbers_with_whitespace(input_str)
    # The regex r"(?ui)\W" matches any non-word character and replaces sequences with a single space.
    assert result == "Hello  World  123 456_789 "


def test_replace_non_letters_non_numbers_with_whitespace_empty():
    assert StringProcessor.replace_non_letters_non_numbers_with_whitespace("") == ""


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("  hello  ", "hello"),
        ("hello", "hello"),
        ("\t\nhello\r ", "hello"),
    ],
)
def test_strip(input_str, expected):
    assert StringProcessor.strip(input_str) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("Hello World", "hello world"),
        ("HELLO", "hello"),
        ("hello", "hello"),
        ("", ""),
    ],
)
def test_to_lower_case(input_str, expected):
    assert StringProcessor.to_lower_case(input_str) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("Hello World", "HELLO WORLD"),
        ("hello", "HELLO"),
        ("HELLO", "HELLO"),
        ("", ""),
    ],
)
def test_to_upper_case(input_str, expected):
    assert StringProcessor.to_upper_case(input_str) == expected


def test_string_processor_instance_methods():
    processor = StringProcessor()
    assert processor.to_lower_case("TEST") == "test"
    assert processor.to_upper_case("test") == "TEST"
    assert processor.strip("  test  ") == "test"
    assert processor.replace_non_letters_non_numbers_with_whitespace("a#b") == "a b"
