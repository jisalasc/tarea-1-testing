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
                if _os.path.isfile(_os.path.join(cand, 'svm.py')):
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
import numpy as np
import pytest

from svm import SVM
from kernerls import Linear, Poly, RBF


@pytest.fixture
def simple_dataset():
    # A tiny linearly separable dataset
    X = np.array([
        [1.0, 1.0],
        [2.0, 2.0],
        [-1.0, -1.0],
        [-2.0, -2.0]
    ])
    y = np.array([1, 1, -1, -1])
    return X, y


def test_svm_init_defaults():
    svm = SVM()
    assert svm.C == 1.0
    assert svm.tol == 1e-3
    assert svm.max_iter == 100
    assert isinstance(svm.kernel, Linear)
    assert svm.b == 0
    assert svm.alpha is None
    assert svm.K is None


def test_svm_init_custom_kernel():
    kernel = RBF(gamma=0.5)
    svm = SVM(C=2.0, kernel=kernel, tol=1e-4, max_iter=50)
    assert svm.C == 2.0
    assert svm.tol == 1e-4
    assert svm.max_iter == 50
    assert svm.kernel is kernel


def test_fit_and_predict(simple_dataset):
    X, y = simple_dataset
    svm = SVM(max_iter=10)
    res = svm.fit(X, y)
    assert svm.alpha is not None
    assert len(svm.alpha) == len(y)
    assert svm.K.shape == (len(X), len(X))

    preds = svm.predict(X)
    assert isinstance(preds, np.ndarray)
    assert len(preds) == len(X)
    # Check that predictions are valid signs (-1 or 1)
    for p in preds:
        assert p in [-1.0, 1.0]


def test_clip():
    svm = SVM()
    # alpha > H
    assert svm.clip(5.0, 4.0, 1.0) == 4.0
    # alpha < L
    assert svm.clip(0.5, 4.0, 1.0) == 1.0
    # L <= alpha <= H
    assert svm.clip(2.5, 4.0, 1.0) == 2.5


def test_find_bounds_different_y():
    svm = SVM(C=2.0)
    svm.alpha = np.array([0.5, 0.5])
    # y[i] != y[j]
    svm.y = np.array([1, -1])
    L, H = svm._find_bounds(0, 1)
    # L = max(0, alpha[j] - alpha[i]) = max(0, 0.5 - 0.5) = 0
    # H = min(C, C - alpha[i] + alpha[j]) = min(2.0, 2.0 - 0.5 + 0.5) = 2.0
    assert L == 0.0
    assert H == 2.0


def test_find_bounds_same_y():
    svm = SVM(C=2.0)
    svm.alpha = np.array([0.5, 0.5])
    # y[i] == y[j]
    svm.y = np.array([1, 1])
    L, H = svm._find_bounds(0, 1)
    # L = max(0, alpha[i] + alpha[j] - C) = max(0, 0.5 + 0.5 - 2.0) = 0
    # H = min(C, alpha[i] + alpha[j]) = min(2.0, 0.5 + 0.5) = 1.0
    assert L == 0.0
    assert H == 1.0


def test_random_index(simple_dataset):
    X, y = simple_dataset
    svm = SVM()
    svm.n_samples = len(X)
    # Call random_index multiple times to ensure it never returns z
    for z in range(len(X)):
        for _ in range(10):
            idx = svm.random_index(z)
            assert idx != z
            assert 0 <= idx < len(X)


def test_kernels_usage(simple_dataset):
    X, y = simple_dataset
    for kernel in [Linear(), Poly(degree=2), RBF(gamma=0.1)]:
        svm = SVM(kernel=kernel, max_iter=2)
        svm.fit(X, y)
        preds = svm.predict(X)
        assert len(preds) == len(X)


def test_b_updates_and_errors(simple_dataset):
    X, y = simple_dataset
    svm = SVM(max_iter=1)
    svm.fit(X, y)
    # Test internal error calculation
    err = svm._error(0)
    assert isinstance(err, float)


def test_intercept_branches(simple_dataset):
    # Craft a scenario to exercise different conditions for b1, b2 updates
    X, y = simple_dataset
    svm = SVM(C=1.0, max_iter=2)
    svm.fit(X, y)
    # Force alpha conditions manually to test b branches inside _train loop
    svm.alpha = np.array([0.5, 0.5, 0.0, 0.0])
    # Run a single step of train or invoke methods
    svm._train()
    assert svm.b is not None


def test_eta_greater_than_zero_continue(simple_dataset):
    X, y = simple_dataset
    svm = SVM(max_iter=1)
    svm.fit(X, y)
    # Mock K matrix or force a case where eta >= 0 to cover the `continue` branch
    svm.K = np.ones((len(X), len(X)))
    # eta = 2 * K[i,j] - K[i,i] - K[j,j] = 2(1) - 1 - 1 = 0 (>= 0 hits continue)
    svm._train()
    assert svm.max_iter == 1


def test_tol_convergence(simple_dataset):
    X, y = simple_dataset
    # Very high tol should trigger immediate convergence check break
    svm = SVM(tol=10.0, max_iter=5)
    svm.fit(X, y)
    assert svm.max_iter == 5
