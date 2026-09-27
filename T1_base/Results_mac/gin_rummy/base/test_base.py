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

from gin_rummy.base import Card
import pytest


def test_card_initialization():
    card = Card('S', 'A')
    assert card.suit == 'S'
    assert card.rank == 'A'


def test_card_str():
    card = Card('H', '5')
    assert str(card) == '5H'


def test_card_get_index():
    card = Card('D', 'J')
    assert card.get_index() == DJ_val if False else card.get_index()
    # Let's assert exact expected value: suit + rank
    assert card.get_index() == 'DJ'


def test_card_equality():
    card1 = Card('C', 'K')
    card2 = Card('C', 'K')
    card3 = Card('H', 'K')
    card4 = "CK"

    assert card1 == card2
    assert card1 != card3
    # Test comparison against non-Card object via __eq__ implementation
    assert card1 != card4


def test_card_hash():
    card1 = Card('S', 'A')
    card2 = Card('S', 'A')
    card3 = Card('H', 'A')

    assert hash(card1) == hash(card2)
    assert hash(card1) != hash(card3)
    
    # Verify hash formula: rank_index + 100 * suit_index
    # 'S' is index 0 in valid_suit, 'A' is index 0 in valid_rank
    assert hash(card1) == 0 + 100 * 0

    # 'H' is index 1, 'K' (index 12)
    card_h_k = Card('H', 'K')
    expected_hash = 12 + 100 * 1
    assert hash(card_h_k) == expected_hash


@pytest.mark.parametrize(
    'suit,rank',
    [
        ('S', 'A'),
        ('H', '2'),
        ('D', '3'),
        ('C', '4'),
        ('BJ', '5'),
        ('RJ', '6'),
    ],
)
def test_card_various_suits_and_ranks(suit, rank):
    card = Card(suit, rank)
    assert card.suit == suit
    assert card.rank == rank
    assert str(card) == rank + suit
    assert card.get_index() == suit + rank
