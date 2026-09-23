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
            for cand in (_os.path.join(d, 'Public_Projects', 'mahjong'), _os.path.join(d, 'mahjong')):
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
from mahjong.dealer import MahjongDealer

class MockPlayer:
    def __init__(self):
        self.hand = []

def test_mahjong_dealer_initialization():
    """Test that the dealer initializes correctly with a shuffled deck."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    
    # Verify deck exists and has cards (assuming init_deck returns a list)
    assert isinstance(dealer.deck, list)
    assert len(dealer.deck) > 0
    assert dealer.table == []

def test_mahjong_dealer_shuffle():
    """Test that shuffle modifies the deck order."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    
    # Capture initial state
    original_deck = list(dealer.deck)
    
    # Shuffle again
    dealer.shuffle()
    
    # With seed 42, the shuffle is deterministic. 
    # Verify the deck is not identical to the original order
    assert dealer.deck != original_deck
    assert len(dealer.deck) == len(original_deck)

def test_mahjong_dealer_deal_cards():
    """Test dealing cards to a player."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = MockPlayer()
    
    initial_deck_len = len(dealer.deck)
    num_to_deal = 5
    
    dealer.deal_cards(player, num_to_deal)
    
    # Verify player hand size
    assert len(player.hand) == num_to_deal
    # Verify deck size decreased
    assert len(dealer.deck) == initial_deck_len - num_to_deal

def test_mahjong_dealer_deal_zero_cards():
    """Test dealing zero cards."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = MockPlayer()
    
    initial_deck_len = len(dealer.deck)
    dealer.deal_cards(player, 0)
    
    assert len(player.hand) == 0
    assert len(dealer.deck) == initial_deck_len

def test_mahjong_dealer_deal_all_cards():
    """Test dealing all cards from the deck."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = MockPlayer()
    
    total_cards = len(dealer.deck)
    dealer.deal_cards(player, total_cards)
    
    assert len(player.hand) == total_cards
    assert len(dealer.deck) == 0

def test_mahjong_dealer_deal_pop_order():
    """Verify that deal_cards pops from the end of the list (LIFO)."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = MockPlayer()
    
    # Peek at the last card
    last_card = dealer.deck[-1]
    
    dealer.deal_cards(player, 1)
    
    # The card in hand should be the one that was at the end
    assert player.hand[0] == last_card

def test_mahjong_dealer_multiple_players():
    """Test dealing to multiple players sequentially."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    p1 = MockPlayer()
    p2 = MockPlayer()
    
    dealer.deal_cards(p1, 2)
    dealer.deal_cards(p2, 2)
    
    assert len(p1.hand) == 2
    assert len(p2.hand) == 2
    assert p1.hand[0] != p2.hand[0]

def test_mahjong_dealer_invalid_deal_count():
    """Test that dealing more cards than available raises an IndexError."""
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = MockPlayer()
    
    total_cards = len(dealer.deck)
    with pytest.raises(IndexError):
        dealer.deal_cards(player, total_cards + 1)
