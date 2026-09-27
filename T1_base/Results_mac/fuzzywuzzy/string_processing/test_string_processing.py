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


def test_replace_non_letters_non_numbers_with_whitespace_basic():
    input_str = "hello, world! 123"
    result = StringProcessor.replace_non_letters_non_numbers_with_whitespace(input_str)
    # The regex r"(?ui)\W" matches any non-word character (unicode-aware).
    # Commas, spaces, exclamation marks will be replaced by a single space.
    assert result == "hello  world  123"


def test_replace_non_letters_non_numbers_with_whitespace_special_chars():
    input_str = "test#string-with_underscores.and.dots"
    result = StringProcessor.replace_non_letters_non_numbers_with_whitespace(input_str)
    # Underscores are word characters (\w) in Python regex, so they are kept.
    # #, -, . are non-word characters, replaced by spaces.
    assert result == "test string with_underscores and dots"


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("  hello  ", "hello"),
        ("\t\n world \r", "world"),
        ("no_whitespace", "no_whitespace"),
        ("", ""),
    ],
)
def test_strip(input_str, expected):
    assert StringProcessor.strip(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("Hello World", "hello world"),
        ("ALREADY LOWER", "already lower"),
        ("123 ABC!", "123 abc!"),
        ("", ""),
    ],
)
def test_to_lower_case(input_str, expected):
    assert StringProcessor.to_lower_case(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("hello world", "HELLO WORLD"),
        ("already upper", "ALREADY UPPER"),
        ("123 abc!", "123 ABC!"),
        ("", ""),
    ],
)
def test_to_upper_case(input_str, expected):
    assert StringProcessor.to_upper_case(input_str) == expected


def test_string_processor_regex_attribute():
    # Verify that the regex attribute is present and is a compiled pattern
    assert hasattr(StringProcessor, "regex")
    assert StringProcessor.regex.pattern == r"(?ui)\W"
