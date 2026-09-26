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

import numpy as np
import pytest

from mahjong.dealer import MahjongDealer


class DummyPlayer:
    def __init__(self):
        self.hand = []


def test_dealer_initialization():
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)

    assert dealer.np_random is rng
    assert isinstance(dealer.deck, list)
    assert len(dealer.deck) > 0
    assert dealer.table == []


def test_dealer_shuffle():
    rng1 = np.random.RandomState(42)
    rng2 = np.random.RandomState(42)

    dealer1 = MahjongDealer(rng1)
    deck_before = list(dealer1.deck)

    # Force a shuffle with the same seed-state rng
    dealer1.shuffle()
    deck_after = dealer1.deck

    # Just checking that shuffle runs successfully and modifies/keeps deck length
    assert len(deck_after) == len(deck_before)


def test_deal_cards():
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = DummyPlayer()

    initial_deck_len = len(dealer.deck)
    deal_num = 5

    dealer.deal_cards(player, deal_num)

    assert len(player.hand) == deal_num
    assert len(dealer.deck) == initial_deck_len - deal_num


def test_deal_zero_cards():
    rng = np.random.RandomState(42)
    dealer = MahjongDealer(rng)
    player = DummyPlayer()

    initial_deck_len = len(dealer.deck)
    dealer.deal_cards(player, 0)

    assert player.hand == []
    assert len(dealer.deck) == initial_deck_len
