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
from unittest.mock import patch, MagicMock
from stock4.tableformat import (
    print_table, TableFormatter, TextTableFormatter, CSVTableFormatter,
    HTMLTableFormatter, ColumnFormatMixin, UpperHeadersMixin, create_formatter
)

class MockRecord:
    def __init__(self, name, price):
        self.name = name
        self.price = price

@pytest.fixture
def records():
    return [MockRecord('AAPL', 150.0), MockRecord('GOOG', 2800.0)]

def test_print_table_validation():
    with pytest.raises(RuntimeError, match='Expected a TableFormatter'):
        print_table([], [], object())

def test_text_formatter_output(capsys, records):
    formatter = TextTableFormatter()
    print_table(records, ['name', 'price'], formatter)
    captured = capsys.readouterr()
    assert "      name      price" in captured.out
    assert "AAPL      150.0" in captured.out

def test_csv_formatter_output(capsys, records):
    formatter = CSVTableFormatter()
    print_table(records, ['name', 'price'], formatter)
    captured = capsys.readouterr()
    assert "name,price" in captured.out
    assert "AAPL,150.0" in captured.out

def test_html_formatter_output(capsys, records):
    formatter = HTMLTableFormatter()
    print_table(records, ['name', 'price'], formatter)
    captured = capsys.readouterr()
    assert "<tr> <th>name</th> <th>price</th> </tr>" in captured.out
    assert "<tr> <td>AAPL</td> <td>150.0</td> </tr>" in captured.out

def test_abstract_formatter_cannot_instantiate():
    with pytest.raises(TypeError):
        TableFormatter()

@pytest.mark.parametrize("fmt_name", ['text', 'csv', 'html'])
def test_create_formatter_basic(fmt_name):
    formatter = create_formatter(fmt_name)
    assert isinstance(formatter, (TextTableFormatter, CSVTableFormatter, HTMLTableFormatter))

def test_create_formatter_invalid():
    with pytest.raises(RuntimeError, match='Unknown format'):
        create_formatter('invalid')

def test_column_format_mixin(capsys):
    class CustomFormatter(ColumnFormatMixin, CSVTableFormatter):
        formats = ['%s', '%.2f']
    
    formatter = CustomFormatter()
    formatter.headings(['A', 'B'])
    formatter.row(['val', 1.234])
    captured = capsys.readouterr()
    assert "val,1.23" in captured.out

def test_upper_headers_mixin(capsys):
    class CustomFormatter(UpperHeadersMixin, CSVTableFormatter):
        pass
    
    formatter = CustomFormatter()
    formatter.headings(['a', 'b'])
    captured = capsys.readouterr()
    assert "A,B" in captured.out

def test_create_formatter_with_mixins(capsys):
    formatter = create_formatter('csv', column_formats=['%s', '%.1f'], upper_headers=True)
    formatter.headings(['name', 'price'])
    formatter.row(['AAPL', 150.123])
    captured = capsys.readouterr()
    assert "NAME,PRICE" in captured.out
    assert "AAPL,150.1" in captured.out

def test_print_table_empty_records(capsys):
    formatter = CSVTableFormatter()
    print_table([], ['a', 'b'], formatter)
    captured = capsys.readouterr()
    assert captured.out == "a,b\n"

def test_column_format_mixin_inheritance():
    # Verify the mixin correctly calls super().row
    class MockBase(TableFormatter):
        def __init__(self):
            self.called = False
        def headings(self, h): pass
        def row(self, data): self.called = True
        
    class Derived(ColumnFormatMixin, MockBase):
        formats = ['%s']
        
    d = Derived()
    d.row(['test'])
    assert d.called is True

def test_upper_headers_mixin_inheritance():
    class MockBase(TableFormatter):
        def __init__(self):
            self.headers = None
        def headings(self, h): self.headers = h
        def row(self, data): pass
        
    class Derived(UpperHeadersMixin, MockBase):
        pass
        
    d = Derived()
    d.headings(['a', 'b'])
    assert d.headers == ['A', 'B']
