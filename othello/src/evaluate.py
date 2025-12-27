"""Position evaluation for Othello.

Provides basic heuristics plus a lightweight evaluation engine that translates
raw scores into user-friendly predictions for the CLI.
"""

import math
from dataclasses import dataclass
from board import Board, get_legal_moves, CORNERS, X_SQUARES


# TUNABLE: Evaluation weights
MOBILITY_WEIGHT = 10.0  # Value per legal move
CORNER_WEIGHT = 100.0   # Bonus for occupying a corner
X_SQUARE_PENALTY = -50.0  # Penalty for X-squares (early game)
PIECE_COUNT_WEIGHT = 1.0  # Value per piece (endgame focus)


def evaluate(board: Board, player: str) -> float:
    """Evaluate board position from perspective of given player.

    Positive score = good for player
    Negative score = bad for player

    Args:
        board: Current board state
        player: Player to evaluate for ('black' or 'white')

    Returns:
        Evaluation score as float
    """
    score = 0.0

    # Determine player and opponent pieces
    if player == 'black':
        own_pieces = board.black_pieces
        opp_pieces = board.white_pieces
    else:
        own_pieces = board.white_pieces
        opp_pieces = board.black_pieces

    # --- MOBILITY: Number of legal moves ---
    # More moves = more options = better position
    own_board = Board(
        black_pieces=board.black_pieces,
        white_pieces=board.white_pieces,
        current_player=player
    )
    own_mobility = len(get_legal_moves(own_board))

    opponent = 'white' if player == 'black' else 'black'
    opp_board = Board(
        black_pieces=board.black_pieces,
        white_pieces=board.white_pieces,
        current_player=opponent
    )
    opp_mobility = len(get_legal_moves(opp_board))

    score += (own_mobility - opp_mobility) * MOBILITY_WEIGHT

    # --- CORNERS: High-value stable pieces ---
    # Corners can never be flipped
    own_corners = bin(own_pieces & CORNERS).count('1')
    opp_corners = bin(opp_pieces & CORNERS).count('1')
    score += (own_corners - opp_corners) * CORNER_WEIGHT

    # --- X-SQUARES: Penalty for giving opponent corners ---
    # X-squares adjacent to corners are risky if corner is empty
    own_x_squares = bin(own_pieces & X_SQUARES).count('1')
    opp_x_squares = bin(opp_pieces & X_SQUARES).count('1')
    score += (own_x_squares - opp_x_squares) * X_SQUARE_PENALTY

    # --- PIECE COUNT: Total pieces (matters more in endgame) ---
    own_count = bin(own_pieces).count('1')
    opp_count = bin(opp_pieces).count('1')
    score += (own_count - opp_count) * PIECE_COUNT_WEIGHT

    return score


def evaluate_terminal(board: Board, player: str) -> float:
    """Evaluate terminal (game over) position.

    Returns large positive/negative scores for wins/losses.

    Args:
        board: Terminal board state
        player: Player to evaluate for

    Returns:
        +inf for win, -inf for loss, 0 for tie
    """
    if player == 'black':
        own_count = bin(board.black_pieces).count('1')
        opp_count = bin(board.white_pieces).count('1')
    else:
        own_count = bin(board.white_pieces).count('1')
        opp_count = bin(board.black_pieces).count('1')

    piece_diff = own_count - opp_count

    if piece_diff > 0:
        return 10000.0 + piece_diff  # Win + piece advantage
    elif piece_diff < 0:
        return -10000.0 + piece_diff  # Loss + piece disadvantage
    else:
        return 0.0  # Tie


@dataclass
class EvaluationSummary:
    """Human-friendly description of the current position."""

    score: float          # Positive = bot/white advantage
    win_probability: float  # Estimated chance bot wins (0-1)
    leader: str           # 'bot', 'human', or 'even'


class EvaluationEngine:
    """Translate heuristic scores into user-facing predictions."""

    def __init__(self, logistic_scale: float = 40.0):
        """Create an evaluator.

        Args:
            logistic_scale: Controls how quickly scores map to probabilities.
        """
        self.logistic_scale = logistic_scale

    def evaluate_position(self, board: Board) -> EvaluationSummary:
        """Summarize current position from the bot's perspective."""
        score = evaluate(board, 'white')  # Bot always plays white
        # Convert score to pseudo win probability via logistic function.
        scaled = max(min(score / self.logistic_scale, 60), -60)
        win_probability = 1.0 / (1.0 + math.exp(-scaled))

        if score > 1e-6:
            leader = 'bot'
        elif score < -1e-6:
            leader = 'human'
        else:
            leader = 'even'

        return EvaluationSummary(score=score, win_probability=win_probability, leader=leader)
