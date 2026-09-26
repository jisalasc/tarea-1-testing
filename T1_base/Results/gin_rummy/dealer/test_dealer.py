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


class DummyPlayer:
    """A minimal mock-like player to track calls without relying on complex internal states."""
    def __init__(self):
        self.hand = []
        self.populated_count = 0

    def did_populate_hand(self):
        self.populated_count += 1


@pytest.fixture
def rng():
    return np.random.RandomState(42)


def test_dealer_initialization(rng):
    dealer = GinRummyDealer(rng)
    
    assert dealer.np_random is rng
    assert dealer.discard_pile == []
    # Standard deck from utils.get_deck() has 52 cards
    assert len(dealer.shuffled_deck) == 52
    assert len(dealer.stock_pile) == 52
    # stock_pile should be a copy of shuffled_deck
    assert dealer.stock_pile == dealer.shuffled_deck
    # But they should be separate list instances
    assert dealer.stock_pile is not dealer.shuffled_deck


def test_deal_cards_normal(rng):
    dealer = GinRummyDealer(rng)
    player = DummyPlayer()
    
    initial_stock_len = len(dealer.stock_pile)
    num_to_deal = 5
    
    dealer.deal_cards(player, num_to_deal)
    
    assert len(player.hand) == num_to_deal
    assert len(dealer.stock_pile) == initial_stock_len - num_to_deal
    assert player.populated_count == 1


@pytest.mark.parametrize("num_cards", [0, 1, 10])
def test_deal_cards_various_counts(rng, num_cards):
    dealer = GinRummyDealer(rng)
    player = DummyPlayer()
    
    dealer.deal_cards(player, num_cards)
    
    assert len(player.hand) == num_cards
    assert player.populated_count == 1


def test_deal_cards_with_actual_gin_rummy_player(rng):
    dealer = GinRummyDealer(rng)
    player = GinRummyPlayer(player_id=0, np_random=rng)
    
    dealer.deal_cards(player, 7)
    
    assert len(player.hand) == 7
    # GinRummyPlayer doesn't raise error on did_populate_hand
