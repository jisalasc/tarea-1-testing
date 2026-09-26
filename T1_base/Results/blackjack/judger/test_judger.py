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

from unittest.mock import MagicMock
import numpy as np
import pytest

from blackjack.judger import BlackjackJudger


@pytest.fixture
def judger():
    np_random = np.random.RandomState(42)
    return BlackjackJudger(np_random)


@pytest.mark.parametrize(
    "ranks,expected_score",
    [
        (["2", "3"], 5),
        (["T", "J", "Q", "K"], 40),
        (["A", "A"], 12),
        (["A", "9", "A"], 21),
        (["A", "A", "A"], 13),
        (["K", "5", "A"], 16),
        (["A", "K", "5"], 16),
        (["A", "K", "A"], 12),
    ],
)
def test_judge_score(judger, ranks, expected_score):
    cards = [MagicMock(rank=r) for r in ranks]
    assert judger.judge_score(cards) == expected_score


def test_judge_round_alive(judger):
    player = MagicMock()
    player.hand = [MagicMock(rank="T"), MagicMock(rank="5")]
    status, score = judger.judge_round(player)
    assert status == "alive"
    assert score == 15


def test_judge_round_bust(judger):
    player = MagicMock()
    player.hand = [MagicMock(rank="K"), MagicMock(rank="Q"), MagicMock(rank="5")]
    status, score = judger.judge_round(player)
    assert status == "bust"
    assert score == 25


@pytest.mark.parametrize(
    "player_status,dealer_status,player_score,dealer_score,expected_winner_val",
    [
        ("bust", "alive", 22, 18, -1),
        ("alive", "bust", 15, 22, 2),
        ("alive", "alive", 20, 18, 2),
        ("alive", "alive", 17, 19, -1),
        ("alive", "alive", 18, 18, 1),
    ],
)
def test_judge_game(
    judger,
    player_status,
    dealer_status,
    player_score,
    dealer_score,
    expected_winner_val,
):
    game = MagicMock()
    player = MagicMock()
    player.status = player_status
    player.score = player_score
    dealer = MagicMock()
    dealer.status = dealer_status
    dealer.score = dealer_score

    game.players = [player]
    game.dealer = dealer
    game.winner = {}
    game_pointer = 0

    judger.judge_game(game, game_pointer)

    assert game.winner["player0"] == expected_winner_val


def test_init_sets_attributes(judger):
    np_random = np.random.RandomState(123)
    j = BlackjackJudger(np_random)
    assert j.np_random is np_random
    assert j.rank2score["A"] == 11
    assert j.rank2score["K"] == 10
    assert j.rank2score["2"] == 2
