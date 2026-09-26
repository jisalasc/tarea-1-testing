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
    
    # Check that all suits and ranks are represented
    suit_list = ['S', 'H', 'D', 'C']
    rank_list = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    expected_cards = [Card(s, r) for s in suit_list for r in rank_list]
    for expected in expected_cards:
        assert expected in deck


def test_dealer_init_default():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(np_random=rng)
    
    assert dealer.np_random is rng
    assert dealer.num_decks == 1
    assert len(dealer.deck) == 52
    assert dealer.hand == []
    assert dealer.status == 'alive'
    assert dealer.score == 0


@pytest.mark.parametrize("num_decks", [0, 2])
def test_dealer_init_custom_decks(num_decks):
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(np_random=rng, num_decks=num_decks)
    
    assert dealer.num_decks == num_decks
    if num_decks == 0:
        assert len(dealer.deck) == 52
    else:
        assert len(dealer.deck) == 52 * num_decks


def test_dealer_shuffle():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(np_random=rng, num_decks=1)
    deck_before = list(dealer.deck)
    
    dealer.shuffle()
    deck_after = dealer.deck
    
    assert len(deck_after) == len(deck_before)
    assert set(deck_after) == set(deck_before)


def test_deal_card_finite_deck():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(np_random=rng, num_decks=1)
    player = DummyPlayer()
    
    initial_deck_len = len(dealer.deck)
    dealer.deal_card(player)
    
    assert len(player.hand) == 1
    assert isinstance(player.hand[0], Card)
    assert len(dealer.deck) == initial_deck_len - 1
    assert player.hand[0] not in dealer.deck


def test_deal_card_infinite_deck():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(np_random=rng, num_decks=0)
    player = DummyPlayer()
    
    initial_deck_len = len(dealer.deck)
    dealer.deal_card(player)
    
    assert len(player.hand) == 1
    assert isinstance(player.hand[0], Card)
    # With num_decks == 0, cards are not popped from the deck
    assert len(dealer.deck) == initial_deck_len
