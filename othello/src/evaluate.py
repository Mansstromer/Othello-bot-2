"""Position evaluation for Othello.

Provides advanced heuristics including stability, frontier, positional weights,
and parity analysis. Plus a lightweight evaluation engine that translates
raw scores into user-friendly predictions for the CLI.
"""

import math
from dataclasses import dataclass
from board import Board, get_legal_moves, CORNERS, X_SQUARES, DIRECTIONS, NOT_A_FILE, NOT_H_FILE


# TUNABLE: Evaluation weights (rebalanced for advanced features)
MOBILITY_WEIGHT = 15.0       # Value per legal move
CORNER_WEIGHT = 120.0        # Bonus for occupying a corner
X_SQUARE_PENALTY = -60.0     # Penalty for X-squares (when corner is empty)
PIECE_COUNT_WEIGHT = 1.0     # Value per piece (endgame focus)
STABILITY_WEIGHT = 25.0      # Value per stable piece
FRONTIER_WEIGHT = -8.0       # Penalty per frontier piece
POSITION_WEIGHT_SCALE = 1.0  # Scale for positional weights
PARITY_WEIGHT = 15.0         # Endgame parity bonus

# Positional weight table (8x8 board)
# Corners and edges are valuable, C-squares (diagonal to corner) are good
# X-squares are handled separately with context-aware penalty
POSITION_WEIGHTS = [
    120,  -20,   20,   10,   10,   20,  -20,  120,  # Row 1
    -20,  -40,   -5,   -5,   -5,   -5,  -40,  -20,  # Row 2
     20,   -5,   15,    5,    5,   15,   -5,   20,  # Row 3
     10,   -5,    5,    3,    3,    5,   -5,   10,  # Row 4
     10,   -5,    5,    3,    3,    5,   -5,   10,  # Row 5
     20,   -5,   15,    5,    5,   15,   -5,   20,  # Row 6
    -20,  -40,   -5,   -5,   -5,   -5,  -40,  -20,  # Row 7
    120,  -20,   20,   10,   10,   20,  -20,  120,  # Row 8
]


def count_stable_pieces(board: Board, player_pieces: int, opponent_pieces: int) -> int:
    """Count pieces that can never be flipped (stability analysis).

    A piece is stable if it cannot be flipped for the rest of the game.
    This includes:
    1. Corners (always stable)
    2. Pieces in stable edges connected to corners
    3. Pieces completely surrounded by stable pieces

    Args:
        board: Current board state
        player_pieces: Bitboard of player's pieces
        opponent_pieces: Bitboard of opponent's pieces

    Returns:
        Number of stable pieces
    """
    occupied = player_pieces | opponent_pieces
    stable = 0

    # Start with corners owned by player
    stable_mask = player_pieces & CORNERS

    # Iteratively expand stable region
    # A piece is stable if it's connected to stable pieces in all attack directions
    changed = True
    iterations = 0
    while changed and iterations < 10:  # Limit iterations for performance
        changed = False
        old_stable = stable_mask
        iterations += 1

        # Check all 8 directions
        for direction in DIRECTIONS:
            shift = abs(direction)

            # Get edge mask for this direction
            if direction in [1, 9, -7]:  # Right
                edge_mask = NOT_H_FILE
            elif direction in [-1, -9, 7]:  # Left
                edge_mask = NOT_A_FILE
            else:
                edge_mask = 0xFFFFFFFFFFFFFFFF

            # Expand stable region in this direction
            if direction > 0:
                new_stable = ((stable_mask & edge_mask) << shift) & player_pieces
            else:
                new_stable = ((stable_mask & edge_mask) >> shift) & player_pieces

            # Also check if piece is on edge and anchored
            # Pieces on edges are stable if all squares from corner to them are filled
            stable_mask |= new_stable

        if stable_mask != old_stable:
            changed = True

    return bin(stable_mask).count('1')


def count_frontier_pieces(player_pieces: int, opponent_pieces: int) -> int:
    """Count frontier pieces (pieces with at least one empty neighbor).

    Frontier pieces are vulnerable to capture. Fewer is better.

    Args:
        player_pieces: Bitboard of player's pieces
        opponent_pieces: Bitboard of opponent's pieces

    Returns:
        Number of frontier pieces
    """
    occupied = player_pieces | opponent_pieces
    empty = ~occupied & 0xFFFFFFFFFFFFFFFF

    frontier = 0

    # Check each direction for empty neighbors
    for direction in DIRECTIONS:
        shift = abs(direction)

        # Get edge mask
        if direction in [1, 9, -7]:
            edge_mask = NOT_H_FILE
        elif direction in [-1, -9, 7]:
            edge_mask = NOT_A_FILE
        else:
            edge_mask = 0xFFFFFFFFFFFFFFFF

        # Find player pieces with empty neighbors in this direction
        if direction > 0:
            frontier |= ((empty & edge_mask) >> shift) & player_pieces
        else:
            frontier |= ((empty & edge_mask) << shift) & player_pieces

    return bin(frontier).count('1')


def get_positional_value(player_pieces: int, opponent_pieces: int) -> float:
    """Calculate positional value based on piece locations.

    Args:
        player_pieces: Bitboard of player's pieces
        opponent_pieces: Bitboard of opponent's pieces

    Returns:
        Positional score difference (player - opponent)
    """
    player_value = 0.0
    opponent_value = 0.0

    for square in range(64):
        mask = 1 << square
        weight = POSITION_WEIGHTS[square]

        if player_pieces & mask:
            player_value += weight
        elif opponent_pieces & mask:
            opponent_value += weight

    return player_value - opponent_value


def get_parity_bonus(board: Board, player: str) -> float:
    """Calculate parity bonus in endgame.

    In endgame, the player who makes the last move in a region has an advantage.
    If total empty squares is odd, current player has parity advantage.

    Args:
        board: Current board state
        player: Player to evaluate for

    Returns:
        Parity bonus
    """
    occupied = board.black_pieces | board.white_pieces
    empty_count = 64 - bin(occupied).count('1')

    # Only apply in endgame (less than 20 empty squares)
    if empty_count >= 20:
        return 0.0

    # Calculate parity advantage
    # If empty count is odd and it's player's turn, they get last move
    parity = empty_count % 2

    if board.current_player == player:
        return parity * PARITY_WEIGHT
    else:
        return -parity * PARITY_WEIGHT


def is_corner_empty(corner_square: int, board: Board) -> bool:
    """Check if a corner square is empty.

    Args:
        corner_square: Corner square index
        board: Current board state

    Returns:
        True if corner is empty
    """
    occupied = board.black_pieces | board.white_pieces
    return not (occupied & (1 << corner_square))


def get_smart_x_square_penalty(board: Board, player_pieces: int) -> float:
    """Calculate X-square penalty only when adjacent corner is empty.

    X-squares are only bad if they give opponent access to the corner.

    Args:
        board: Current board state
        player_pieces: Bitboard of player's pieces

    Returns:
        X-square penalty
    """
    penalty = 0.0

    # Map X-squares to their adjacent corners
    # B2 (9) -> A1 (0), G2 (14) -> H1 (7)
    # B7 (49) -> A8 (56), G7 (54) -> H8 (63)
    x_to_corner = {
        9: 0,    # B2 -> A1
        14: 7,   # G2 -> H1
        49: 56,  # B7 -> A8
        54: 63,  # G7 -> H8
    }

    for x_square, corner in x_to_corner.items():
        # If player has X-square AND corner is empty, apply penalty
        if (player_pieces & (1 << x_square)) and is_corner_empty(corner, board):
            penalty += X_SQUARE_PENALTY

    return penalty


def evaluate(board: Board, player: str) -> float:
    """Evaluate board position from perspective of given player.

    Uses advanced heuristics:
    - Mobility (legal moves)
    - Stability (pieces that can't be flipped)
    - Frontier (pieces with empty neighbors)
    - Positional weights (some squares are better)
    - Corner control
    - Smart X-square penalty (context-aware)
    - Parity (endgame advantage)
    - Piece count (endgame tiebreaker)

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

    # --- STABILITY: Pieces that can never be flipped ---
    # Stable pieces are extremely valuable
    own_stable = count_stable_pieces(board, own_pieces, opp_pieces)
    opp_stable = count_stable_pieces(board, opp_pieces, own_pieces)
    score += (own_stable - opp_stable) * STABILITY_WEIGHT

    # --- FRONTIER: Pieces with empty neighbors ---
    # Frontier pieces are vulnerable - fewer is better
    own_frontier = count_frontier_pieces(own_pieces, opp_pieces)
    opp_frontier = count_frontier_pieces(opp_pieces, own_pieces)
    score += (own_frontier - opp_frontier) * FRONTIER_WEIGHT

    # --- POSITIONAL WEIGHTS: Some squares are inherently better ---
    position_value = get_positional_value(own_pieces, opp_pieces)
    score += position_value * POSITION_WEIGHT_SCALE

    # --- CORNERS: Included in positional weights, but corners are so important
    # they get double-counted here for extra emphasis
    own_corners = bin(own_pieces & CORNERS).count('1')
    opp_corners = bin(opp_pieces & CORNERS).count('1')
    score += (own_corners - opp_corners) * CORNER_WEIGHT

    # --- SMART X-SQUARES: Only penalize if adjacent corner is empty ---
    own_x_penalty = get_smart_x_square_penalty(board, own_pieces)
    opp_x_penalty = get_smart_x_square_penalty(board, opp_pieces)
    score += own_x_penalty - opp_x_penalty

    # --- PARITY: Endgame advantage for last move ---
    parity_bonus = get_parity_bonus(board, player)
    score += parity_bonus

    # --- PIECE COUNT: Total pieces (matters in endgame) ---
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
