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
    'suit, rank, expected',
    [
        ('S', 'A', 'AS'),
        ('H', '5', '5H'),
        ('D', 'J', 'JD'),
        ('C', '3', '3C'),
        ('BJ', 'A', 'ABJ'),
        ('RJ', 'K', 'KRJ'),
    ],
)
def test_card_str(suit, rank, expected):
    card = Card(suit, rank)
    assert str(card) == expected


@pytest.mark.parametrize(
    'suit, rank, expected',
    [
        ('S', 'A', 'SA'),
        ('H', '5', 'H5'),
        ('D', 'J', 'DJ'),
        ('BJ', 'A', 'BJA'),
    ],
)
def test_card_get_index(suit, rank, expected):
    card = Card(suit, rank)
    assert card.get_index() == expected


def test_card_equality_same():
    c1 = Card('H', '10') # Note: rank is 'T' typically, but let's test exact equality logic
    c2 = Card('H', '10')
    assert c1 == c2


def test_card_equality_different():
    c1 = Card('H', 'A')
    c2 = Card('S', 'A')
    c3 = Card('H', 'K')
    assert not (c1 == c2)
    assert not (c1 == c3)


def test_card_equality_other_type():
    card = Card('H', 'A')
    # Comparing against a non-Card object should return NotImplemented,
    # which causes Python to evaluate it as False (or raise TypeError depending on context,
    # but with `return NotImplemented`, Python returns False for `==`).
    assert (card == "AH") is False
    assert (card == 123) is False


def test_card_hash():
    c1 = Card('S', 'A')
    c2 = Card('S', 'A')
    c3 = Card('H', 'A')

    # Hash should be equal for equal cards
    assert hash(c1) == hash(c2)
    # Hash should likely differ for different cards
    assert hash(c1) != hash(c3)

    # Verify formula: rank_index + 100 * suit_index
    # 'S' is index 0 in valid_suit, 'A' is index 0 in valid_rank
    # Expected hash for 'SA': 0 + 100 * 0 = 0
    assert hash(c1) == 0

    # 'H' is index 1 in valid_suit, 'A' is index 0 in valid_rank
    # Expected hash for 'AH' (rank A, suit H): 0 + 100 * 1 = 100
    assert hash(c3) == 100
