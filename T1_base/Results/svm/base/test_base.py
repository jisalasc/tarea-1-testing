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

# coding:utf-8
import pytest
import numpy as np
from base import BaseEstimator


class DummyEstimator(BaseEstimator):
    def _predict(self, X=None):
        return np.zeros(X.shape[0] if isinstance(X, np.ndarray) and X.ndim > 1 else 1)


class DummyNoYEstimator(BaseEstimator):
    y_required = False

    def _predict(self, X=None):
        return np.ones(X.shape[0] if isinstance(X, np.ndarray) and X.ndim > 1 else 1)


class DummyNoFitRequiredEstimator(BaseEstimator):
    fit_required = False

    def _predict(self, X=None):
        return np.full(X.shape[0] if isinstance(X, np.ndarray) and X.ndim > 1 else 1, 42)


def test_base_estimator_fit_2d_and_predict():
    estimator = DummyEstimator()
    X = [[1, 2], [3, 4]]
    y = [0, 1]
    estimator.fit(X, y)

    assert isinstance(estimator.X, np.ndarray)
    assert isinstance(estimator.y, np.ndarray)
    assert estimator.n_samples == 2
    assert estimator.n_features == 2

    preds = estimator.predict([[5, 6]])
    assert isinstance(preds, np.ndarray)
    assert len(preds) == 1


def test_base_estimator_fit_1d_input():
    estimator = DummyEstimator()
    X = [1, 2, 3]
    y = [0]
    estimator.fit(X, y)

    assert isinstance(estimator.X, np.ndarray)
    assert estimator.n_samples == 1
    assert estimator.n_features == (3,)


def test_empty_matrix_raises_value_error():
    estimator = DummyEstimator()
    with pytest.raises(ValueError, match="Got an empty matrix."):
        estimator.fit([], [1])


def test_missing_y_raises_value_error():
    estimator = DummyEstimator()
    with pytest.raises(ValueError, match="Missed required argument y"):
        estimator.fit([[1, 2]], None)


def test_empty_y_raises_value_error():
    estimator = DummyEstimator()
    with pytest.raises(ValueError, match="The targets array must be no-empty."):
        estimator.fit([[1, 2]], [])


def test_y_not_required():
    estimator = DummyNoYEstimator()
    estimator.fit([[1, 2]], None)
    assert estimator.y is None
    preds = estimator.predict([[3, 4]])
    assert len(preds) == 1


def test_predict_without_fit_raises_error():
    estimator = DummyEstimator()
    estimator.X = None
    with pytest.raises(ValueError, match="You must call `fit` before `predict`"):
        estimator.predict([[1, 2]])


def test_fit_required_false_predict_without_fit():
    estimator = DummyNoFitRequiredEstimator()
    estimator.X = None
    preds = estimator.predict([[1, 2]])
    assert preds[0] == 42


def test_not_implemented_predict():
    base_est = BaseEstimator()
    base_est.fit([[1, 2]], [0])
    with pytest.raises(NotImplementedError):
        base_est.predict([[1, 2]])


def test_predict_non_ndarray_input():
    estimator = DummyEstimator()
    estimator.fit([[1, 2]], [0])
    preds = estimator.predict([[3, 4], [5, 6]])
    assert len(preds) == 2
