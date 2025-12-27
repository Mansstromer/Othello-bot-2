"""Search algorithms for Othello.

Implements negamax with alpha-beta pruning, move ordering, transposition tables,
endgame perfect solver, and advanced move ordering heuristics.
"""

from typing import Tuple, Optional, Dict, List
from board import Board, get_legal_moves, make_move, pass_turn, is_game_over, CORNERS
from evaluate import evaluate, evaluate_terminal


# Transposition table: maps board hash to (depth, score, best_move)
TranspositionTable = Dict[int, Tuple[int, float, Optional[int]]]

# Killer moves: moves that caused beta cutoffs at each depth
KillerMoves = Dict[int, List[int]]

# History heuristic: tracks how often moves are good
HistoryTable = Dict[int, int]


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


def order_moves(
    board: Board,
    moves: list[int],
    pv_move: Optional[int] = None,
    killer_moves: Optional[List[int]] = None,
    history: Optional[HistoryTable] = None
) -> list[int]:
    """Order moves for better alpha-beta pruning.

    Priority (highest to lowest):
    1. PV move (best move from previous iteration)
    2. Corner moves
    3. Killer moves (moves that caused cutoffs)
    4. Other moves sorted by history heuristic
    5. X-square moves (lowest priority)

    Args:
        board: Current board state
        moves: List of legal moves
        pv_move: Principal variation move (best from previous search)
        killer_moves: Moves that caused beta cutoffs at this depth
        history: History heuristic table

    Returns:
        Ordered list of moves
    """
    if not moves:
        return []

    # Initialize history if not provided
    if history is None:
        history = {}

    # Categorize moves
    pv = []
    corners = []
    killers = []
    regular = []
    x_squares = []

    for move in moves:
        move_bit = 1 << move

        # PV move gets highest priority
        if pv_move is not None and move == pv_move:
            pv.append(move)
        # Corners are always good
        elif move_bit & CORNERS:
            corners.append(move)
        # Killer moves get priority
        elif killer_moves and move in killer_moves:
            killers.append(move)
        # X-squares are risky
        elif move_bit & 0x0000420000004200:  # X-squares mask
            x_squares.append(move)
        else:
            regular.append(move)

    # Sort regular moves by history heuristic (moves that worked well before)
    regular.sort(key=lambda m: history.get(m, 0), reverse=True)

    # Combine in priority order
    return pv + corners + killers + regular + x_squares


def solve_endgame(
    board: Board,
    alpha: float,
    beta: float,
    player: str,
    tt: Optional[TranspositionTable] = None
) -> Tuple[float, Optional[int]]:
    """Perfect endgame solver - searches to completion.

    Used when few squares remain (typically ≤15 empties).
    Returns exact game-theoretic value.

    Args:
        board: Current board state
        alpha: Alpha bound
        beta: Beta bound
        player: Player to maximize for
        tt: Transposition table

    Returns:
        Tuple of (exact_score, best_move)
    """
    if tt is None:
        tt = {}

    # Check transposition table
    h = board_hash(board)
    if h in tt:
        stored_depth, stored_score, stored_move = tt[h]
        # In endgame solver, we want exact scores, so always use TT entry
        return stored_score, stored_move

    # Game over - return exact terminal value
    if is_game_over(board):
        score = evaluate_terminal(board, player)
        return score, None

    # Get legal moves
    moves = get_legal_moves(board)

    # Must pass if no moves
    if not moves:
        passed_board = pass_turn(board)
        opponent = 'white' if player == 'black' else 'black'
        score, _ = solve_endgame(passed_board, -beta, -alpha, opponent, tt)
        return -score, None

    # Order moves for better pruning
    ordered_moves = order_moves(board, moves)

    best_score = float('-inf')
    best_move = ordered_moves[0]

    for move in ordered_moves:
        new_board = make_move(board, move)

        # Recursively solve
        opponent = 'white' if player == 'black' else 'black'
        score, _ = solve_endgame(new_board, -beta, -alpha, opponent, tt)
        score = -score

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        # Beta cutoff
        if alpha >= beta:
            break

    # Store in transposition table with infinite depth (exact)
    tt[h] = (9999, best_score, best_move)

    return best_score, best_move


def negamax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    player: str,
    tt: Optional[TranspositionTable] = None,
    killer_moves: Optional[KillerMoves] = None,
    history: Optional[HistoryTable] = None,
    pv_move: Optional[int] = None,
    current_depth: int = 0
) -> Tuple[float, Optional[int]]:
    """Negamax search with alpha-beta pruning, killer moves, and history heuristic.

    Automatically switches to endgame solver when ≤15 empty squares remain.

    Args:
        board: Current board state
        depth: Remaining search depth
        alpha: Alpha bound for pruning
        beta: Beta bound for pruning
        player: Player to maximize for
        tt: Transposition table (optional)
        killer_moves: Killer move table (optional)
        history: History heuristic table (optional)
        pv_move: Principal variation move from previous iteration
        current_depth: Current search depth (for killer moves)

    Returns:
        Tuple of (score, best_move)
        Score is from perspective of 'player'
        best_move is None if no legal moves
    """
    if tt is None:
        tt = {}
    if killer_moves is None:
        killer_moves = {}
    if history is None:
        history = {}

    # Check if we should use endgame solver
    occupied = board.black_pieces | board.white_pieces
    empty_count = 64 - bin(occupied).count('1')

    # Switch to perfect solver in endgame
    if empty_count <= 15:
        return solve_endgame(board, alpha, beta, player, tt)

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
        score, _ = negamax(passed_board, depth - 1, -beta, -alpha, opponent, tt,
                          killer_moves, history, None, current_depth + 1)
        return -score, None

    # Get killer moves for this depth
    depth_killers = killer_moves.get(current_depth, [])

    # Order moves with advanced heuristics
    ordered_moves = order_moves(board, moves, pv_move, depth_killers, history)

    best_score = float('-inf')
    best_move = ordered_moves[0]

    for move in ordered_moves:
        new_board = make_move(board, move)

        # Switch perspective for negamax
        opponent = 'white' if player == 'black' else 'black'
        score, _ = negamax(new_board, depth - 1, -beta, -alpha, opponent, tt,
                          killer_moves, history, None, current_depth + 1)
        score = -score  # Negate for current player

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        # Beta cutoff - update killer moves and history
        if alpha >= beta:
            # Store killer move
            if current_depth not in killer_moves:
                killer_moves[current_depth] = []
            if move not in killer_moves[current_depth]:
                killer_moves[current_depth].insert(0, move)
                # Keep only top 2 killers per depth
                killer_moves[current_depth] = killer_moves[current_depth][:2]

            # Update history heuristic
            history[move] = history.get(move, 0) + depth * depth

            break

    # Store in transposition table
    tt[h] = (depth, best_score, best_move)

    return best_score, best_move
