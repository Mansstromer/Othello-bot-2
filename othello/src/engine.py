"""Othello engine API - main interface for external code.

Combines board, evaluation, and search into a single easy-to-use interface.
Features aspiration windows, iterative deepening, killer moves, and history heuristic.
"""

import time
from typing import Optional, Tuple
from board import Board, get_legal_moves
from search import negamax, TranspositionTable, KillerMoves, HistoryTable


class OthelloEngine:
    """Othello game engine with advanced search features.

    Features:
    - Iterative deepening
    - Aspiration windows
    - Killer move heuristic
    - History heuristic
    - Endgame perfect solver (automatic when ≤15 empties)

    This is the main class external code should interact with.
    """

    def __init__(self):
        """Initialize the engine."""
        self.tt: TranspositionTable = {}
        self.killer_moves: KillerMoves = {}
        self.history: HistoryTable = {}
        self.nodes_searched = 0
        self.max_depth_reached = 0
        self.pv_move: Optional[int] = None

    def get_best_move(
        self,
        board: Board,
        time_limit_seconds: float = 5.0
    ) -> Tuple[Optional[int], float, int]:
        """Find best move using iterative deepening with aspiration windows.

        Args:
            board: Current board state
            time_limit_seconds: Maximum time to search

        Returns:
            Tuple of (best_move, evaluation, depth_reached)
            best_move is None if no legal moves available
        """
        # Reset stats
        self.nodes_searched = 0
        self.max_depth_reached = 0

        # Get legal moves
        moves = get_legal_moves(board)
        if not moves:
            return None, 0.0, 0

        # If only one move, return immediately
        if len(moves) == 1:
            self.pv_move = moves[0]
            return moves[0], 0.0, 0

        # Iterative deepening with aspiration windows
        start_time = time.time()
        best_move = moves[0]
        best_score = 0.0
        depth = 1

        # Clear tables for new search (but keep history across moves for learning)
        self.tt.clear()
        self.killer_moves.clear()
        # Don't clear history - it accumulates learning

        # Aspiration window size
        ASPIRATION_WINDOW = 50.0

        while True:
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed >= time_limit_seconds and depth > 1:
                break

            # Set aspiration window
            if depth <= 2:
                # Use full window for shallow searches
                alpha = float('-inf')
                beta = float('inf')
            else:
                # Use narrow window based on previous score
                alpha = best_score - ASPIRATION_WINDOW
                beta = best_score + ASPIRATION_WINDOW

            # Search at current depth with aspiration window
            try:
                score, move = negamax(
                    board,
                    depth,
                    alpha,
                    beta,
                    board.current_player,
                    self.tt,
                    self.killer_moves,
                    self.history,
                    self.pv_move,
                    0
                )

                # Check if we failed outside the window
                if score <= alpha:
                    # Failed low - research with lower bound
                    score, move = negamax(
                        board,
                        depth,
                        float('-inf'),
                        beta,
                        board.current_player,
                        self.tt,
                        self.killer_moves,
                        self.history,
                        self.pv_move,
                        0
                    )
                elif score >= beta:
                    # Failed high - research with upper bound
                    score, move = negamax(
                        board,
                        depth,
                        alpha,
                        float('inf'),
                        board.current_player,
                        self.tt,
                        self.killer_moves,
                        self.history,
                        self.pv_move,
                        0
                    )

                if move is not None:
                    best_move = move
                    best_score = score
                    self.pv_move = move  # Store for next iteration
                    self.max_depth_reached = depth

            except KeyboardInterrupt:
                # Allow graceful interruption
                break

            # Check time again before incrementing depth
            elapsed = time.time() - start_time
            if elapsed >= time_limit_seconds:
                break

            # Increase depth for next iteration
            depth += 1

            # Stop if we've searched extremely deep (endgame solver handles deep endgames)
            if depth > 50:
                break

        return best_move, best_score, self.max_depth_reached

    def reset(self):
        """Reset engine state (clear all tables except history)."""
        self.tt.clear()
        self.killer_moves.clear()
        # Keep history for learning across games
        self.nodes_searched = 0
        self.max_depth_reached = 0
        self.pv_move = None
