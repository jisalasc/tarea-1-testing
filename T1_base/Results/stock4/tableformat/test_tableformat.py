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
    create_formatter,
)


class DummyRecord:
    def __init__(self, name, price, shares):
        self.name = name
        self.price = price
        self.shares = shares


def test_table_formatter_is_abstract():
    with pytest.raises(TypeError):
        TableFormatter()


def test_print_table_invalid_formatter():
    class NotAFormatter:
        pass

    records = [DummyRecord('AA', 10.0, 100)]
    fields = ['name', 'price']
    with pytest.raises(RuntimeError) as exc_info:
        print_table(records, fields, NotAFormatter())
    assert str(exc_info.value) == 'Expected a TableFormatter'




def test_print_table_empty_records(capsys):
    formatter = CSVTableFormatter()
    print_table([], ['name', 'price'], formatter)
    captured = capsys.readouterr()
    lines = [line for line in captured.out.split('\n') if line]
    assert lines == ['name,price']




def test_create_formatter_unknown():
    with pytest.raises(RuntimeError) as exc_info:
        create_formatter('unknown_format')
    assert str(exc_info.value) == 'Unknown format unknown_format'


def test_column_format_mixin_direct():
    class CustomFormatter(ColumnFormatMixin, CSVTableFormatter):
        formats = ['%s', '%d']

    formatter = CustomFormatter()
    # Test headings delegates properly
    import io
    import sys

    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        formatter.headings(['a', 'b'])
        formatter.row(['hello', 42])
    finally:
        sys.stdout = sys.__stdout__

    output = captured_output.getvalue().strip().split('\n')
    assert output == ['a,b', 'hello,42']


def test_upper_headers_mixin_direct():
    class CustomFormatter(UpperHeadersMixin, CSVTableFormatter):
        pass

    formatter = CustomFormatter()
    import io
    import sys

    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        formatter.headings(['a', 'b'])
    finally:
        sys.stdout = sys.__stdout__

    output = captured_output.getvalue().strip()
    assert output == 'A,B'

from stock4.tableformat import print_table


def test_print_table_output_all_formats(capsys):
    records = [DummyRecord('GOOG', 123.45, 50)]
    fields = ['name', 'price', 'shares']

    # Test TextTableFormatter via print_table
    print_table(records, fields, TextTableFormatter())
    
    # Test HTMLTableFormatter via print_table
    print_table(records, fields, HTMLTableFormatter())

    # Test CSVTableFormatter row output specifically via print_table
    print_table(records, fields, CSVTableFormatter())


def test_create_formatter_combinations():
    # Test text formatter with column_formats and upper_headers
    formatter_text = create_formatter('text', column_formats=['%10s', '%10.2f', '%10d'], upper_headers=True)
    assert isinstance(formatter_text, TextTableFormatter)

    # Test csv formatter with column_formats only
    formatter_csv = create_formatter('csv', column_formats=['%s', '%.2f', '%d'])
    assert isinstance(formatter_csv, CSVTableFormatter)

    # Test html formatter with upper_headers only
    formatter_html = create_formatter('html', upper_headers=True)
    assert isinstance(formatter_html, HTMLTableFormatter)
