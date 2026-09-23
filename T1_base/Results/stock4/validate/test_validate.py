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
                if _os.path.isfile(_os.path.join(cand, 'validate.py')):
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
from stock4.validate import (
    Validator, Typed, Positive, NonEmpty, PositiveInteger, PositiveFloat, 
    NonEmptyString, isvalidator, validated, enforce, Integer, Float, String
)

def test_validator_basic():
    v = Validator("test")
    assert v.check(10) == 10
    
    class Dummy:
        val = Validator()
    
    d = Dummy()
    d.val = 5
    assert d.__dict__['val'] == 5

def test_typed_classes():
    assert Integer.check(1) == 1
    with pytest.raises(TypeError, match="expected <class 'int'>"):
        Integer.check("a")
    
    assert Float.check(1.5) == 1.5
    with pytest.raises(TypeError, match="expected <class 'float'>"):
        Float.check(1)
        
    assert String.check("abc") == "abc"
    with pytest.raises(TypeError, match="expected <class 'str'>"):
        String.check(123)

def test_positive_and_nonempty():
    assert Positive.check(0) == 0
    assert Positive.check(1) == 1
    with pytest.raises(ValueError, match="must be >= 0"):
        Positive.check(-1)
        
    assert NonEmpty.check("a") == "a"
    with pytest.raises(ValueError, match="must be non-empty"):
        NonEmpty.check("")

def test_composite_validators():
    assert PositiveInteger.check(5) == 5
    with pytest.raises(ValueError, match="must be >= 0"):
        PositiveInteger.check(-1)
    with pytest.raises(TypeError, match="expected <class 'int'>"):
        PositiveInteger.check(1.1)
        
    assert PositiveFloat.check(1.1) == 1.1
    with pytest.raises(ValueError, match="must be >= 0"):
        PositiveFloat.check(-0.1)
        
    assert NonEmptyString.check("x") == "x"
    with pytest.raises(ValueError, match="must be non-empty"):
        NonEmptyString.check("")

def test_isvalidator():
    assert isvalidator(Validator) is True
    assert isvalidator(PositiveInteger) is True
    assert isvalidator(int) is False
    assert isvalidator("not a class") is False

def test_validated_decorator():
    @validated
    def func(x: Integer, y: Positive):
        return x + y

    assert func(1, 2) == 3
    with pytest.raises(TypeError, match="Bad Arguments"):
        func("a", -1)

def test_validated_return_check():
    @validated
    def func(x: Integer) -> Positive:
        return x
    
    assert func(5) == 5
    with pytest.raises(TypeError, match="Bad return: must be >= 0"):
        func(-1)

def test_enforce_decorator():
    @enforce(x=Integer, y=Positive, return_=Positive)
    def func(x, y):
        return x + y

    assert func(1, 2) == 3
    with pytest.raises(TypeError, match="Bad Arguments"):
        func(1.1, -1)
    # The original test failed because it expected a return check error, 
    # but the argument check (y=-2) triggers first.
    with pytest.raises(TypeError, match="Bad Arguments"):
        func(1, -2)

def test_validator_subclass_registry():
    class NewValidator(Validator):
        pass
    assert "NewValidator" in Validator.validators
    assert Validator.validators["NewValidator"] is NewValidator

def test_validated_no_annotations():
    @validated
    def simple(x, y):
        return x + y
    assert simple(1, 2) == 3

def test_enforce_no_annotations():
    @enforce()
    def simple(x, y):
        return x + y
    assert simple(1, 2) == 3

def test_validator_set_name():
    class Container:
        v = Validator()
    
    assert Container.v.name == 'v'

def test_validated_partial_annotations():
    @validated
    def func(x: Integer, y):
        return x + y
    
    assert func(1, 2) == 3
    with pytest.raises(TypeError, match="Bad Arguments"):
        func("a", 1)

def test_enforce_partial_annotations():
    @enforce(x=Integer)
    def func(x, y):
        return x + y
    
    assert func(1, 2) == 3
    with pytest.raises(TypeError, match="Bad Arguments"):
        func("a", 1)
