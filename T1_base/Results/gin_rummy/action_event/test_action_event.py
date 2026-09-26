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
import utils as utils
from gin_rummy import Card
from gin_rummy.action_event import (
    ActionEvent,
    ScoreNorthPlayerAction,
    ScoreSouthPlayerAction,
    DrawCardAction,
    PickUpDiscardAction,
    DeclareDeadHandAction,
    GinAction,
    DiscardAction,
    KnockAction,
    score_player_0_action_id,
    score_player_1_action_id,
    draw_card_action_id,
    pick_up_discard_action_id,
    declare_dead_hand_action_id,
    gin_action_id,
    discard_action_id,
    knock_action_id,
)


def test_action_event_init_and_equality():
    event1 = ActionEvent(10)
    event2 = ActionEvent(10)
    event3 = ActionEvent(20)

    assert event1.action_id == 10
    assert event1 == event2
    assert event1 != event3
    assert event1 != "not an action event"


def test_get_num_actions():
    num_actions = ActionEvent.get_num_actions()
    assert num_actions == knock_action_id + 52


@pytest.mark.parametrize(
    "action_id,expected_type,expected_str",
    [
        (score_player_0_action_id, ScoreNorthPlayerAction, "score N"),
        (score_player_1_action_id, ScoreSouthPlayerAction, "score S"),
        (draw_card_action_id, DrawCardAction, "draw_card"),
        (pick_up_discard_action_id, PickUpDiscardAction, "pick_up_discard"),
        (declare_dead_hand_action_id, DeclareDeadHandAction, "declare_dead_hand"),
        (gin_action_id, GinAction, "gin"),
    ],
)
def test_decode_action_basic_events(action_id, expected_type, expected_str):
    action = ActionEvent.decode_action(action_id)
    assert isinstance(action, expected_type)
    assert action.action_id == action_id
    assert str(action) == expected_str


@pytest.mark.parametrize("card_id", [0, 10, 25, 51])
def test_decode_action_discard(card_id):
    action_id = discard_action_id + card_id
    card = utils.get_card(card_id=card_id)
    action = ActionEvent.decode_action(action_id)
    assert isinstance(action, DiscardAction)
    assert action.action_id == action_id
    assert action.card == card
    assert str(action) == f"discard {str(card)}"


@pytest.mark.parametrize("card_id", [0, 12, 30, 51])
def test_decode_action_knock(card_id):
    action_id = knock_action_id + card_id
    card = utils.get_card(card_id=card_id)
    action = ActionEvent.decode_action(action_id)
    assert isinstance(action, KnockAction)
    assert action.action_id == action_id
    assert action.card == card
    assert str(action) == f"knock {str(card)}"




def test_score_north_player_action():
    action = ScoreNorthPlayerAction()
    assert action.action_id == score_player_0_action_id
    assert str(action) == "score N"
    assert action == ActionEvent(score_player_0_action_id)


def test_score_south_player_action():
    action = ScoreSouthPlayerAction()
    assert action.action_id == score_player_1_action_id
    assert str(action) == "score S"
    assert action == ActionEvent(score_player_1_action_id)


def test_draw_card_action():
    action = DrawCardAction()
    assert action.action_id == draw_card_action_id
    assert str(action) == "draw_card"
    assert action == ActionEvent(draw_card_action_id)


def test_pick_up_discard_action():
    action = PickUpDiscardAction()
    assert action.action_id == pick_up_discard_action_id
    assert str(action) == "pick_up_discard"
    assert action == ActionEvent(pick_up_discard_action_id)


def test_declare_dead_hand_action():
    action = DeclareDeadHandAction()
    assert action.action_id == declare_dead_hand_action_id
    assert str(action) == "declare_dead_hand"
    assert action == ActionEvent(declare_dead_hand_action_id)


def test_gin_action():
    action = GinAction()
    assert action.action_id == gin_action_id
    assert str(action) == "gin"
    assert action == ActionEvent(gin_action_id)


@pytest.mark.parametrize("card_id", [0, 5, 15, 51])
def test_discard_action(card_id):
    card = utils.get_card(card_id=card_id)
    action = DiscardAction(card=card)
    expected_id = discard_action_id + card_id
    assert action.action_id == expected_id
    assert action.card == card
    assert str(action) == f"discard {str(card)}"
    assert action == ActionEvent(expected_id)


@pytest.mark.parametrize("card_id", [0, 7, 22, 51])
def test_knock_action(card_id):
    card = utils.get_card(card_id=card_id)
    action = KnockAction(card=card)
    expected_id = knock_action_id + card_id
    assert action.action_id == expected_id
    assert action.card == card
    assert str(action) == f"knock {str(card)}"
    assert action == ActionEvent(expected_id)
