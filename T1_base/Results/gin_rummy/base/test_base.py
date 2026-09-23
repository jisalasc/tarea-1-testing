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

import pytest
from gin_rummy.base import Card

def test_card_initialization():
    """Verify that Card attributes are set correctly."""
    c = Card('S', 'A')
    assert c.suit == 'S'
    assert c.rank == 'A'

def test_card_str():
    """Verify string representation."""
    c = Card('H', '5')
    assert str(c) == '5H'

def test_card_get_index():
    """Verify get_index output format."""
    c = Card('D', 'J')
    assert c.get_index() == 'DJ'


def test_card_hash():
    """Verify hash calculation logic."""
    # suit_index: S=0, H=1, D=2, C=3, BJ=4, RJ=5
    # rank_index: A=0, 2=1, ..., T=9, J=10, Q=11, K=12
    # hash = rank_index + 100 * suit_index
    c1 = Card('S', 'A')  # 0 + 100*0 = 0
    c2 = Card('H', '2')  # 1 + 100*1 = 101
    c3 = Card('RJ', 'K') # 12 + 100*5 = 512
    
    assert hash(c1) == 0
    assert hash(c2) == 101
    assert hash(c3) == 512

@pytest.mark.parametrize("suit, rank", [
    ('S', 'A'), ('H', '2'), ('D', '3'), ('C', '4'), ('BJ', '5'), ('RJ', '6'),
    ('S', '7'), ('S', '8'), ('S', '9'), ('S', 'T'), ('S', 'J'), ('S', 'Q'), ('S', 'K')
])
def test_valid_card_combinations(suit, rank):
    """Ensure all valid combinations can be instantiated."""
    c = Card(suit, rank)
    assert c.suit == suit
    assert c.rank == rank

def test_card_class_attributes():
    """Verify class-level constants."""
    assert len(Card.valid_suit) == 6
    assert len(Card.valid_rank) == 13
    assert 'S' in Card.valid_suit
    assert 'A' in Card.valid_rank


def test_hash_uniqueness():
    """Verify that different cards have different hashes."""
    c1 = Card('S', 'A')
    c2 = Card('S', '2')
    c3 = Card('H', 'A')
    assert hash(c1) != hash(c2)
    assert hash(c1) != hash(c3)

def test_card_str_consistency():
    """Verify str representation matches expected format for all ranks/suits."""
    c = Card('C', 'T')
    assert str(c) == 'TC'
    assert c.get_index() == 'CT'

def test_card_set_membership():
    """Verify cards work in sets (requires __hash__ and __eq__)."""
    c1 = Card('S', 'A')
    c2 = Card('S', 'A')
    card_set = {c1, c2}
    assert len(card_set) == 1
    assert c1 in card_set
