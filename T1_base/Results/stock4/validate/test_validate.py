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
    Validator,
    Typed,
    Positive,
    NonEmpty,
    PositiveInteger,
    PositiveFloat,
    NonEmptyString,
    Integer,
    Float,
    String,
    isvalidator,
    validated,
    enforce,
)


def test_validator_basic():
    v = Validator("foo")
    assert v.name == "foo"
    assert v.check(10) == 10

    # Test __set_name__ and descriptor protocol __set__
    class Holder:
        val = Validator()

    h = Holder()
    h.val = 42
    assert h.__dict__["val"] == 42


def test_validator_subclass_registry():
    assert "Validator" not in Validator.validators
    assert "Typed" in Validator.validators
    assert "Positive" in Validator.validators
    assert "NonEmpty" in Validator.validators
    assert "PositiveInteger" in Validator.validators
    assert Validator.validators["PositiveInteger"] is PositiveInteger


def test_typed_validation():
    assert Integer.check(5) == 5
    with pytest.raises(TypeError, match="expected <class 'int'>"):
        Integer.check(5.5)

    assert Float.check(3.14) == 3.14
    with pytest.raises(TypeError, match="expected <class 'float'>"):
        Float.check(10)

    assert String.check("hello") == "hello"
    with pytest.raises(TypeError, match="expected <class 'str'>"):
        String.check(123)


def test_positive_validation():
    assert Positive.check(0) == 0
    assert Positive.check(100) == 100
    with pytest.raises(ValueError, match="must be >= 0"):
        Positive.check(-1)


def test_non_empty_validation():
    assert NonEmpty.check([1, 2]) == [1, 2]
    assert NonEmpty.check("abc") == "abc"
    with pytest.raises(ValueError, match="must be non-empty"):
        NonEmpty.check("")
    with pytest.raises(ValueError, match="must be non-empty"):
        NonEmpty.check([])


def test_composite_validators():
    assert PositiveInteger.check(10) == 10
    with pytest.raises(TypeError):
        PositiveInteger.check(10.5)
    with pytest.raises(ValueError):
        PositiveInteger.check(-5)

    assert PositiveFloat.check(1.5) == 1.5
    with pytest.raises(TypeError):
        PositiveFloat.check("1.5")
    with pytest.raises(ValueError):
        PositiveFloat.check(-0.1)

    assert NonEmptyString.check("hello") == "hello"
    with pytest.raises(TypeError):
        NonEmptyString.check(123)
    with pytest.raises(ValueError):
        NonEmptyString.check("")


def test_isvalidator():
    assert isvalidator(Validator) is True
    assert isvalidator(PositiveInteger) is True
    assert isvalidator(int) is False
    assert isvalidator("not a class") is False
    class NotAValidator:
        pass
    assert isvalidator(NotAValidator) is False


def test_validated_decorator_success():
    @validated
    def add(x: PositiveInteger, y: PositiveInteger) -> PositiveInteger:
        return x + y

    assert add(2, 3) == 5


def test_validated_decorator_bad_arguments():
    @validated
    def add(x: PositiveInteger, y: PositiveInteger):
        return x + y

    with pytest.raises(TypeError) as exc_info:
        add(-1, "abc")
    msg = str(exc_info.value)
    assert "Bad Arguments" in msg
    assert "x:" in msg
    assert "y:" in msg


def test_validated_decorator_bad_return():
    @validated
    def bad_add(x: PositiveInteger) -> PositiveInteger:
        return -5

    with pytest.raises(TypeError) as exc_info:
        bad_add(5)
    assert "Bad return:" in str(exc_info.value)


def test_validated_decorator_no_return_annotation():
    @validated
    def no_return(x: PositiveInteger):
        return x

    assert no_return(10) == 10


def test_enforce_decorator_success():
    @enforce(x=PositiveInteger, y=PositiveInteger, return_=PositiveInteger)
    def multiply(x, y):
        return x * y

    assert multiply(3, 4) == 12


def test_enforce_decorator_bad_arguments():
    @enforce(x=PositiveInteger)
    def identity(x):
        return x

    with pytest.raises(TypeError) as exc_info:
        identity(-10)
    assert "Bad Arguments" in str(exc_info.value)
    assert "x:" in str(exc_info.value)


def test_enforce_decorator_bad_return():
    @enforce(return_=PositiveInteger)
    def negative_result():
        return -1

    with pytest.raises(TypeError) as exc_info:
        negative_result()
    assert "Bad return:" in str(exc_info.value)


def test_enforce_decorator_no_return_enforcement():
    @enforce(x=Integer)
    def just_x(x):
        return x

    assert just_x(42) == 42
