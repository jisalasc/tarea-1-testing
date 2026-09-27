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
                if _os.path.isfile(_os.path.join(cand, 'dealer.py')):
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

import numpy as np
import pytest

from blackjack.dealer import init_standard_deck, BlackjackDealer
from blackjack.base import Card


class DummyPlayer:
    def __init__(self):
        self.hand = []


def test_init_standard_deck():
    deck = init_standard_deck()
    assert isinstance(deck, list)
    assert len(deck) == 52
    assert all(isinstance(c, Card) for c in deck)
    
    # Check specific combinations
    assert Card('S', 'A') in deck
    assert Card('C', 'K') in deck


@pytest.mark.parametrize("num_decks", [1, 2, 0])
def test_blackjack_dealer_init(num_decks):
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=num_decks)

    assert dealer.np_random is rng
    assert dealer.num_decks == num_decks
    assert isinstance(dealer.hand, list)
    assert dealer.hand == []
    assert dealer.status == 'alive'
    assert dealer.score == 0

    if num_decks == 1:
        assert len(dealer.deck) == 52
    elif num_decks == 2:
        assert len(dealer.deck) == 104
    elif num_decks == 0:
        assert len(dealer.deck) == 52  # infinite decks does not multiply standard deck list


def test_dealer_shuffle():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=1)
    original_deck = list(dealer.deck)

    # Shuffle should modify deck in place and contain the same cards
    dealer.shuffle()
    assert len(dealer.deck) == len(original_deck)
    # Even if shuffle could theoretically result in the same order, with a seeded RNG and 52 cards it's effectively reordered
    assert set(dealer.deck) == set(original_deck)


def test_deal_card_finite_deck():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=1)
    player = DummyPlayer()

    initial_deck_len = len(dealer.deck)
    dealer.deal_card(player)

    assert len(player.hand) == 1
    assert isinstance(player.hand[0], Card)
    # Finite deck should pop the card, reducing deck length by 1
    assert len(dealer.deck) == initial_deck_len - 1
    assert player.hand[0] not in dealer.deck


def test_deal_card_infinite_deck():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=0)  # 0 indicates infinite decks
    player = DummyPlayer()

    initial_deck_len = len(dealer.deck)
    dealer.deal_card(player)

    assert len(player.hand) == 1
    assert isinstance(player.hand[0], Card)
    # Infinite deck should NOT pop the card, deck length remains unchanged
    assert len(dealer.deck) == initial_deck_len
