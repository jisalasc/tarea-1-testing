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
            for cand in (_os.path.join(d, 'Public_Projects', 'svm'), _os.path.join(d, 'svm')):
                if _os.path.isfile(_os.path.join(cand, 'base.py')):
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
import numpy as np
from base import BaseEstimator

class ConcreteEstimator(BaseEstimator):
    def _predict(self, X=None):
        return np.zeros(X.shape[0])

class NoYEstimator(BaseEstimator):
    y_required = False
    def _predict(self, X=None):
        return np.ones(X.shape[0])

def test_setup_input_basic():
    est = ConcreteEstimator()
    X = np.array([[1, 2], [3, 4]])
    y = np.array([0, 1])
    est._setup_input(X, y)
    assert np.array_equal(est.X, X)
    assert np.array_equal(est.y, y)
    assert est.n_samples == 2
    assert est.n_features == 2

def test_setup_input_1d_array():
    est = ConcreteEstimator()
    X = np.array([1, 2, 3])
    y = np.array([1])
    est._setup_input(X, y)
    assert est.n_samples == 1
    assert est.n_features == (3,)

def test_setup_input_empty_matrix():
    est = ConcreteEstimator()
    with pytest.raises(ValueError, match="Got an empty matrix."):
        est._setup_input(np.array([]))

def test_setup_input_missing_y():
    est = ConcreteEstimator()
    with pytest.raises(ValueError, match="Missed required argument y"):
        est._setup_input(np.array([[1]]))

def test_setup_input_empty_y():
    est = ConcreteEstimator()
    with pytest.raises(ValueError, match="The targets array must be no-empty."):
        est._setup_input(np.array([[1]]), np.array([]))

def test_fit_and_predict():
    est = ConcreteEstimator()
    X = np.array([[1, 2]])
    y = np.array([1])
    est.fit(X, y)
    pred = est.predict(X)
    assert np.array_equal(pred, np.array([0.0]))


def test_no_y_required():
    est = NoYEstimator()
    X = np.array([[1]])
    # Should not raise error even if y is None
    est.fit(X, None)
    pred = est.predict(X)
    assert np.array_equal(pred, np.array([1.0]))


def test_input_conversion():
    est = ConcreteEstimator()
    # Test list conversion
    est.fit([[1, 2]], [0])
    assert isinstance(est.X, np.ndarray)
    assert isinstance(est.y, np.ndarray)
    assert est.X.shape == (1, 2)
