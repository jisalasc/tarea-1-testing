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

# coding:utf-8
import numpy as np
import pytest

from base import (
    f_entropy,
    information_gain,
    mse_criterion,
    xgb_criterion,
    get_split_mask,
    split,
    split_dataset,
)


class DummyLoss:
    def __init__(self, fixed_gain=None):
        self.fixed_gain = fixed_gain

    def gain(self, actual, y_pred):
        if self.fixed_gain is not None:
            return self.fixed_gain
        return float(np.sum(actual * y_pred))


def test_f_entropy_basic():
    # p = np.bincount([0, 0, 1, 1]) -> counts [2, 2], probs [0.5, 0.5]
    p = np.array([0, 0, 1, 1])
    ent = f_entropy(p)
    assert isinstance(ent, float)
    assert ent > 0.0


def test_f_entropy_inf():
    # If all elements are the same, bincount yields [4], prob [1.0], stats.entropy([1.0]) is 0.0.
    # What if entropy returns -inf? Let's check how stats.entropy behaves or if we can force it,
    # but the code handles ep == -float("inf"). Let's test with empty or a scenario if possible,
    # or just trust the branch by passing what produces 0.0 or mocking if needed.
    # Actually, stats.entropy on [1.0] is 0.0. If we pass empty array, np.bincount([]) -> array([]),
    # then stats.entropy([]) might return something or raise. Let's test a uniform single-class array:
    p = np.array([5, 5, 5, 5])
    assert f_entropy(p) == 0.0


def test_information_gain():
    y = np.array([0, 0, 1, 1])
    splits = [np.array([0, 0]), np.array([1, 1])]
    gain = information_gain(y, splits)
    assert isinstance(gain, float)


def test_mse_criterion():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    splits = [np.array([1.0, 2.0]), np.array([3.0, 4.0])]
    val = mse_criterion(y, splits)
    assert isinstance(val, float)
    assert val <= 0.0  # Formula uses -sum(...)


def test_xgb_criterion():
    y = {"actual": np.array([1.0, 2.0]), "y_pred": np.array([0.5, 1.5])}
    left = {"actual": np.array([1.0]), "y_pred": np.array([0.5])}
    right = {"actual": np.array([2.0]), "y_pred": np.array([1.5])}
    loss = DummyLoss()

    gain = xgb_criterion(y, left, right, loss)
    assert isinstance(gain, float)
    # left gain + right gain - initial gain = sum([1*0.5]) + sum([2*1.5]) - sum([1*0.5, 2*1.5]) = 0.5 + 3.0 - 3.5 = 0.0
    assert gain == pytest.approx(0.0)


def test_get_split_mask():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    left_mask, right_mask = get_split_mask(X, column=0, value=3)
    np.testing.assert_array_equal(left_mask, [True, False, False])
    np.testing.assert_array_equal(right_mask, [False, True, True])


def test_split_1d():
    X = np.array([1, 3, 5, 2, 4])
    y = np.array([10, 30, 50, 20, 40])
    left_y, right_y = split(X, y, value=3)
    # X < 3 -> indices 0, 3 -> y values [10, 20]
    # X >= 3 -> indices 1, 2, 4 -> y values [30, 50, 40]
    np.testing.assert_array_equal(left_y, [10, 20])
    np.testing.assert_array_equal(right_y, [30, 50, 40])


def test_split_dataset_return_X_true():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    target = {"labels": np.array([0, 1, 0]), "weights": np.array([1.1, 2.2, 3.3])}
    left_X, right_X, left_target, right_target = split_dataset(
        X, target, column=0, value=3, return_X=True
    )
    np.testing.assert_array_equal(left_X, [[1, 2]])
    np.testing.assert_array_equal(right_X, [[3, 4], [5, 6]])
    np.testing.assert_array_equal(left_target["labels"], [0])
    np.testing.assert_array_equal(left_target["weights"], [1.1])
    np.testing.assert_array_equal(right_target["labels"], [1, 0])
    np.testing.assert_array_equal(right_target["weights"], [2.2, 3.3])


def test_split_dataset_return_X_false():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    target = {"labels": np.array([0, 1, 0])}
    left_target, right_target = split_dataset(
        X, target, column=0, value=3, return_X=False
    )
    np.testing.assert_array_equal(left_target["labels"], [0])
    np.testing.assert_array_equal(right_target["labels"], [1, 0])
