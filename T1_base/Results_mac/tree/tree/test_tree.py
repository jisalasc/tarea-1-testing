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
                if _os.path.isfile(_os.path.join(cand, 'tree.py')):
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
import random
import numpy as np
import pytest

from tree import Tree
from base import information_gain, mse_criterion, split, split_dataset, xgb_criterion


class MockLoss:
    def approximate(self, actual, y_pred):
        return np.mean(actual - y_pred)

    def gain(self, actual, y_pred):
        return np.sum((actual - y_pred) ** 2)


def test_tree_initialization():
    tree = Tree(regression=True, criterion=mse_criterion, n_classes=None)
    assert tree.regression is True
    assert tree.impurity is None
    assert tree.threshold is None
    assert tree.column_index is None
    assert tree.outcome is None
    assert tree.criterion == mse_criterion
    assert tree.loss is None
    assert tree.n_classes is None
    assert tree.left_child is None
    assert tree.right_child is None
    assert tree.is_terminal is True


def test_is_terminal_property():
    tree = Tree()
    assert tree.is_terminal is True

    tree.left_child = Tree()
    # left_child is set, but right_child is None -> not(left and right) -> True
    assert tree.is_terminal is True

    tree.right_child = Tree()
    # both are set -> not(True and True) -> False
    assert tree.is_terminal is False


def test_find_splits():
    tree = Tree()
    X = np.array([1.0, 3.0, 2.0, 5.0])
    splits = tree._find_splits(X)
    # Unique sorted: [1.0, 2.0, 3.0, 5.0]
    # Averages: (1+2)/2=1.5, (2+3)/2=2.5, (3+5)/2=4.0
    assert sorted(splits) == [1.5, 2.5, 4.0]


def test_calculate_leaf_value_regression():
    tree = Tree(regression=True)
    targets = {"y": np.array([2.0, 4.0, 6.0])}
    tree._calculate_leaf_value(targets)
    assert tree.outcome == 4.0


def test_calculate_leaf_value_classification():
    tree = Tree(regression=False, n_classes=3)
    targets = {"y": np.array([0, 1, 1, 2])}
    tree._calculate_leaf_value(targets)
    # bincount for [0, 1, 1, 2], minlength=3 -> [1, 2, 1]
    # divided by 4 -> [0.25, 0.5, 0.25]
    np.testing.assert_array_equal(tree.outcome, [0.25, 0.5, 0.25])


def test_calculate_leaf_value_boosting():
    loss = MockLoss()
    tree = Tree(regression=True)
    tree.loss = loss
    targets = {"actual": np.array([10.0, 20.0]), "y_pred": np.array([5.0, 15.0])}
    tree._calculate_leaf_value(targets)
    # MockLoss approximate returns mean(actual - y_pred) -> mean([5.0, 5.0]) = 5.0
    assert tree.outcome == 5.0


def test_train_classification_leaf_fallback():
    # Not enough samples or low gain causes AssertionError, falling back to leaf value calculation
    random.seed(42)
    X = np.array([[1.0], [2.0], [3.0]])
    target = {"y": np.array([0, 0, 0])}
    tree = Tree(regression=False, criterion=information_gain)
    tree.train(X, target, min_samples_split=10, max_depth=5, minimum_gain=0.1)

    assert tree.is_terminal is True
    assert tree.n_classes == 1
    np.testing.assert_array_equal(tree.outcome, [1.0])


def test_train_regression_successful_split():
    random.seed(42)
    X = np.array([[1.0], [2.0], [10.0], [11.0], [12.0], [13.0], [14.0], [15.0], [16.0], [17.0], [18.0]])
    target = {"y": np.array([1.0, 1.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0])}
    tree = Tree(regression=True, criterion=mse_criterion)
    tree.train(X, target, min_samples_split=2, max_depth=2, minimum_gain=0.01)

    assert tree.is_terminal is False
    assert tree.column_index == 0
    assert tree.threshold is not None
    assert tree.left_child is not None
    assert tree.right_child is not None


def test_train_boosting():
    random.seed(42)
    X = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0], [8.0], [9.0], [10.0], [11.0]])
    target = {
        "y": np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]),
        "actual": np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
        "y_pred": np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1])
    }
    loss = MockLoss()
    tree = Tree(regression=True)
    tree.train(X, target, min_samples_split=2, max_depth=2, minimum_gain=0.01, loss=loss)

    assert tree.loss == loss
    assert tree.is_terminal is True


def test_predict_row_terminal():
    tree = Tree(regression=True)
    tree.outcome = 42.0
    row = np.array([1.0, 2.0])
    assert tree.predict_row(row) == 42.0


def test_predict_row_recursive():
    tree = Tree(regression=True)
    tree.column_index = 0
    tree.threshold = 5.0

    left_child = Tree(regression=True)
    left_child.outcome = 1.0
    right_child = Tree(regression=True)
    right_child.outcome = 2.0

    tree.left_child = left_child
    tree.right_child = right_child

    # row[0] < 5.0 goes left
    assert tree.predict_row(np.array([3.0])) == 1.0
    # row[0] >= 5.0 goes right
    assert tree.predict_row(np.array([5.0])) == 2.0
    assert tree.predict_row(np.array([10.0])) == 2.0


def test_predict_multiple_rows():
    tree = Tree(regression=True)
    tree.outcome = 7.0
    X = np.array([[1.0], [2.0], [3.0]])
    predictions = tree.predict(X)
    np.testing.assert_array_equal(predictions, [7.0, 7.0, 7.0])


def test_train_with_array_target():
    random.seed(42)
    X = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0], [8.0], [9.0], [10.0], [11.0]])
    target = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    tree = Tree(regression=False, criterion=information_gain)
    tree.train(X, target, min_samples_split=2, max_depth=1)
    # Since all targets are identical, gain is 0, so it hits the AssertionError and becomes terminal
    assert tree.is_terminal is True
    np.testing.assert_array_equal(tree.outcome, [0.0, 1.0])


def test_train_max_depth_zero():
    random.seed(42)
    X = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0], [8.0], [9.0], [10.0], [11.0]])
    target = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
    tree = Tree(regression=False, criterion=information_gain)
    # max_depth=0 will cause assert max_depth > 0 to fail immediately
    tree.train(X, target, min_samples_split=2, max_depth=0)
    assert tree.is_terminal is True


def test_train_min_samples_split_violation():
    random.seed(42)
    X = np.array([[1.0], [2.0]])
    target = np.array([0, 1])
    tree = Tree(regression=False, criterion=information_gain)
    # X.shape[0] is 2, min_samples_split=10 -> fails assert X.shape[0] > min_samples_split
    tree.train(X, target, min_samples_split=10, max_depth=5)
    assert tree.is_terminal is True
