"""Search algorithms for Othello.

Implements negamax with alpha-beta pruning, move ordering, and transposition tables.
"""

from typing import Tuple, Optional, Dict
from board import Board, get_legal_moves, make_move, pass_turn, is_game_over, CORNERS
from evaluate import evaluate, evaluate_terminal


# Transposition table: maps board hash to (depth, score, best_move)
TranspositionTable = Dict[int, Tuple[int, float, Optional[int]]]


def board_hash(board: Board) -> int:
    """Create hash of board state for transposition table.

    Args:
        board: Board state

    Returns:
        Integer hash combining piece positions and current player
    """
    # Simple hash: combine bitboards with player bit
    player_bit = 1 if board.current_player == 'black' else 0
    return (board.black_pieces << 65) | (board.white_pieces << 1) | player_bit


def order_moves(board: Board, moves: list[int]) -> list[int]:
    """Order moves for better alpha-beta pruning.

    Priority:
    1. Corner moves (highest value)
    2. Non-corner moves
    3. X-square moves (lowest priority early game)

    Args:
        board: Current board state
        moves: List of legal moves

    Returns:
        Ordered list of moves
    """
    corners = []
    regular = []
    x_squares = []

    for move in moves:
        move_bit = 1 << move
        if move_bit & CORNERS:
            corners.append(move)
        elif move_bit & 0x0000420000004200:  # X-squares mask (simplified)
            x_squares.append(move)
        else:
            regular.append(move)

    # Try corners first, then regular moves, X-squares last
    return corners + regular + x_squares


def negamax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    player: str,
    tt: Optional[TranspositionTable] = None
) -> Tuple[float, Optional[int]]:
    """Negamax search with alpha-beta pruning.

    Args:
        board: Current board state
        depth: Remaining search depth
        alpha: Alpha bound for pruning
        beta: Beta bound for pruning
        player: Player to maximize for
        tt: Transposition table (optional)

    Returns:
        Tuple of (score, best_move)
        Score is from perspective of 'player'
        best_move is None if no legal moves
    """
    if tt is None:
        tt = {}

    # Check transposition table
    h = board_hash(board)
    if h in tt:
        stored_depth, stored_score, stored_move = tt[h]
        if stored_depth >= depth:
            return stored_score, stored_move

    # Terminal depth or game over
    if depth == 0:
        score = evaluate(board, player)
        return score, None

    if is_game_over(board):
        score = evaluate_terminal(board, player)
        return score, None

    # Get legal moves
    moves = get_legal_moves(board)

    # Must pass if no moves
    if not moves:
        passed_board = pass_turn(board)
        opponent = 'white' if player == 'black' else 'black'
        score, _ = negamax(passed_board, depth - 1, -beta, -alpha, opponent, tt)
        return -score, None

    # Order moves for better pruning
    ordered_moves = order_moves(board, moves)

    best_score = float('-inf')
    best_move = ordered_moves[0]

    for move in ordered_moves:
        new_board = make_move(board, move)

        # Switch perspective for negamax
        opponent = 'white' if player == 'black' else 'black'
        score, _ = negamax(new_board, depth - 1, -beta, -alpha, opponent, tt)
        score = -score  # Negate for current player

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        # Beta cutoff
        if alpha >= beta:
            break

    # Store in transposition table
    tt[h] = (depth, best_score, best_move)

    return best_score, best_move
