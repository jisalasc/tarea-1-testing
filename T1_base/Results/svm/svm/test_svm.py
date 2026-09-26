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
def simple_data():
    X = np.array([
        [1.0, 1.0],
        [2.0, 2.0],
        [-1.0, -1.0],
        [-2.0, -2.0]
    ])
    y = np.array([1, 1, -1, -1])
    return X, y


def test_svm_initialization():
    svm = SVM()
    assert svm.C == 1.0
    assert svm.tol == 1e-3
    assert svm.max_iter == 100
    assert isinstance(svm.kernel, Linear)
    assert svm.b == 0
    assert svm.alpha is None
    assert svm.K is None

    custom_kernel = RBF(gamma=0.5)
    svm_custom = SVM(C=2.0, kernel=custom_kernel, tol=1e-2, max_iter=50)
    assert svm_custom.C == 2.0
    assert svm_custom.tol == 1e-2
    assert svm_custom.max_iter == 50
    assert svm_custom.kernel is custom_kernel


def test_svm_fit_and_predict(simple_data):
    X, y = simple_data
    svm = SVM(C=1.0, max_iter=5)
    result = svm.fit(X, y)
    assert svm.alpha is not None
    assert len(svm.alpha) == len(X)
    assert svm.K.shape == (len(X), len(X))

    preds = svm.predict(X)
    assert isinstance(preds, np.ndarray)
    assert preds.shape == (len(X),)


def test_clip():
    svm = SVM()
    # alpha > H -> returns H
    assert svm.clip(5.0, 3.0, 0.0) == 3.0
    # alpha < L -> returns L
    assert svm.clip(-1.0, 3.0, 0.0) == 0.0
    # L <= alpha <= H -> returns alpha
    assert svm.clip(2.0, 3.0, 0.0) == 2.0


def test_random_index(simple_data):
    X, y = simple_data
    svm = SVM()
    svm.n_samples = len(X)
    np.random.seed(42)
    for z in range(svm.n_samples):
        idx = svm.random_index(z)
        assert idx != z
        assert 0 <= idx < svm.n_samples


def test_find_bounds(simple_data):
    X, y = simple_data
    svm = SVM(C=1.0)
    svm.alpha = np.array([0.5, 0.5, 0.5, 0.5])
    svm.C = 1.0

    # y[i] != y[j]
    svm.y = np.array([1, -1, 1, -1])
    L, H = svm._find_bounds(0, 1)
    # L = max(0, alpha[j] - alpha[i]) = max(0, 0.5 - 0.5) = 0.0
    # H = min(C, C - alpha[i] + alpha[j]) = min(1.0, 1.0 - 0.5 + 0.5) = 1.0
    assert L == 0.0
    assert H == 1.0

    # y[i] == y[j]
    svm.y = np.array([1, 1, -1, -1])
    L, H = svm._find_bounds(0, 1)
    # L = max(0, alpha[i] + alpha[j] - C) = max(0, 0.5 + 0.5 - 1.0) = 0.0
    # H = min(C, alpha[i] + alpha[j]) = min(1.0, 0.5 + 0.5) = 1.0
    assert L == 0.0
    assert H == 1.0


def test_error(simple_data):
    X, y = simple_data
    svm = SVM(max_iter=1)
    svm.fit(X, y)
    err = svm._error(0)
    assert isinstance(err, float)


def test_predict_row(simple_data):
    X, y = simple_data
    svm = SVM(max_iter=1)
    svm.fit(X, y)
    row_pred = svm._predict_row(X[0])
    assert isinstance(row_pred, float)


def test_train_eta_ge_zero(simple_data):
    # Test case where eta >= 0 causes continue in _train loop
    X, y = simple_data
    svm = SVM(max_iter=1, kernel=Linear())
    svm.fit(X, y)
    # Manually trigger training iterations where K[i,j] or K values might result in eta >= 0
    # Let's force K such that 2 * K[i,j] - K[i,i] - K[j,j] >= 0
    svm.K = np.ones((len(X), len(X)))
    # With K all ones, eta = 2(1) - 1 - 1 = 0. This hits eta >= 0.
    svm._train()
    assert svm.alpha is not None


def test_train_b_branching(simple_data):
    X, y = simple_data
    svm = SVM(C=1.0, max_iter=2)
    svm._setup_input(X, y)
    svm.K = np.zeros((svm.n_samples, svm.n_samples))
    for i in range(svm.n_samples):
        svm.K[:, i] = svm.kernel(svm.X, svm.X[i, :])
    svm.alpha = np.zeros(svm.n_samples)
    svm.sv_idx = np.arange(0, svm.n_samples)

    # Force alpha values to exercise branches for b1, b2, and 0.5*(b1+b2)
    svm.alpha[0] = 0.5  # 0 < alpha[i] < C
    svm.alpha[1] = 0.0  # not in (0, C)
    svm._train()
    assert svm.b is not None


def test_kernels_with_svm(simple_data):
    X, y = simple_data
    for kernel in [Linear(), Poly(degree=2), RBF(gamma=0.1)]:
        svm = SVM(C=1.0, kernel=kernel, max_iter=2)
        svm.fit(X, y)
        preds = svm.predict(X)
        assert len(preds) == len(X)
