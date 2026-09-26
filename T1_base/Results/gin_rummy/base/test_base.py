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
            for cand in (_os.path.join(d, 'Public_Projects', 'gin_rummy'), _os.path.join(d, 'gin_rummy')):
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

import gin_rummy.base as target_module


def test_module_imports():
    assert target_module is not None

def test_Card_exists():
    assert hasattr(target_module, 'Card')

from gin_rummy.base import Card

def test_card_equality():
    card1 = Card('S', 'A')
    card2 = Card('S', 'A')
    card3 = Card('H', 'A')
    
    assert card1 == card2
    assert card1 != card3
    assert card1 != "not a card"

def test_card_hash():
    card1 = Card('S', 'A')
    card2 = Card('S', 'A')
    card3 = Card('H', '2')
    
    assert hash(card1) == hash(card2)
    assert hash(card1) != hash(card3)
    assert len({card1, card2, card3}) == 2

def test_card_str():
    card = Card('H', 'K')
    assert str(card) == 'KH'

def test_card_get_index():
    card = Card('D', '5')
    assert card.get_index() == 'D5'
