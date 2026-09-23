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

import pytest
import numpy as np
from unittest.mock import MagicMock
from gin_rummy.dealer import GinRummyDealer
from gin_rummy.player import GinRummyPlayer

@pytest.fixture
def rng():
    return np.random.RandomState(42)

@pytest.fixture
def dealer(rng):
    return GinRummyDealer(rng)

@pytest.fixture
def player(rng):
    # Mocking the player to avoid complex dependency initialization
    p = MagicMock(spec=GinRummyPlayer)
    p.hand = []
    return p

def test_dealer_initialization(rng):
    dealer = GinRummyDealer(rng)
    assert dealer.discard_pile == []
    assert len(dealer.shuffled_deck) == 52
    assert len(dealer.stock_pile) == 52
    # Verify stock_pile is a copy, not the same list object
    assert dealer.stock_pile is not dealer.shuffled_deck
    assert dealer.stock_pile == dealer.shuffled_deck

def test_deal_cards_updates_player_hand(dealer, player):
    num_cards = 5
    initial_stock_size = len(dealer.stock_pile)
    
    dealer.deal_cards(player, num_cards)
    
    assert len(player.hand) == num_cards
    assert len(dealer.stock_pile) == initial_stock_size - num_cards
    player.did_populate_hand.assert_called_once()

def test_deal_cards_zero_count(dealer, player):
    dealer.deal_cards(player, 0)
    assert len(player.hand) == 0
    player.did_populate_hand.assert_called_once()

def test_deal_cards_exhaust_stock(dealer, player):
    num_cards = 52
    dealer.deal_cards(player, num_cards)
    assert len(player.hand) == 52
    assert len(dealer.stock_pile) == 0
    with pytest.raises(IndexError):
        dealer.deal_cards(player, 1)

def test_dealer_randomness_consistency(rng):
    # Ensure two dealers with the same seed produce the same shuffle
    dealer1 = GinRummyDealer(np.random.RandomState(42))
    dealer2 = GinRummyDealer(np.random.RandomState(42))
    
    assert dealer1.stock_pile == dealer2.stock_pile

def test_deal_cards_order(dealer, player):
    # Verify that cards are popped from the end of the stock_pile
    original_stock = list(dealer.stock_pile)
    dealer.deal_cards(player, 2)
    
    assert player.hand[0] == original_stock[-1]
    assert player.hand[1] == original_stock[-2]
    assert dealer.stock_pile == original_stock[:-2]

def test_deal_cards_multiple_players(dealer, rng):
    p1 = MagicMock(spec=GinRummyPlayer)
    p1.hand = []
    p2 = MagicMock(spec=GinRummyPlayer)
    p2.hand = []
    
    dealer.deal_cards(p1, 3)
    dealer.deal_cards(p2, 3)
    
    assert len(p1.hand) == 3
    assert len(p2.hand) == 3
    assert len(dealer.stock_pile) == 52 - 6
    # Ensure no overlap
    assert all(card not in p2.hand for card in p1.hand)
