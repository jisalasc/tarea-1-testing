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
    Integer,
    Float,
    String,
    PositiveInteger,
    PositiveFloat,
    NonEmptyString,
    isvalidator,
    validated,
    enforce,
)


def test_validator_basic():
    v = Validator("foo")
    assert v.name == "foo"

    v2 = Validator()
    assert v2.name is None

    # Test __set_name__
    v2.__set_name__(None, "bar")
    assert v2.name == "bar"

    # Test check classmethod
    assert Validator.check(42) == 42


def test_validator_descriptor_protocol():
    class Dummy:
        val = Validator()

    d = Dummy()
    d.val = 123
    assert d.__dict__["val"] == 123


def test_validator_subclass_collection():
    assert "Validator" not in Validator.validators
    assert "Typed" in Validator.validators
    assert "Positive" in Validator.validators
    assert "NonEmptyString" in Validator.validators


def test_typed_validation():
    assert Integer.check(5) == 5

    with pytest.raises(TypeError, match="expected <class 'int'>"):
        Integer.check("not an int")

    assert Float.check(3.14) == 3.14
    with pytest.raises(TypeError, match="expected <class 'float'>"):
        Float.check(1)  # int is not float according to isinstance(1, float)

    assert String.check("hello") == "hello"
    with pytest.raises(TypeError, match="expected <class 'str'>"):
        String.check(123)


def test_positive_validation():
    assert Positive.check(0) == 0
    assert Positive.check(10) == 10

    with pytest.raises(ValueError, match="must be >= 0"):
        Positive.check(-1)


def test_non_empty_validation():
    assert NonEmpty.check([1, 2]) == [1, 2]
    assert NonEmpty.check("abc") == "abc"

    with pytest.raises(ValueError, match="must be non-empty"):
        NonEmpty.check("")

    with pytest.raises(ValueError, match="must be non-empty"):
        NonEmpty.check([])


def test_compound_validators():
    assert PositiveInteger.check(5) == 5
    with pytest.raises(TypeError):
        PositiveInteger.check("5")
    with pytest.raises(ValueError):
        PositiveInteger.check(-5)

    assert PositiveFloat.check(2.5) == 2.5
    with pytest.raises(TypeError):
        PositiveFloat.check(2)
    with pytest.raises(ValueError):
        PositiveFloat.check(-0.1)

    assert NonEmptyString.check("abc") == "abc"
    with pytest.raises(TypeError):
        NonEmptyString.check(123)
    with pytest.raises(ValueError):
        NonEmptyString.check("")


def test_isvalidator():
    assert isvalidator(Validator) is True
    assert isvalidator(Integer) is True
    assert isvalidator(PositiveInteger) is True
    assert isvalidator(int) is False
    assert isvalidator("not a class") is False
    assert isvalidator(object) is False


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
    err_str = str(exc_info.value)
    assert "Bad Arguments" in err_str
    assert "x:" in err_str
    assert "y:" in err_str


def test_validated_decorator_bad_return():
    @validated
    def bad_add(x: PositiveInteger) -> PositiveInteger:
        return -5

    with pytest.raises(TypeError) as exc_info:
        bad_add(5)
    assert "Bad return:" in str(exc_info.value)


def test_validated_decorator_no_annotations():
    @validated
    def plain(x, y):
        return x + y

    assert plain(2, 3) == 5


def test_enforce_decorator_success():
    @enforce(x=PositiveInteger, y=PositiveInteger, return_=PositiveInteger)
    def multiply(x, y):
        return x * y

    assert multiply(3, 4) == 12


def test_enforce_decorator_bad_arguments():
    @enforce(x=PositiveInteger, y=PositiveInteger)
    def multiply(x, y):
        return x * y

    with pytest.raises(TypeError) as exc_info:
        multiply(-2, -3)
    err_str = str(exc_info.value)
    assert "Bad Arguments" in err_str
    assert "x:" in err_str
    assert "y:" in err_str


def test_enforce_decorator_bad_return():
    @enforce(x=PositiveInteger, return_=PositiveInteger)
    def make_negative(x):
        return -x

    with pytest.raises(TypeError) as exc_info:
        make_negative(5)
    assert "Bad return:" in str(exc_info.value)


def test_enforce_decorator_no_return_check():
    @enforce(x=PositiveInteger)
    def just_check(x):
        return x

    assert just_check(10) == 10
    with pytest.raises(TypeError):
        just_check(-1)
