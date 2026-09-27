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


def test_init_default():
    game = MahjongGame()
    assert game.allow_step_back is False
    assert game.num_players == 4
    assert isinstance(game.np_random, np.random.RandomState)


def test_init_with_step_back():
    game = MahjongGame(allow_step_back=True)
    assert game.allow_step_back is True


def test_get_num_actions():
    assert MahjongGame.get_num_actions() == 38


def test_get_num_players():
    game = MahjongGame()
    assert game.get_num_players() == 4


def test_init_game_returns_state_and_player():
    game = MahjongGame()
    state, player_id = game.init_game()
    assert isinstance(state, dict)
    assert isinstance(player_id, int)
    assert 0 <= player_id < 4
    assert game.cur_state == state


def test_get_player_id():
    game = MahjongGame()
    game.init_game()
    pid = game.get_player_id()
    assert isinstance(pid, int)
    assert pid == game.round.current_player


def test_get_state():
    game = MahjongGame()
    game.init_game()
    state = game.get_state(0)
    assert isinstance(state, dict)


def test_step_without_step_back():
    game = MahjongGame(allow_step_back=False)
    state, player_id = game.init_game()
    legal_actions = game.get_legal_actions(state)
    action = legal_actions[0] if legal_actions else 'check'
    
    next_state, next_player = game.step(action)
    assert isinstance(next_state, dict)
    assert isinstance(next_player, int)
    assert game.history == []


def test_step_with_step_back_records_history():
    game = MahjongGame(allow_step_back=True)
    state, player_id = game.init_game()
    legal_actions = game.get_legal_actions(state)
    action = legal_actions[0] if legal_actions else 'check'

    game.step(action)
    assert len(game.history) == 1


def test_step_back_empty_history():
    game = MahjongGame(allow_step_back=True)
    game.init_game()
    success = game.step_back()
    assert success is False


def test_step_back_success():
    game = MahjongGame(allow_step_back=True)
    state, player_id = game.init_game()
    legal_actions = game.get_legal_actions(state)
    action = legal_actions[0] if legal_actions else 'check'

    game.step(action)
    assert len(game.history) == 1

    success = game.step_back()
    assert success is True
    assert len(game.history) == 0


def test_get_legal_actions_play_branch():
    state = {'valid_act': ['play'], 'action_cards': ['card1', 'card2']}
    actions = MahjongGame.get_legal_actions(state)
    assert actions == ['card1', 'card2']
    assert state['valid_act'] == ['card1', 'card2']


def test_get_legal_actions_other_branch():
    state = {'valid_act': ['chow', 'pong']}
    actions = MahjongGame.get_legal_actions(state)
    assert actions == ['chow', 'pong']


def test_is_over():
    game = MahjongGame()
    game.init_game()
    over = game.is_over()
    assert isinstance(over, bool)
    assert hasattr(game, 'winner')
