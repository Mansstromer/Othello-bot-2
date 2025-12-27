"""Tests for evaluation engine predictions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from board import Board
from evaluate import EvaluationEngine


def make_board(black_indices, white_indices, current_player='black'):
    black = 0
    for idx in black_indices:
        black |= 1 << idx
    white = 0
    for idx in white_indices:
        white |= 1 << idx
    return Board(black, white, current_player)


def test_initial_position_is_even():
    engine = EvaluationEngine()
    board = Board.initial()
    summary = engine.evaluate_position(board)
    assert summary.leader == 'even'
    assert summary.win_probability == summary.win_probability  # not NaN
    assert abs(summary.win_probability - 0.5) < 1e-6


def test_bot_advantage_in_summary():
    engine = EvaluationEngine(logistic_scale=10.0)
    board = make_board(
        black_indices=[0, 1],  # Two black pieces
        white_indices=[9, 10, 11, 18, 19, 20, 27, 28, 29]  # White swarm
    )
    summary = engine.evaluate_position(board)
    assert summary.leader == 'bot'
    assert summary.score > 0
    assert summary.win_probability > 0.5


def test_human_advantage_in_summary():
    engine = EvaluationEngine(logistic_scale=10.0)
    board = make_board(
        black_indices=[0, 1, 2, 8, 9, 10, 16, 17, 18],  # Strong black area
        white_indices=[63]  # Lone white piece
    )
    summary = engine.evaluate_position(board)
    assert summary.leader == 'human'
    assert summary.score < 0
    assert summary.win_probability < 0.5
