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
            for cand in (_os.path.join(d, 'Public_Projects', 'stock4'), _os.path.join(d, 'stock4')):
                if _os.path.isfile(_os.path.join(cand, 'tableformat.py')):
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
from stock4.tableformat import (
    print_table,
    TableFormatter,
    TextTableFormatter,
    CSVTableFormatter,
    HTMLTableFormatter,
    ColumnFormatMixin,
    UpperHeadersMixin,
    create_formatter
)

class DummyRecord:
    def __init__(self, name, price, shares):
        self.name = name
        self.price = price
        self.shares = shares

@pytest.fixture
def sample_records():
    return [
        DummyRecord('AA', 10.5, 100),
        DummyRecord('IBM', 150.25, 50)
    ]

def test_print_table_invalid_formatter(sample_records):
    with pytest.raises(RuntimeError) as excinfo:
        print_table(sample_records, ['name', 'price'], formatter="not_a_formatter")
    assert "Expected a TableFormatter" in str(excinfo.value)

def test_text_table_formatter_execution(sample_records, capsys):
    formatter = TextTableFormatter()
    print_table(sample_records, ['name', 'price', 'shares'], formatter)
    captured = capsys.readouterr().out
    assert 'name' in captured
    assert 'AA' in captured
    assert '10.5' in captured
    assert '100' in captured

def test_csv_table_formatter_execution(sample_records, capsys):
    formatter = CSVTableFormatter()
    print_table(sample_records, ['name', 'price', 'shares'], formatter)
    captured = capsys.readouterr().out
    lines = captured.strip().splitlines()
    assert lines[0] == "name,price,shares"
    assert lines[1] == "AA,10.5,100"
    assert lines[2] == "IBM,150.25,50"

def test_html_table_formatter_execution(sample_records, capsys):
    formatter = HTMLTableFormatter()
    print_table(sample_records, ['name', 'price'], formatter)
    captured = capsys.readouterr().out
    assert "<tr> <th>name</th> <th>price</th> </tr>" in captured
    assert "<tr> <td>AA</td> <td>10.5</td> </tr>" in captured

def test_create_formatter_unknown():
    with pytest.raises(RuntimeError) as excinfo:
        create_formatter('unknown_format')
    assert "Unknown format unknown_format" in str(excinfo.value)

@pytest.mark.parametrize("name,expected_cls", [
    ('text', TextTableFormatter),
    ('csv', CSVTableFormatter),
    ('html', HTMLTableFormatter),
])
def test_create_formatter_base_types(name, expected_cls):
    formatter = create_formatter(name)
    assert isinstance(formatter, expected_cls)

def test_create_formatter_with_column_formats(sample_records, capsys):
    formatter = create_formatter('csv', column_formats=['%s', '%0.2f', '%d'])
    print_table(sample_records, ['name', 'price', 'shares'], formatter)
    captured = capsys.readouterr().out
    lines = captured.strip().splitlines()
    assert lines[1] == "AA,10.50,100"
    assert lines[2] == "IBM,150.25,50"

def test_create_formatter_with_upper_headers(sample_records, capsys):
    formatter = create_formatter('csv', upper_headers=True)
    print_table(sample_records, ['name', 'price'], formatter)
    captured = capsys.readouterr().out
    lines = captured.strip().splitlines()
    assert lines[0] == "NAME,PRICE"
    assert lines[1] == "AA,10.5"

def test_create_formatter_with_both_mixins(sample_records, capsys):
    formatter = create_formatter('csv', column_formats=['%s', '%0.1f'], upper_headers=True)
    print_table(sample_records, ['name', 'price'], formatter)
    captured = capsys.readouterr().out
    lines = captured.strip().splitlines()
    assert lines[0] == "NAME,PRICE"
    assert lines[1] == "AA,10.5"
    assert lines[2] == "IBM,150.2"

def test_abstract_table_formatter_methods():
    class IncompleteFormatter(TableFormatter):
        def headings(self, headers):
            pass
        # Missing row()

    with pytest.raises(TypeError):
        IncompleteFormatter()

    class IncompleteFormatter2(TableFormatter):
        def row(self, rowdata):
            pass
        # Missing headings()

    with pytest.raises(TypeError):
        IncompleteFormatter2()
