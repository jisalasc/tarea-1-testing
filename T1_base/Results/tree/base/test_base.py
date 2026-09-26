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

import base as target_module


def test_module_imports():
    assert target_module is not None

def test_f_entropy_exists():
    assert hasattr(target_module, 'f_entropy')

def test_information_gain_exists():
    assert hasattr(target_module, 'information_gain')

def test_mse_criterion_exists():
    assert hasattr(target_module, 'mse_criterion')

def test_xgb_criterion_exists():
    assert hasattr(target_module, 'xgb_criterion')

def test_get_split_mask_exists():
    assert hasattr(target_module, 'get_split_mask')

def test_split_exists():
    assert hasattr(target_module, 'split')

def test_split_dataset_exists():
    assert hasattr(target_module, 'split_dataset')
