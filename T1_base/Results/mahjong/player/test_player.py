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


def test_init(rng):
    player = MahjongPlayer(player_id=2, np_random=rng)
    assert player.get_player_id() == 2
    assert player.np_random is rng
    assert player.hand == []
    assert player.pile == []


def test_get_player_id(player):
    assert player.get_player_id() == 1


def test_print_hand(player, capsys):
    c1 = DummyCard("1m")
    c2 = DummyCard("2m")
    player.hand = [c1, c2]
    player.print_hand()
    captured = capsys.readouterr()
    assert "['1m', '2m']" in captured.out


def test_print_pile(player, capsys):
    c1 = DummyCard("1p")
    c2 = DummyCard("2p")
    player.pile = [[c1, c2]]
    player.print_pile()
    captured = capsys.readouterr()
    assert "[['1p', '2p']]" in captured.out


def test_play_card(player):
    c1 = DummyCard("1s")
    c2 = DummyCard("2s")
    player.hand = [c1, c2]
    dealer = DummyDealer(table=[])

    player.play_card(dealer, c1)

    assert player.hand == [c2]
    assert dealer.table == [c1]


def test_play_card_raises_when_card_not_in_hand(player):
    c1 = DummyCard("1s")
    c2 = DummyCard("2s")
    player.hand = [c2]
    dealer = DummyDealer(table=[])

    with pytest.raises(ValueError):
        player.play_card(dealer, c1)


def test_chow_standard(player):
    c_hand1 = DummyCard("2m")
    c_hand2 = DummyCard("3m")
    c_last = DummyCard("1m")
    player.hand = [c_hand1, c_hand2, DummyCard("9p")]
    dealer = DummyDealer(table=[c_last])

    chow_cards = [c_last, c_hand1, c_hand2]
    player.chow(dealer, chow_cards)

    assert dealer.table == []
    assert player.hand == [DummyCard("9p")]
    assert player.pile == [chow_cards]


def test_chow_card_not_in_hand(player):
    c_hand = DummyCard("2m")
    c_missing = DummyCard("3m")
    c_last = DummyCard("1m")
    player.hand = [c_hand]
    dealer = DummyDealer(table=[c_last])

    chow_cards = [c_last, c_missing, c_hand]
    player.chow(dealer, chow_cards)

    assert dealer.table == []
    assert player.hand == []
    assert player.pile == [chow_cards]


def test_chow_last_card_branch_exclusion(player):
    c_last = DummyCard("1m")
    player.hand = [c_last]
    dealer = DummyDealer(table=[c_last])

    # c_last == last_card, so `card != last_card` evaluates to False for c_last,
    # meaning it won't be popped from self.hand even though it's in hand.
    chow_cards = [c_last]
    player.chow(dealer, chow_cards)

    assert dealer.table == []
    assert player.hand == [c_last]
    assert player.pile == [chow_cards]


def test_pong_standard(player):
    c1 = DummyCard("5p")
    c2 = DummyCard("5p")
    c3 = DummyCard("5p")
    player.hand = [c1, c2, DummyCard("1s")]
    dealer = DummyDealer(table=[])

    pong_cards = [c1, c2, c3]
    player.pong(dealer, pong_cards)

    assert player.hand == [DummyCard("1s")]
    assert player.pile == [pong_cards]


def test_pong_card_not_in_hand(player):
    c1 = DummyCard("5p")
    c_missing = DummyCard("5p")
    player.hand = [c1]
    dealer = DummyDealer(table=[])

    pong_cards = [c1, c_missing, c_missing]
    player.pong(dealer, pong_cards)

    assert player.hand == []
    assert player.pile == [pong_cards]


def test_gong_standard(player):
    c1 = DummyCard("9z")
    c2 = DummyCard("9z")
    c3 = DummyCard("9z")
    c4 = DummyCard("9z")
    player.hand = [c1, c2, c3, c4]
    dealer = DummyDealer(table=[])

    gong_cards = [c1, c2, c3, c4]
    player.gong(dealer, gong_cards)

    assert player.hand == []
    assert player.pile == [gong_cards]


def test_gong_card_not_in_hand(player):
    c1 = DummyCard("9z")
    c_missing = DummyCard("9z")
    player.hand = [c1]
    dealer = DummyDealer(table=[])

    gong_cards = [c1, c_missing, c_missing, c_missing]
    player.gong(dealer, gong_cards)

    assert player.hand == []
    assert player.pile == [gong_cards]
