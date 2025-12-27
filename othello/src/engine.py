"""Othello engine API - main interface for external code.

Combines board, evaluation, and search into a single easy-to-use interface.
"""

import time
from typing import Optional, Tuple
from board import Board, get_legal_moves
from search import negamax, TranspositionTable


class OthelloEngine:
    """Othello game engine with iterative deepening search.

    This is the main class external code should interact with.
    """

    def __init__(self):
        """Initialize the engine."""
        self.tt: TranspositionTable = {}
        self.nodes_searched = 0
        self.max_depth_reached = 0

    def get_best_move(
        self,
        board: Board,
        time_limit_seconds: float = 5.0
    ) -> Tuple[Optional[int], float, int]:
        """Find best move using iterative deepening within time limit.

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
            return moves[0], 0.0, 0

        # Iterative deepening
        start_time = time.time()
        best_move = moves[0]
        best_score = float('-inf')
        depth = 1

        # Clear transposition table for new search
        self.tt.clear()

        while True:
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed >= time_limit_seconds and depth > 1:
                break

            # Search at current depth
            try:
                score, move = negamax(
                    board,
                    depth,
                    float('-inf'),
                    float('inf'),
                    board.current_player,
                    self.tt
                )

                if move is not None:
                    best_move = move
                    best_score = score
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

            # Stop if we've searched very deep
            if depth > 20:
                break

        return best_move, best_score, self.max_depth_reached

    def reset(self):
        """Reset engine state (clear transposition table)."""
        self.tt.clear()
        self.nodes_searched = 0
        self.max_depth_reached = 0
