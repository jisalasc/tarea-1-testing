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
                if _os.path.isfile(_os.path.join(cand, 'judger.py')):
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
from blackjack.judger import BlackjackJudger

class MockCard:
    def __init__(self, rank):
        self.rank = rank

class MockPlayer:
    def __init__(self, hand, status=None, score=0):
        self.hand = hand
        self.status = status
        self.score = score

class MockGame:
    def __init__(self, players, dealer):
        self.players = players
        self.dealer = dealer
        self.winner = {}

@pytest.fixture
def judger():
    return BlackjackJudger(np.random.RandomState(42))

def test_judge_score(judger):
    # Basic scores
    assert judger.judge_score([MockCard("2"), MockCard("3")]) == 5
    assert judger.judge_score([MockCard("T"), MockCard("K")]) == 20
    # Ace logic: 11 + 11 = 22 -> 12
    assert judger.judge_score([MockCard("A"), MockCard("A")]) == 12
    # Ace logic: 11 + 5 + 6 = 22 -> 12
    assert judger.judge_score([MockCard("A"), MockCard("5"), MockCard("6")]) == 12
    # No Ace
    assert judger.judge_score([MockCard("9"), MockCard("8")]) == 17

def test_judge_round(judger):
    player_alive = MockPlayer([MockCard("2"), MockCard("3")])
    status, score = judger.judge_round(player_alive)
    assert status == "alive"
    assert score == 5

    player_bust = MockPlayer([MockCard("K"), MockCard("Q"), MockCard("5")])
    status, score = judger.judge_round(player_bust)
    assert status == "bust"
    assert score == 25

def test_judge_game_logic(judger):
    # Setup scenarios
    p1 = MockPlayer([], status='alive', score=18)
    dealer_bust = MockPlayer([], status='bust', score=22)
    game = MockGame([p1], dealer_bust)
    
    # 1. Player alive, Dealer bust
    judger.judge_game(game, 0)
    assert game.winner['player0'] == 2

    # 2. Player bust
    p_bust = MockPlayer([], status='bust', score=22)
    game2 = MockGame([p_bust], MockPlayer([], status='alive', score=18))
    judger.judge_game(game2, 0)
    assert game2.winner['player0'] == -1

    # 3. Player higher score
    p_win = MockPlayer([], status='alive', score=20)
    d_lose = MockPlayer([], status='alive', score=19)
    game3 = MockGame([p_win], d_lose)
    judger.judge_game(game3, 0)
    assert game3.winner['player0'] == 2

    # 4. Dealer higher score
    p_lose = MockPlayer([], status='alive', score=15)
    d_win = MockPlayer([], status='alive', score=19)
    game4 = MockGame([p_lose], d_win)
    judger.judge_game(game4, 0)
    assert game4.winner['player0'] == -1

    # 5. Tie
    p_tie = MockPlayer([], status='alive', score=18)
    d_tie = MockPlayer([], status='alive', score=18)
    game5 = MockGame([p_tie], d_tie)
    judger.judge_game(game5, 0)
    assert game5.winner['player0'] == 1

def test_judge_score_complex_ace(judger):
    # Multiple aces handling
    # A, A, A, A = 11+1+1+1 = 14
    assert judger.judge_score([MockCard("A")] * 4) == 14
    # A, A, 9 = 11+1+9 = 21
    assert judger.judge_score([MockCard("A"), MockCard("A"), MockCard("9")]) == 21
    # A, A, T = 11+1+10 = 22 -> 12
    assert judger.judge_score([MockCard("A"), MockCard("A"), MockCard("T")]) == 12
