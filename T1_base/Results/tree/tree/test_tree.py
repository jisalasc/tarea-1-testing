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

import pytest
import numpy as np
import random
from tree import Tree
from base import information_gain, mse_criterion

# Mocking the loss object for gradient boosting tests
class MockLoss:
    def approximate(self, actual, y_pred):
        return np.mean(actual - y_pred)
    
    def gain(self, actual, y_pred):
        return np.sum(actual - y_pred)

@pytest.fixture
def sample_data():
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
    y = np.array([0, 0, 1, 1])
    return X, y

def test_tree_initialization():
    t = Tree(regression=True, criterion=mse_criterion, n_classes=2)
    assert t.regression is True
    assert t.criterion == mse_criterion
    assert t.n_classes == 2
    assert t.is_terminal is True

def test_find_splits():
    t = Tree()
    X = np.array([1.0, 2.0, 3.0])
    splits = t._find_splits(X)
    assert sorted(splits) == [1.5, 2.5]

def test_train_classification_terminal(sample_data):
    X, y = sample_data
    # Force terminal by setting min_samples_split high
    t = Tree(regression=False, criterion=information_gain)
    t.train(X, y, min_samples_split=10)
    assert t.is_terminal is True
    assert np.array_equal(t.outcome, np.array([0.5, 0.5]))

def test_train_regression_split(sample_data):
    X, y = sample_data
    # Regression tree
    t = Tree(regression=True, criterion=mse_criterion)
    # Use small min_samples_split to force a split
    t.train(X, y, min_samples_split=1, max_depth=2)
    assert t.is_terminal is False
    assert t.column_index is not None
    assert t.threshold is not None

def test_predict_single_row(sample_data):
    X, y = sample_data
    t = Tree(regression=True, criterion=mse_criterion)
    t.train(X, y, min_samples_split=1, max_depth=2)
    prediction = t.predict_row(X[0])
    assert isinstance(prediction, (float, np.float64))

def test_predict_array(sample_data):
    X, y = sample_data
    t = Tree(regression=True, criterion=mse_criterion)
    t.train(X, y, min_samples_split=1, max_depth=2)
    preds = t.predict(X)
    assert preds.shape == (4,)


def test_find_best_split_random_features():
    random.seed(111)
    X = np.random.rand(10, 5)
    y = np.random.randint(0, 2, 10)
    t = Tree(regression=False, criterion=information_gain)
    col, val, gain = t._find_best_split(X, {"y": y}, n_features=2)
    assert 0 <= col < 5
    assert isinstance(val, float)
    assert gain >= 0

def test_train_max_depth_zero():
    X = np.array([[1.0], [2.0]])
    y = np.array([0, 1])
    t = Tree()
    t.train(X, y, max_depth=0)
    assert t.is_terminal is True
    assert t.outcome is not None

def test_train_minimum_gain_constraint():
    X = np.array([[1.0], [1.0000001]])
    y = np.array([0, 0])
    t = Tree(regression=False, criterion=information_gain)
    # max_depth must be > 0 to attempt a split
    t.train(X, y, min_samples_split=1, max_depth=1, minimum_gain=1.0)
    assert t.is_terminal is True

def test_predict_logic_branch():
    # Force a specific tree structure
    t = Tree()
    t.column_index = 0
    t.threshold = 5.0
    t.left_child = Tree()
    t.left_child.outcome = 1.0
    t.right_child = Tree()
    t.right_child.outcome = 2.0
    
    assert t.predict_row(np.array([4.0])) == 1.0
    assert t.predict_row(np.array([6.0])) == 2.0

def test_calculate_leaf_value_regression():
    t = Tree(regression=True)
    t._calculate_leaf_value({"y": np.array([1.0, 3.0])})
    assert t.outcome == 2.0

def test_calculate_leaf_value_classification():
    t = Tree(regression=False, n_classes=2)
    t._calculate_leaf_value({"y": np.array([0, 1, 1])})
    assert np.array_equal(t.outcome, np.array([1/3, 2/3]))
