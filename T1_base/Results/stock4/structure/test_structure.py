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
from stock4.structure import Structure, validate_attributes, typed_structure
from stock4.validate import Validator, Typed, Positive, NonEmptyString

# Concrete implementation for testing
class Stock(Structure):
    name = NonEmptyString()
    shares = Typed(int)
    price = Typed(float)

def test_structure_init():
    s = Stock("AAPL", 100, 150.0)
    assert s.name == "AAPL"
    assert s.shares == 100
    assert s.price == 150.0

def test_structure_repr():
    s = Stock("GOOG", 10, 2000.0)
    assert repr(s) == "Stock('GOOG', 10, 2000.0)"

def test_structure_iter():
    s = Stock("MSFT", 50, 300.0)
    assert list(s) == ["MSFT", 50, 300.0]

def test_structure_eq():
    s1 = Stock("IBM", 10, 100.0)
    s2 = Stock("IBM", 10, 100.0)
    s3 = Stock("IBM", 10, 101.0)
    assert s1 == s2
    assert s1 != s3
    assert s1 != "not a stock"

def test_structure_setattr_restriction():
    s = Stock("AAPL", 10, 10.0)
    with pytest.raises(AttributeError, match="No attribute invalid"):
        s.invalid = 5
    s.shares = 20
    assert s.shares == 20



def test_validate_attributes_no_fields():
    class Empty(Structure):
        pass
    e = Empty()
    assert e._fields == ()
    assert e._types == ()

def test_validate_attributes_callable_annotation():
    class Annotated(Structure):
        def method(self, x: int):
            return x
    # Trigger validation
    validate_attributes(Annotated)
    assert hasattr(Annotated, 'method')
    # The decorator 'validated' is applied, checking if it's callable
    assert callable(Annotated.method)

def test_structure_meta_prepare():
    # Verify ChainMap initialization in metaclass
    class MetaTest(Structure):
        pass
    assert isinstance(MetaTest._fields, tuple)

def test_structure_setattr_private():
    s = Stock("A", 1, 1.0)
    s._hidden = "secret"
    assert s._hidden == "secret"

def test_structure_fields_order():
    class Ordered(Structure):
        a = Typed(int)
        b = Typed(int)
    o = Ordered(1, 2)
    assert o._fields == ("a", "b")


def test_structure_create_init_code_generation():
    # Test the internal code generation logic
    class Generated(Structure):
        a = Typed(int)
    
    # Verify __init__ exists and works
    g = Generated(42)
    assert g.a == 42
    
    # Verify it handles multiple fields
    class Multi(Structure):
        a = Typed(int)
        b = Typed(int)
    m = Multi(1, 2)
    assert m.a == 1 and m.b == 2

def test_structure_subclass_validation():
    # Ensure __init_subclass__ triggers validate_attributes
    class Sub(Structure):
        val = Typed(int)
    
    s = Sub(100)
    assert s.val == 100
    assert "_fields" in Sub.__dict__

def test_structure_eq_type_mismatch():
    class Other(Structure):
        name = NonEmptyString()
    
    s = Stock("A", 1, 1.0)
    o = Other("A")
    assert not (s == o)

def test_structure_iter_order():
    class OrderTest(Structure):
        first = Typed(int)
        second = Typed(int)
    
    o = OrderTest(1, 2)
    it = iter(o)
    assert next(it) == 1
    assert next(it) == 2
