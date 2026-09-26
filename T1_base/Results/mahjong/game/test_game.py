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


def test_initialization():
    game = MahjongGame(allow_step_back=False)
    assert not game.allow_step_back
    assert game.num_players == 4
    assert isinstance(game.np_random, np.random.RandomState)

    game_with_step = MahjongGame(allow_step_back=True)
    assert game_with_step.allow_step_back


def test_init_game():
    game = MahjongGame(allow_step_back=True)
    state, current_player = game.init_game()
    
    assert isinstance(state, dict)
    assert isinstance(current_player, int)
    assert game.get_player_id() == current_player
    assert game.cur_state == state
    assert game.get_num_players() == 4
    assert game.dealer is not None
    assert len(game.players) == 4
    assert game.judger is not None
    assert game.round is not None
    assert game.history == []


def test_step_and_step_back():
    game = MahjongGame(allow_step_back=True)
    game.init_game()
    
    initial_round_player = game.round.current_player
    
    # Mock proceed_round to avoid hanging/complex logic
    game.round.proceed_round = lambda players, action: setattr(game.round, 'current_player', (game.round.current_player + 1) % 4)

    # Take a step with a dummy action
    next_state, next_player = game.step('check')
    assert isinstance(next_state, dict)
    assert isinstance(next_player, int)
    assert len(game.history) == 1

    # Test step_back
    success = game.step_back()
    assert success is True
    assert len(game.history) == 0
    assert game.round.current_player == initial_round_player


def test_step_back_without_history():
    game = MahjongGame(allow_step_back=False)
    game.init_game()
    
    success = game.step_back()
    assert success is False


def test_get_state():
    game = MahjongGame()
    game.init_game()
    state = game.get_state(0)
    assert isinstance(state, dict)


def test_get_legal_actions_play():
    # If state['valid_act'] is ['play'], get_legal_actions replaces it with state['action_cards']
    state = {
        'valid_act': ['play'],
        'action_cards': ['card1', 'card2']
    }
    legal = MahjongGame.get_legal_actions(state)
    assert legal == ['card1', 'card2']
    # Verify state['valid_act'] is also mutated per implementation
    assert state['valid_act'] == ['card1', 'card2']


def test_get_legal_actions_other():
    state = {
        'valid_act': ['call', 'fold']
    }
    legal = MahjongGame.get_legal_actions(state)
    assert legal == ['call', 'fold']


def test_get_num_actions():
    assert MahjongGame.get_num_actions() == 38


def test_get_num_players():
    game = MahjongGame()
    assert game.get_num_players() == 4


def test_get_player_id():
    game = MahjongGame()
    game.init_game()
    assert game.get_player_id() == game.round.current_player


def test_is_over():
    game = MahjongGame()
    game.init_game()
    game.judger.judge_game = lambda g: (False, None, None)
    over = game.is_over()
    assert isinstance(over, bool)
    assert hasattr(game, 'winner')


@pytest.mark.parametrize("allow_step_back", [True, False])
def test_game_modes(allow_step_back):
    game = MahjongGame(allow_step_back=allow_step_back)
    game.dealer = type('MockDealer', (), {'deal_cards': lambda self, *a: None})()
    game.players = [type('MockPlayer', (), {})() for _ in range(4)]
    game.judger = type('MockJudger', (), {'judge_game': lambda self, g: (False, 0, None)})()
    game.round = type('MockRound', (), {'current_player': 0, 'get_state': lambda self, p, id: {}})()
    state, player_id = game.init_game()
    assert state is not None
    assert player_id in range(4)
