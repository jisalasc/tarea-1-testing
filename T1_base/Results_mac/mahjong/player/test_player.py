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
                if _os.path.isfile(_os.path.join(cand, 'player.py')):
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
from mahjong.player import MahjongPlayer


class DummyCard:
    def __init__(self, name):
        self.name = name

    def get_str(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, DummyCard):
            return self.name == other.name
        return False


class DummyDealer:
    def __init__(self, table=None):
        self.table = table if table is not None else []


@pytest.fixture
def rng():
    return np.random.RandomState(42)


@pytest.fixture
def player(rng):
    return MahjongPlayer(player_id=1, np_random=rng)


def test_init_and_get_player_id(rng):
    player = MahjongPlayer(player_id=5, np_random=rng)
    assert player.get_player_id() == 5
    assert player.player_id == 5
    assert player.np_random is rng
    assert player.hand == []
    assert player.pile == []


def test_print_hand(player, capsys):
    player.hand = [DummyCard("1M"), DummyCard("2M")]
    player.print_hand()
    captured = capsys.readouterr()
    assert "['1M', '2M']" in captured.out


def test_print_pile(player, capsys):
    player.pile = [[DummyCard("1P"), DummyCard("2P")]]
    player.print_pile()
    captured = capsys.readouterr()
    assert "[['1P', '2P']]" in captured.out


def test_play_card(player):
    c1 = DummyCard("1S")
    c2 = DummyCard("2S")
    player.hand = [c1, c2]
    dealer = DummyDealer(table=[])

    player.play_card(dealer, c1)

    assert player.hand == [c2]
    assert dealer.table == [c1]


def test_chow_standard(player):
    c_last = DummyCard("3W")
    c_hand1 = DummyCard("1W")
    c_hand2 = DummyCard("2W")
    player.hand = [c_hand1, c_hand2, DummyCard("9W")]
    dealer = DummyDealer(table=[DummyCard("4W"), c_last])

    cards_to_chow = [c_hand1, c_hand2, c_last]
    player.chow(dealer, cards_to_chow)

    # c_last was popped from dealer table, hand had c_hand1 and c_hand2 removed, pile got cards_to_chow
    assert dealer.table == [DummyCard("4W")]
    assert player.hand == [DummyCard("9W")]
    assert player.pile == [cards_to_chow]


def test_chow_missing_or_last_card_branches(player):
    c_last = DummyCard("3W")
    c_hand1 = DummyCard("1W")
    # c_last is in cards, but not removed from hand because card != last_card check
    # Also test a card in cards that is NOT in hand (should be ignored by 'if card in self.hand')
    c_absent = DummyCard("5W")
    player.hand = [c_hand1, DummyCard("9W")]
    dealer = DummyDealer(table=[c_last])

    cards_to_chow = [c_hand1, c_absent, c_last]
    player.chow(dealer, cards_to_chow)

    assert dealer.table == []
    assert player.hand == [DummyCard("9W")]
    assert player.pile == [cards_to_chow]


def test_gong_standard(player):
    c1 = DummyCard("5Z")
    player.hand = [c1, DummyCard("1Z")]
    dealer = DummyDealer(table=[])

    gong_cards = [c1, c1, c1, c1]
    player.gong(dealer, gong_cards)

    assert player.hand == [DummyCard("1Z")]
    assert player.pile == [gong_cards]


def test_gong_partial_in_hand(player):
    c1 = DummyCard("5Z")
    c_absent = DummyCard("6Z")
    player.hand = [c1, DummyCard("1Z")]
    dealer = DummyDealer(table=[])

    gong_cards = [c1, c_absent]
    player.gong(dealer, gong_cards)

    assert player.hand == [DummyCard("1Z")]
    assert player.pile == [gong_cards]


def test_pong_standard(player):
    c1 = DummyCard("2Z")
    player.hand = [c1, c1, DummyCard("3Z")]
    dealer = DummyDealer(table=[])

    pong_cards = [c1, c1, c1]
    player.pong(dealer, pong_cards)

    assert player.hand == [DummyCard("3Z")]
    assert player.pile == [pong_cards]


def test_pong_partial_in_hand(player):
    c1 = DummyCard("2Z")
    c_absent = DummyCard("4Z")
    player.hand = [c1, DummyCard("3Z")]
    dealer = DummyDealer(table=[])

    pong_cards = [c1, c_absent]
    player.pong(dealer, pong_cards)

    assert player.hand == [DummyCard("3Z")]
    assert player.pile == [pong_cards]
