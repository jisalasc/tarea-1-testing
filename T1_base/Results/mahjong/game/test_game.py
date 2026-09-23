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
                if _os.path.isfile(_os.path.join(cand, 'game.py')):
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
from mahjong.game import MahjongGame

@pytest.fixture
def game():
    return MahjongGame(allow_step_back=True)

def test_init(game):
    assert game.allow_step_back is True
    assert game.num_players == 4
    assert isinstance(game.np_random, np.random.RandomState)

def test_init_game(game):
    state, player_id = game.init_game()
    assert isinstance(state, dict)
    assert 0 <= player_id < 4
    assert len(game.players) == 4
    assert game.cur_state == state


def test_step_back_empty_history(game):
    # Initialize game to ensure attributes are set
    game.init_game()
    # Clear history to test empty state
    game.history = []
    assert game.step_back() is False

def test_get_state(game):
    game.init_game()
    state = game.get_state(0)
    assert isinstance(state, dict)

def test_get_legal_actions_play_branch(game):
    # Test the branch where valid_act is ['play']
    state = {'valid_act': ['play'], 'action_cards': ['1m', '2m']}
    actions = MahjongGame.get_legal_actions(state)
    assert actions == ['1m', '2m']

def test_get_legal_actions_other_branch(game):
    # Test the branch where valid_act is something else
    state = {'valid_act': ['pong', 'hu']}
    actions = MahjongGame.get_legal_actions(state)
    assert actions == ['pong', 'hu']

def test_get_num_actions(game):
    assert MahjongGame.get_num_actions() == 38

def test_get_num_players(game):
    assert game.get_num_players() == 4

def test_get_player_id(game):
    game.init_game()
    pid = game.get_player_id()
    assert 0 <= pid < 4

def test_is_over(game):
    game.init_game()
    # The result depends on the judger, but we verify it returns a boolean
    result = game.is_over()
    assert isinstance(result, bool)
    assert hasattr(game, 'winner')

def test_step_without_step_back():
    game = MahjongGame(allow_step_back=False)
    game.init_game()
    valid_actions = game.get_legal_actions(game.cur_state)
    game.step(valid_actions[0])
    assert not hasattr(game, 'history') or len(game.history) == 0

@pytest.mark.parametrize("player_id", [0, 1, 2, 3])
def test_get_state_for_all_players(game, player_id):
    game.init_game()
    state = game.get_state(player_id)
    assert isinstance(state, dict)

def test_game_flow_integration(game):
    # Simple integration test for core flow
    state, pid = game.init_game()
    assert pid == game.get_player_id()
    
    # Perform a move
    valid_actions = game.get_legal_actions(state)
    new_state, next_pid = game.step(valid_actions[0])
    assert isinstance(new_state, dict)
    assert next_pid != pid
    assert game.cur_state == new_state


def test_num_players_property(game):
    assert game.num_players == 4

def test_random_state_consistency():
    game1 = MahjongGame()
    game2 = MahjongGame()
    # Ensure random states are distinct
    assert game1.np_random is not game2.np_random

def test_step_back_multiple_times(game):
    game.init_game()
    valid_actions = game.get_legal_actions(game.cur_state)
    game.step(valid_actions[0])
    # After step, state changes, get new valid actions
    valid_actions_2 = game.get_legal_actions(game.cur_state)
    game.step(valid_actions_2[0])
    assert len(game.history) == 2
    game.step_back()
    game.step_back()
    assert len(game.history) == 0
    assert game.step_back() is False

def test_get_legal_actions_empty_list(game):
    state = {'valid_act': [], 'action_cards': []}
    assert MahjongGame.get_legal_actions(state) == []

def test_step_invalid_action_handling(game):
    # This tests that the game proceeds even if action is arbitrary
    game.init_game()
    with pytest.raises(Exception):
        game.step("invalid_action")

def test_judger_interaction(game):
    game.init_game()
    # Ensure judger exists and is accessible via game
    assert hasattr(game, 'judger')
    assert game.judger is not None
