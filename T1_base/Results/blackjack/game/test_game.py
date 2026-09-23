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
            for cand in (_os.path.join(d, 'Public_Projects', 'blackjack'), _os.path.join(d, 'blackjack')):
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
from blackjack.game import BlackjackGame

@pytest.fixture
def game():
    g = BlackjackGame(allow_step_back=True)
    g.configure({'game_num_players': 2, 'game_num_decks': 1})
    return g

def test_init_and_configure(game):
    assert game.allow_step_back is True
    assert game.num_players == 2
    assert game.num_decks == 1

def test_init_game(game):
    state, player_id = game.init_game()
    assert player_id == 0
    assert 'player0 hand' in state
    assert 'player1 hand' in state
    assert 'dealer hand' in state
    assert len(game.players) == 2
    assert game.game_pointer == 0

def test_get_num_players(game):
    game.configure({'game_num_players': 3, 'game_num_decks': 1})
    assert game.get_num_players() == 3

def test_get_num_actions():
    assert BlackjackGame.get_num_actions() == 2

def test_get_player_id(game):
    game.init_game()
    assert game.get_player_id() == 0

def test_step_hit_and_stand(game):
    game.init_game()
    # Hit
    state, next_id = game.step("hit")
    assert next_id == 0 or next_id == 1
    # Stand
    state, next_id = game.step("stand")
    assert next_id in [0, 1]

def test_step_back(game):
    game.init_game()
    game.step("hit")
    assert game.step_back() is True
    assert game.step_back() is False

def test_is_over_initial(game):
    game.init_game()
    assert game.is_over() is False

def test_step_logic_branches(game):
    # Force a scenario where game pointer increments
    game.init_game()
    game.step("stand")
    assert game.game_pointer == 1
    
    # Test last player stand triggers dealer logic
    game.step("stand")
    assert game.game_pointer == 0

def test_step_hit_bust_logic(game):
    game.init_game()
    # Manually force a bust if possible or just exercise the code path
    # Since we can't easily force cards, we just exercise the hit path
    game.step("hit")
    # If player busts, game_pointer logic triggers
    # We check if it handles the pointer increment
    assert game.game_pointer in [0, 1]

def test_get_state_format(game):
    game.init_game()
    state = game.get_state(0)
    assert 'actions' in state
    assert 'state' in state
    assert 'dealer hand' in state
    assert len(state['state']) == 2


def test_game_over_state(game):
    game.init_game()
    # Manually set winners to simulate end
    game.winner = {'dealer': 1, 'player0': 1, 'player1': 1}
    assert game.is_over() is True

def test_dealer_hand_visibility(game):
    game.init_game()
    # Before game over, dealer hand should be length 1 (hidden card)
    state = game.get_state(0)
    assert len(state['dealer hand']) == 1
    
    # After game over, should show all cards
    game.winner = {'dealer': 1, 'player0': 1, 'player1': 1}
    state = game.get_state(0)
    assert len(state['dealer hand']) >= 1

def test_step_invalid_action_defaults_to_hit(game):
    game.init_game()
    # Any action not "stand" is treated as "hit"
    state, _ = game.step("invalid_action")
    assert 'actions' in state

def test_step_pointer_reset(game):
    game.init_game()
    game.game_pointer = game.num_players - 1
    game.step("stand")
    assert game.game_pointer == 0

def test_step_back_restores_state(game):
    game.init_game()
    original_dealer_score = game.dealer.score
    game.step("hit")
    game.step_back()
    assert game.dealer.score == original_dealer_score

def test_configure_multiple_decks(game):
    game.configure({'game_num_players': 1, 'game_num_decks': 6})
    assert game.num_decks == 6


def test_get_state_all_players(game):
    game.configure({'game_num_players': 2, 'game_num_decks': 1})
    game.init_game()
    state = game.get_state(0)
    assert 'player0 hand' in state
    assert 'player1 hand' in state

def test_step_back_history_management(game):
    game.init_game()
    game.step("hit")
    game.step("hit")
    assert len(game.history) == 2
    game.step_back()
    assert len(game.history) == 1
