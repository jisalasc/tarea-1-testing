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

import pytest
import numpy as np
from svm import SVM
from kernerls import Linear, Poly, RBF

def test_svm_initialization():
    """Test constructor and default values."""
    model = SVM(C=2.0, tol=0.01, max_iter=50)
    assert model.C == 2.0
    assert model.tol == 0.01
    assert model.max_iter == 50
    assert isinstance(model.kernel, Linear)
    assert model.b == 0
    assert model.alpha is None

def test_svm_fit_setup():
    """Test _setup_input and kernel initialization."""
    X = np.array([[1, 2], [3, 4]])
    y = np.array([1, -1])
    model = SVM(kernel=Poly(degree=2))
    model.fit(X, y)
    assert model.K.shape == (2, 2)
    assert model.alpha.shape == (2,)
    assert isinstance(model.kernel, Poly)

def test_svm_train_logic():
    """Test training loop and convergence."""
    X = np.array([[1, 1], [-1, -1]])
    y = np.array([1, -1])
    model = SVM(max_iter=1)
    model.fit(X, y)
    assert model.alpha is not None
    assert len(model.alpha) == 2

def test_clip_method():
    """Test the clipping logic."""
    model = SVM()
    assert model.clip(10, 5, 0) == 5
    assert model.clip(-1, 5, 0) == 0
    assert model.clip(2, 5, 0) == 2

def test_find_bounds():
    """Test L and H calculation branches."""
    model = SVM(C=1.0)
    model.alpha = np.array([0.5, 0.5])
    model.y = np.array([1, -1])
    
    # Case: y[i] != y[j]
    L, H = model._find_bounds(0, 1)
    assert L == 0
    assert H == 1.0
    
    # Case: y[i] == y[j]
    model.y = np.array([1, 1])
    L, H = model._find_bounds(0, 1)
    assert L == 0
    assert H == 1.0

def test_predict_methods():
    """Test prediction interface."""
    X = np.array([[1, 1], [-1, -1]])
    y = np.array([1, -1])
    model = SVM()
    model.fit(X, y)
    
    # Test _predict_row
    row_val = model._predict_row(X[0])
    assert isinstance(row_val, (float, np.float64))
    
    # Test _predict
    preds = model._predict(X)
    assert preds.shape == (2,)
    assert all(p in [-1.0, 0.0, 1.0] for p in preds)

def test_random_index():
    """Test random index selection."""
    model = SVM()
    model.n_samples = 5
    idx = model.random_index(0)
    assert idx != 0
    assert 0 <= idx < 5

def test_error_calculation():
    """Test error calculation."""
    X = np.array([[1, 1], [-1, -1]])
    y = np.array([1, -1])
    model = SVM()
    model.fit(X, y)
    err = model._error(0)
    assert isinstance(err, float)

def test_kernel_types():
    """Test different kernel objects."""
    X = np.array([[1, 1], [-1, -1]])
    y = np.array([1, -1])
    for kernel in [Linear(), Poly(degree=2), RBF(gamma=0.5)]:
        model = SVM(kernel=kernel)
        model.fit(X, y)
        assert model.kernel == kernel

def test_convergence_tol():
    """Test that max_iter stops the loop."""
    X = np.array([[1, 1], [-1, -1]])
    y = np.array([1, -1])
    model = SVM(max_iter=1)
    model.fit(X, y)
    # Check that it didn't crash and set state
    assert model.alpha is not None

def test_sv_idx_selection():
    """Test that support vectors are identified."""
    X = np.array([[1, 1], [-1, -1], [0, 0]])
    y = np.array([1, -1, 1])
    model = SVM()
    model.fit(X, y)
    # sv_idx should be indices where alpha > 0
    assert all(idx < len(X) for idx in model.sv_idx)
    assert isinstance(model.sv_idx, np.ndarray)

@pytest.mark.parametrize("y_val, expected_L, expected_H", [
    (np.array([1, -1]), 0.0, 1.0),
    (np.array([1, 1]), 0.0, 1.0)
])
def test_find_bounds_parametrized(y_val, expected_L, expected_H):
    model = SVM(C=1.0)
    model.alpha = np.array([0.5, 0.5])
    model.y = y_val
    L, H = model._find_bounds(0, 1)
    assert L == expected_L
    assert H == expected_H
