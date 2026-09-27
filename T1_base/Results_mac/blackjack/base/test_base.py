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
    card = Card('S', 'A')
    assert card.suit == 'S'
    assert card.rank == 'A'


@pytest.mark.parametrize(
    'suit, rank, expected_str',
    [
        ('S', 'A', 'AS'),
        ('H', '5', '5H'),
        ('D', 'J', 'JD'),
        ('C', '3', '3C'),
        ('BJ', 'A', 'ABJ'),  # Note: Card.__str__ uses rank + suit
        ('RJ', 'K', 'KRJ'),
    ],
)
def test_card_str(suit, rank, expected_str):
    card = Card(suit, rank)
    assert str(card) == expected_str


@pytest.mark.parametrize(
    'suit, rank, expected_index',
    [
        ('S', 'A', 'SA'),
        ('H', '5', 'H5'),
        ('D', 'J', 'DJ'),
        ('BJ', 'A', 'BJA'),
        ('RJ', 'K', 'RJK'),
    ],
)
def test_card_get_index(suit, rank, expected_index):
    card = Card(suit, rank)
    assert card.get_index() == expected_index


def test_card_equality():
    card1 = Card('H', '10')
    card2 = Card('H', '10')
    card3 = Card('S', '10')
    card4 = Card('H', '9')

    # Equality with another Card
    assert card1 == card2
    assert card1 != card3
    assert card1 != card4

    # Equality with a non-Card type should return NotImplemented (resulting in False or handled by Python)
    assert not (card1 == 'H10')
    assert card1 != 'H10'


def test_card_hash():
    card1 = Card('S', 'A')
    card2 = Card('S', 'A')
    card3 = Card('H', 'A')

    # Hash should be equal for identical cards
    assert hash(card1) == hash(card2)
    # Hash should differ for different suits/ranks
    assert hash(card1) != hash(card3)

    # Verify hash formula value based on code: rank_index + 100 * suit_index
    # 'S' is index 0 in valid_suit, 'A' is index 0 in valid_rank
    assert hash(card1) == 0 + 100 * 0

    # 'H' is index 1, '5' is index 4 ('A','2','3','4','5')
    card_h5 = Card('H', '5')
    assert hash(card_h5) == 4 + 100 * 1


def test_card_class_constants():
    assert 'S' in Card.valid_suit
    assert 'H' in Card.valid_suit
    assert 'D' in Card.valid_suit
    assert 'C' in Card.valid_suit
    assert 'BJ' in Card.valid_suit
    assert 'RJ' in Card.valid_suit

    assert 'A' in Card.valid_rank
    assert 'K' in Card.valid_rank
