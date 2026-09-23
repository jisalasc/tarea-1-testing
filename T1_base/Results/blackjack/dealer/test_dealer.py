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

import pytest
import numpy as np
from blackjack.dealer import init_standard_deck, BlackjackDealer
from blackjack.base import Card

class MockPlayer:
    def __init__(self):
        self.hand = []

def test_init_standard_deck():
    deck = init_standard_deck()
    assert len(deck) == 52
    assert isinstance(deck[0], Card)
    # Check for uniqueness
    assert len(set(deck)) == 52

def test_blackjack_dealer_initialization():
    rng = np.random.RandomState(42)
    # Test single deck
    dealer = BlackjackDealer(rng, num_decks=1)
    assert len(dealer.deck) == 52
    assert dealer.status == 'alive'
    assert dealer.score == 0
    
    # Test multi-deck
    dealer_multi = BlackjackDealer(rng, num_decks=2)
    assert len(dealer_multi.deck) == 104

def test_blackjack_dealer_infinite_deck():
    rng = np.random.RandomState(42)
    # num_decks=0 triggers infinite deck logic
    dealer = BlackjackDealer(rng, num_decks=0)
    assert len(dealer.deck) == 52  # init_standard_deck is called once
    
    player = MockPlayer()
    dealer.deal_card(player)
    assert len(player.hand) == 1
    # Check that card was NOT popped from deck
    assert len(dealer.deck) == 52

def test_shuffle():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=1)
    original_deck = list(dealer.deck)
    dealer.shuffle()
    assert len(dealer.deck) == 52
    assert dealer.deck != original_deck

def test_deal_card_removes_from_deck():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=1)
    player = MockPlayer()
    
    initial_len = len(dealer.deck)
    dealer.deal_card(player)
    
    assert len(player.hand) == 1
    assert len(dealer.deck) == initial_len - 1

def test_deal_card_logic():
    # Verify the card dealt is actually from the deck
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=1)
    player = MockPlayer()
    
    # Capture the state before dealing
    deck_snapshot = list(dealer.deck)
    dealer.deal_card(player)
    
    assert player.hand[0] in deck_snapshot
    assert player.hand[0] not in dealer.deck

@pytest.mark.parametrize("num_decks", [1, 2])
def test_dealer_state_consistency(num_decks):
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=num_decks)
    assert dealer.num_decks == num_decks
    assert dealer.status == 'alive'
    assert dealer.score == 0

def test_init_standard_deck_content():
    deck = init_standard_deck()
    # Verify specific cards exist
    assert Card('S', 'A') in deck
    assert Card('C', 'K') in deck
    assert Card('H', '7') in deck

def test_deal_card_multiple_times():
    rng = np.random.RandomState(42)
    dealer = BlackjackDealer(rng, num_decks=1)
    player = MockPlayer()
    
    dealer.deal_card(player)
    dealer.deal_card(player)
    
    assert len(player.hand) == 2
    assert len(dealer.deck) == 50
    assert player.hand[0] != player.hand[1]
