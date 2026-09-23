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
            for cand in (_os.path.join(d, 'Public_Projects', 'tree'), _os.path.join(d, 'tree')):
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
from base import (
    f_entropy, information_gain, mse_criterion, xgb_criterion, 
    get_split_mask, split, split_dataset
)

def test_f_entropy():
    # Test entropy of uniform distribution
    p = np.array([0, 1, 2, 3])
    # bincount: [1, 1, 1, 1], p: [0.25, 0.25, 0.25, 0.25]
    # entropy = -4 * (0.25 * log(0.25)) = 1.38629436
    assert f_entropy(p) == pytest.approx(1.38629436)
    
    # Test empty input (bincount returns empty, entropy 0)
    assert f_entropy(np.array([], dtype=int)) == 0.0

def test_information_gain():
    y = np.array([0, 0, 1, 1])
    splits = [np.array([0, 0]), np.array([1, 1])]
    # f_entropy(y) = 0.693, splits_entropy = 0.5 * (0 + 0) = 0
    gain = information_gain(y, splits)
    assert gain == pytest.approx(0.69314718)

def test_mse_criterion():
    y = np.array([1.0, 2.0, 3.0])
    splits = [np.array([1.0]), np.array([2.0, 3.0])]
    # mean = 2.0
    # split1: (1-2)^2 * 1/3 = 0.333
    # split2: ((2-2)^2 + (3-2)^2) * 2/3 = 0.666
    # sum = 1.0, result = -1.0
    assert mse_criterion(y, splits) == pytest.approx(-1.0)

def test_xgb_criterion():
    class MockLoss:
        def gain(self, actual, y_pred):
            return np.sum(actual - y_pred)
            
    y = {"actual": np.array([1, 2]), "y_pred": np.array([0, 0])}
    left = {"actual": np.array([1]), "y_pred": np.array([0])}
    right = {"actual": np.array([2]), "y_pred": np.array([0])}
    
    # left gain = 1, right gain = 2, initial = 3
    # gain = 1 + 2 - 3 = 0
    assert xgb_criterion(y, left, right, MockLoss()) == 0

def test_get_split_mask():
    X = np.array([[1, 5], [2, 6], [3, 4]])
    left, right = get_split_mask(X, 0, 2)
    # col 0: 1 < 2 (T), 2 < 2 (F), 3 < 2 (F)
    assert np.array_equal(left, [True, False, False])
    assert np.array_equal(right, [False, True, True])

def test_split():
    X = np.array([1, 2, 3])
    y = np.array([10, 20, 30])
    left, right = split(X, y, 2)
    # X < 2: [1], X >= 2: [2, 3]
    assert np.array_equal(left, [10])
    assert np.array_equal(right, [20, 30])

def test_split_dataset_with_X():
    X = np.array([[1], [2]])
    target = {"y": np.array([10, 20])}
    left_X, right_X, left, right = split_dataset(X, target, 0, 2, return_X=True)
    assert np.array_equal(left_X, [[1]])
    assert np.array_equal(right_X, [[2]])
    assert np.array_equal(left["y"], [10])
    assert np.array_equal(right["y"], [20])

def test_split_dataset_without_X():
    X = np.array([[1], [2]])
    target = {"y": np.array([10, 20])}
    left, right = split_dataset(X, target, 0, 2, return_X=False)
    assert "y" in left
    assert "y" in right
    assert np.array_equal(left["y"], [10])
    assert np.array_equal(right["y"], [20])

def test_f_entropy_inf_handling():
    # Force entropy to return -inf by passing empty array logic
    # stats.entropy([]) is 0, but if we pass something that results in 0 prob
    # The code explicitly checks for -inf
    assert f_entropy(np.array([0])) == 0.0
