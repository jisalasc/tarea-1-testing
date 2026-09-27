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

import numpy as np
import pytest
from blackjack.judger import BlackjackJudger


class DummyCard:
    def __init__(self, rank):
        self.rank = rank


class DummyPlayer:
    def __init__(self, hand, status=None, score=None):
        self.hand = hand
        self.status = status
        self.score = score


class DummyDealer:
    def __init__(self, status=None, score=None):
        self.status = status
        self.score = score


class DummyGame:
    def __init__(self, players, dealer, winner=None):
        self.players = players
        self.dealer = dealer
        self.winner = winner if winner is not None else {}


@pytest.fixture
def judger():
    rng = np.random.RandomState(42)
    return BlackjackJudger(rng)


@pytest.mark.parametrize(
    "cards,expected_score",
    [
        ([DummyCard("2"), DummyCard("3")], 5),
        ([DummyCard("A"), DummyCard("9")], 20),
        ([DummyCard("A"), DummyCard("A")], 12),  # 22 -> 12
        ([DummyCard("A"), DummyCard("A"), DummyCard("A")], 13),  # 33 -> 23 -> 13
        ([DummyCard("T"), DummyCard("J"), DummyCard("Q")], 30),
        ([DummyCard("K"), DummyCard("A")], 21),
    ],
)
def test_judge_score(judger, cards, expected_score):
    score = judger.judge_score(cards)
    assert score == expected_score


@pytest.mark.parametrize(
    "hand,expected_status,expected_score",
    [
        ([DummyCard("T"), DummyCard("5")], "alive", 15),
        ([DummyCard("T"), DummyCard("K"), DummyCard("5")], "bust", 25),
    ],
)
def test_judge_round(judger, hand, expected_status, expected_score):
    player = DummyPlayer(hand=hand)
    status, score = judger.judge_round(player)
    assert status == expected_status
    assert score == expected_score


@pytest.mark.parametrize(
    "player_status,player_score,dealer_status,dealer_score,expected_winner_val",
    [
        ("bust", 25, "alive", 18, -1),      # player bust
        ("alive", 19, "bust", 25, 2),        # dealer bust, player not bust
        ("alive", 20, "alive", 18, 2),       # player score > dealer score
        ("alive", 17, "alive", 19, -1),      # player score < dealer score
        ("alive", 18, "alive", 18, 1),       # player score == dealer score
    ],
)
def test_judge_game(judger, player_status, player_score, dealer_status, dealer_score, expected_winner_val):
    player = DummyPlayer(hand=[], status=player_status, score=player_score)
    dealer = DummyDealer(status=dealer_status, score=dealer_score)
    game = DummyGame(players=[player], dealer=dealer)
    
    judger.judge_game(game, 0)
    
    assert game.winner == {"player0": expected_winner_val}


def test_init(judger):
    assert isinstance(judger.np_random, np.random.RandomState)
    assert judger.rank2score["A"] == 11
    assert judger.rank2score["K"] == 10
