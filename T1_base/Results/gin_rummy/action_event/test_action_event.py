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
                if _os.path.isfile(_os.path.join(cand, 'action_event.py')):
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
from gin_rummy import Card
import gin_rummy.utils as utils
from gin_rummy.action_event import (
    ActionEvent, ScoreNorthPlayerAction, ScoreSouthPlayerAction, 
    DrawCardAction, PickUpDiscardAction, DeclareDeadHandAction, 
    GinAction, DiscardAction, KnockAction
)

def test_action_event_equality():
    a1 = ActionEvent(10)
    a2 = ActionEvent(10)
    a3 = ActionEvent(11)
    assert a1 == a2
    assert a1 != a3
    assert a1 != "not an action"

def test_get_num_actions():
    # knock_action_id (58) + 52 = 110
    assert ActionEvent.get_num_actions() == 110

@pytest.mark.parametrize("action_id, expected_cls, expected_str", [
    (0, ScoreNorthPlayerAction, "score N"),
    (1, ScoreSouthPlayerAction, "score S"),
    (2, DrawCardAction, "draw_card"),
    (3, PickUpDiscardAction, "pick_up_discard"),
    (4, DeclareDeadHandAction, "declare_dead_hand"),
    (5, GinAction, "gin"),
])
def test_decode_simple_actions(action_id, expected_cls, expected_str):
    action = ActionEvent.decode_action(action_id)
    assert isinstance(action, expected_cls)
    assert str(action) == expected_str

def test_decode_discard_action():
    # Discard range 6 to 57. Let's test card_id 0 (index 6)
    action = ActionEvent.decode_action(6)
    assert isinstance(action, DiscardAction)
    assert action.action_id == 6
    assert isinstance(action.card, Card)
    assert str(action).startswith("discard ")

def test_decode_knock_action():
    # Knock range 58 to 109. Let's test card_id 0 (index 58)
    action = ActionEvent.decode_action(58)
    assert isinstance(action, KnockAction)
    assert action.action_id == 58
    assert isinstance(action.card, Card)
    assert str(action).startswith("knock ")

def test_decode_invalid_action():
    with pytest.raises(Exception, match="decode_action: unknown action_id=111"):
        ActionEvent.decode_action(111)

def test_discard_action_init():
    card = utils.get_card(0)
    action = DiscardAction(card=card)
    assert action.action_id == 6
    assert action.card == card

def test_knock_action_init():
    card = utils.get_card(0)
    action = KnockAction(card=card)
    assert action.action_id == 58
    assert action.card == card

def test_action_event_str_classes():
    assert str(ScoreNorthPlayerAction()) == "score N"
    assert str(ScoreSouthPlayerAction()) == "score S"
    assert str(DrawCardAction()) == "draw_card"
    assert str(PickUpDiscardAction()) == "pick_up_discard"
    assert str(DeclareDeadHandAction()) == "declare_dead_hand"
    assert str(GinAction()) == "gin"

@pytest.mark.parametrize("card_id", range(52))
def test_all_discard_actions(card_id):
    card = utils.get_card(card_id)
    action = DiscardAction(card=card)
    decoded = ActionEvent.decode_action(6 + card_id)
    assert decoded == action
    assert isinstance(decoded, DiscardAction)
    assert decoded.card == card

@pytest.mark.parametrize("card_id", range(52))
def test_all_knock_actions(card_id):
    card = utils.get_card(card_id)
    action = KnockAction(card=card)
    decoded = ActionEvent.decode_action(58 + card_id)
    assert decoded == action
    assert isinstance(decoded, KnockAction)
    assert decoded.card == card
