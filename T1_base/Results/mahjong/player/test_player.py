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

import pytest
import numpy as np
from unittest.mock import MagicMock
from mahjong.player import MahjongPlayer

class MockCard:
    def __init__(self, name):
        self.name = name
    def get_str(self):
        return self.name
    def __eq__(self, other):
        return self.name == other.name

@pytest.fixture
def player():
    np_random = np.random.RandomState(42)
    return MahjongPlayer(player_id=1, np_random=np_random)

def test_init(player):
    assert player.get_player_id() == 1
    assert player.hand == []
    assert player.pile == []

def test_print_methods(player, capsys):
    player.hand = [MockCard("A"), MockCard("B")]
    player.pile = [[MockCard("C"), MockCard("D")]]
    player.print_hand()
    player.print_pile()
    captured = capsys.readouterr()
    assert "['A', 'B']" in captured.out
    assert "[['C', 'D']]" in captured.out

def test_play_card(player):
    card1 = MockCard("A")
    card2 = MockCard("B")
    player.hand = [card1, card2]
    dealer = MagicMock()
    dealer.table = []
    
    player.play_card(dealer, card1)
    
    assert player.hand == [card2]
    assert dealer.table == [card1]

def test_chow(player):
    card_table = MockCard("T")
    card_hand1 = MockCard("A")
    card_hand2 = MockCard("B")
    player.hand = [card_hand1, card_hand2]
    dealer = MagicMock()
    dealer.table = [card_table]
    
    # Chow takes last card from table and two from hand
    player.chow(dealer, [card_hand1, card_hand2, card_table])
    
    assert dealer.table == []
    assert player.hand == []
    assert player.pile == [[card_hand1, card_hand2, card_table]]

def test_chow_partial_match(player):
    # Tests the logic: if card in self.hand and card != last_card
    card_table = MockCard("T")
    card_hand1 = MockCard("A")
    player.hand = [card_hand1]
    dealer = MagicMock()
    dealer.table = [card_table]
    
    # Only card_hand1 matches, card_table is the last_card
    player.chow(dealer, [card_hand1, card_table])
    
    assert player.hand == []
    assert player.pile == [[card_hand1, card_table]]

def test_gong(player):
    card1 = MockCard("A")
    card2 = MockCard("B")
    player.hand = [card1, card2]
    dealer = MagicMock()
    
    player.gong(dealer, [card1, card2])
    
    assert player.hand == []
    assert player.pile == [[card1, card2]]

def test_gong_no_match(player):
    card1 = MockCard("A")
    player.hand = [card1]
    dealer = MagicMock()
    # Card B is not in hand
    player.gong(dealer, [MockCard("B")])
    
    assert player.hand == [card1]
    assert player.pile == [[MockCard("B")]]

def test_pong(player):
    card1 = MockCard("A")
    card2 = MockCard("A")
    player.hand = [card1, card2]
    dealer = MagicMock()
    
    player.pong(dealer, [card1, card2])
    
    assert player.hand == []
    assert player.pile == [[card1, card2]]

def test_play_card_value_error(player):
    dealer = MagicMock()
    with pytest.raises(ValueError):
        player.play_card(dealer, MockCard("Missing"))

def test_chow_logic_branching(player):
    # Test chow with empty hand
    dealer = MagicMock()
    dealer.table = [MockCard("T")]
    player.chow(dealer, [MockCard("T")])
    assert player.pile == [[MockCard("T")]]

def test_gong_empty_cards(player):
    dealer = MagicMock()
    player.gong(dealer, [])
    assert player.pile == [[]]

def test_pong_empty_cards(player):
    dealer = MagicMock()
    player.pong(dealer, [])
    assert player.pile == [[]]

def test_complex_hand_state(player):
    cards = [MockCard(str(i)) for i in range(5)]
    player.hand = list(cards)
    dealer = MagicMock()
    dealer.table = []
    
    player.play_card(dealer, cards[2])
    assert len(player.hand) == 4
    assert cards[2] in dealer.table
    
    player.pong(dealer, [cards[0], cards[1]])
    assert len(player.hand) == 2
    assert [cards[0], cards[1]] in player.pile
