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

from gin_rummy.dealer import GinRummyDealer
from gin_rummy.player import GinRummyPlayer


def test_dealer_initialization():
    np_random = np.random.RandomState(42)
    dealer = GinRummyDealer(np_random)

    assert dealer.np_random is np_random
    assert dealer.discard_pile == []
    assert isinstance(dealer.shuffled_deck, list)
    assert len(dealer.shuffled_deck) > 0
    assert dealer.stock_pile == dealer.shuffled_deck
    # Ensure stock_pile is a copy, not the exact same list object
    assert dealer.stock_pile is not dealer.shuffled_deck


def test_deal_cards_single_and_multiple():
    np_random = np.random.RandomState(123)
    dealer = GinRummyDealer(np_random)
    player = GinRummyPlayer(player_id=0, np_random=np_random)

    initial_stock_len = len(dealer.stock_pile)
    assert player.hand == []

    # Deal 1 card
    dealer.deal_cards(player, 1)
    assert len(player.hand) == 1
    assert len(dealer.stock_pile) == initial_stock_len - 1

    # Deal 3 more cards
    dealer.deal_cards(player, 3)
    assert len(player.hand) == 4
    assert len(dealer.stock_pile) == initial_stock_len - 4


def test_deal_cards_zero():
    np_random = np.random.RandomState(99)
    dealer = GinRummyDealer(np_random)
    player = GinRummyPlayer(player_id=1, np_random=np_random)

    initial_stock_len = len(dealer.stock_pile)
    dealer.deal_cards(player, 0)

    assert player.hand == []
    assert len(dealer.stock_pile) == initial_stock_len


def test_deal_cards_populates_player_hand():
    class DummyPlayer:
        def __init__(self):
            self.hand = []
            self.populated_called = False

        def did_populate_hand(self):
            self.populated_called = True

    np_random = np.random.RandomState(7)
    dealer = GinRummyDealer(np_random)
    dummy_player = DummyPlayer()

    dealer.deal_cards(dummy_player, 2)
    assert len(dummy_player.hand) == 2
    assert dummy_player.populated_called is True


def test_shuffled_deck_randomness():
    # Verify that different np_random seeds result in different initial shuffled decks
    dealer1 = GinRummyDealer(np.random.RandomState(1))
    dealer2 = GinRummyDealer(np.random.RandomState(2))

    # Decks should contain the same cards logically, but order should differ (with high probability)
    assert set(dealer1.shuffled_deck) == set(dealer2.shuffled_deck)
    # Check that at least some positions differ or orders are not identical
    assert dealer1.shuffled_deck != dealer2.shuffled_deck
