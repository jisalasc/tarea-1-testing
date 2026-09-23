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
            for cand in (_os.path.join(d, 'Public_Projects', 'blackjack'), _os.path.join(d, 'blackjack')):
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
from blackjack.base import Card

def test_card_initialization():
    """Verify that Card initializes attributes correctly."""
    card = Card('S', 'A')
    assert card.suit == 'S'
    assert card.rank == 'A'

def test_card_str():
    """Verify the string representation of the card."""
    card = Card('H', '5')
    assert str(card) == '5H'

def test_card_get_index():
    """Verify the get_index method returns suit + rank."""
    card = Card('D', 'J')
    assert card.get_index() == 'DJ'


def test_card_hash():
    """Verify hash calculation logic."""
    card1 = Card('S', 'A')
    card2 = Card('H', '2')
    
    # suit_index: S=0, H=1. rank_index: A=0, 2=1.
    # hash = rank_index + 100 * suit_index
    assert hash(card1) == 0 + 100 * 0  # 0
    assert hash(card2) == 1 + 100 * 1  # 101
    
    # Ensure identical cards have identical hashes
    assert hash(Card('S', 'A')) == hash(card1)

@pytest.mark.parametrize("suit, rank", [
    ('S', 'A'), ('H', '2'), ('D', '3'), ('C', '4'), ('BJ', '5'), ('RJ', 'K')
])
def test_valid_card_combinations(suit, rank):
    """Test various valid combinations of suits and ranks."""
    card = Card(suit, rank)
    assert card.suit == suit
    assert card.rank == rank


def test_card_class_attributes():
    """Verify class-level constants are present."""
    assert 'S' in Card.valid_suit
    assert 'A' in Card.valid_rank
    assert len(Card.valid_suit) == 6
    assert len(Card.valid_rank) == 13

def test_card_hash_uniqueness():
    """Ensure different cards produce different hashes."""
    cards = [Card(s, r) for s in Card.valid_suit for r in Card.valid_rank]
    hashes = {hash(c) for c in cards}
    assert len(hashes) == len(cards)

def test_card_repr_consistency():
    """Verify that str and get_index are distinct as per implementation."""
    card = Card('BJ', 'A')
    assert str(card) == 'ABJ'
    assert card.get_index() == 'BJA'
    assert str(card) != card.get_index()

def test_card_equality_with_different_instances():
    """Verify equality works across different object instances."""
    c1 = Card('H', 'K')
    c2 = Card('H', 'K')
    assert c1 == c2
    assert c1 is not c2

def test_card_hash_calculation_boundaries():
    """Test hash calculation with extreme indices."""
    # First card: S, A (0, 0) -> 0
    # Last card: RJ, K (5, 12) -> 12 + 100*5 = 512
    c_first = Card('S', 'A')
    c_last = Card('RJ', 'K')
    assert hash(c_first) == 0
    assert hash(c_last) == 512
