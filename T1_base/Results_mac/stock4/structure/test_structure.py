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
                if _os.path.isfile(_os.path.join(cand, 'structure.py')):
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
from stock4.structure import (
    StructureMeta,
    Structure,
    validate_attributes,
    typed_structure,
)
from stock4.validate import Validator, Typed

class DummyValidator(Validator):
    def __init__(self, name=None, expected_type=None):
        super().__init__(name)
        self.expected_type = expected_type

    def check(self, value):
        return value

class SimpleStructure(Structure):
    x = DummyValidator(name='x', expected_type=int)
    y = DummyValidator(name='y', expected_type=str)

    def compute(self, val: int) -> int:
        return val * 2

class EmptyStructure(Structure):
    pass

def test_structure_meta_prepare():
    ns = StructureMeta.__prepare__('SomeName', (Structure,))
    assert isinstance(ns, dict) or hasattr(ns, 'maps')


def test_structure_repr():
    s = SimpleStructure()
    assert repr(s) == "SimpleStructure()"

def test_structure_iter():
    s = SimpleStructure()
    assert list(s) == []

def test_structure_equality():
    s1 = SimpleStructure()
    s2 = SimpleStructure()
    s3 = SimpleStructure()
    
    class OtherStructure(Structure):
        x = DummyValidator(name='x')
        y = DummyValidator(name='y')

    s4 = OtherStructure()

    assert s1 == s2
    assert s1 != s4
    assert s1 != "not a structure"

def test_from_row():
    row = ['42', 'world']
    # expected_type for x is int, for y is str (identity/default if None)
    class RowStructure(Structure):
        x = DummyValidator(name='x', expected_type=int)
        y = DummyValidator(name='y', expected_type=str)

    s = RowStructure.from_row(row)
    assert isinstance(s, RowStructure)

def test_empty_structure():
    es = EmptyStructure()
    assert es._fields == ()
    assert es._types == ()
    assert list(es) == []
    assert repr(es) == "EmptyStructure()"

def test_validate_attributes_non_validator_annotations():
    class AnnotatedMethodStructure(Structure):
        def my_method(self, val: int) -> int:
            return val

    assert AnnotatedMethodStructure._fields == ()
    s = AnnotatedMethodStructure()
    # Ensure callable with annotations got wrapped via validated()
    assert callable(s.my_method)


def test_structure_setattr_underscore():
    s = SimpleStructure()
    s._private_attr = 99
    assert s._private_attr == 99
