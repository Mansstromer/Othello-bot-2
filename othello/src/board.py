"""Bitboard-based Othello/Reversi board representation.

Board layout (64 squares numbered 0-63):
  A B C D E F G H
1 0 1 2 3 4 5 6 7
2 8 9 ...       15
...
8 56...         63

Bitboards use two 64-bit integers to represent black and white pieces.
Bit N = 1 means a piece exists at square N.
"""

from typing import List, Optional
from dataclasses import dataclass


# Constants for board positions (row-major indexing)
A1, B1, C1, D1, E1, F1, G1, H1 = 0, 1, 2, 3, 4, 5, 6, 7
A2, B2, C2, D2, E2, F2, G2, H2 = 8, 9, 10, 11, 12, 13, 14, 15
A3, B3, C3, D3, E3, F3, G3, H3 = 16, 17, 18, 19, 20, 21, 22, 23
A4, B4, C4, D4, E4, F4, G4, H4 = 24, 25, 26, 27, 28, 29, 30, 31
A5, B5, C5, D5, E5, F5, G5, H5 = 32, 33, 34, 35, 36, 37, 38, 39
A6, B6, C6, D6, E6, F6, G6, H6 = 40, 41, 42, 43, 44, 45, 46, 47
A7, B7, C7, D7, E7, F7, G7, H7 = 48, 49, 50, 51, 52, 53, 54, 55
A8, B8, C8, D8, E8, F8, G8, H8 = 56, 57, 58, 59, 60, 61, 62, 63

# Corner squares (high value in Othello)
CORNERS = (1 << A1) | (1 << H1) | (1 << A8) | (1 << H8)

# X-squares (adjacent to corners, typically bad early game)
X_SQUARES = (1 << B2) | (1 << G2) | (1 << B7) | (1 << G7)

# Direction vectors for the 8 directions (N, NE, E, SE, S, SW, W, NW)
DIRECTIONS = [8, 9, 1, -7, -8, -9, -1, 7]

# Masks to prevent wrapping around board edges
NOT_A_FILE = 0xFEFEFEFEFEFEFEFE  # All bits except column A
NOT_H_FILE = 0x7F7F7F7F7F7F7F7F  # All bits except column H


@dataclass
class Board:
    """Othello board state using bitboards.

    Attributes:
        black_pieces: 64-bit integer with bits set for black pieces
        white_pieces: 64-bit integer with bits set for white pieces
        current_player: 'black' or 'white'
    """
    black_pieces: int
    white_pieces: int
    current_player: str

    @staticmethod
    def initial() -> 'Board':
        """Create board with standard Othello starting position.

        Initial position:
          . . . . . . . .
          . . . . . . . .
          . . . . . . . .
          . . . W B . . .
          . . . B W . . .
          . . . . . . . .
          . . . . . . . .
          . . . . . . . .
        """
        white = (1 << D4) | (1 << E5)  # D4 = 27, E5 = 36
        black = (1 << E4) | (1 << D5)  # E4 = 28, D5 = 35
        return Board(black, white, 'black')

    def copy(self) -> 'Board':
        """Create independent copy of this board."""
        return Board(self.black_pieces, self.white_pieces, self.current_player)

    def get_piece_at(self, square: int) -> Optional[str]:
        """Get piece color at square, or None if empty.

        Args:
            square: Square index (0-63)

        Returns:
            'black', 'white', or None
        """
        mask = 1 << square
        if self.black_pieces & mask:
            return 'black'
        if self.white_pieces & mask:
            return 'white'
        return None


def get_legal_moves(board: Board) -> List[int]:
    """Find all legal moves for current player using bitboard operations.

    A move is legal if it places a piece that flips at least one opponent piece.
    This happens when the new piece creates a continuous line to another friendly
    piece, with only opponent pieces in between.

    Args:
        board: Current board state

    Returns:
        List of legal move squares (0-63)
    """
    if board.current_player == 'black':
        own = board.black_pieces
        opp = board.white_pieces
    else:
        own = board.white_pieces
        opp = board.black_pieces

    empty = ~(own | opp) & 0xFFFFFFFFFFFFFFFF
    legal_mask = 0

    # Check each direction
    for direction in DIRECTIONS:
        # Get direction-specific mask to prevent wrapping
        if direction in [1, 9, -7]:  # Moving toward higher files (right)
            edge_mask = NOT_H_FILE
        elif direction in [-1, -9, 7]:  # Moving toward lower files (left)
            edge_mask = NOT_A_FILE
        else:
            edge_mask = 0xFFFFFFFFFFFFFFFF

        shift = abs(direction)

        # Find opponent pieces adjacent to own pieces in this direction
        if direction > 0:
            candidates = ((own & edge_mask) << shift) & opp
        else:
            candidates = ((own & edge_mask) >> shift) & opp

        # Extend along direction while hitting opponent pieces.
        # Mask before shifting so only pieces that still have neighbors
        # in this direction can keep moving (prevents wraparound).
        for _ in range(5):  # Max 6 flips in a row
            if direction > 0:
                candidates |= ((candidates & edge_mask) << shift) & opp
            else:
                candidates |= ((candidates & edge_mask) >> shift) & opp

        # One more step to find empty squares beyond opponent pieces
        if direction > 0:
            legal_mask |= ((candidates & edge_mask) << shift) & empty
        else:
            legal_mask |= ((candidates & edge_mask) >> shift) & empty

    # Convert bitmask to list of square indices
    moves = []
    for sq in range(64):
        if legal_mask & (1 << sq):
            moves.append(sq)

    return moves


def get_flipped_squares(board: Board, square: int) -> List[int]:
    """Get list of squares that would be flipped by placing a piece.

    Args:
        board: Current board state
        square: Square to place piece (0-63)

    Returns:
        List of square indices that would be flipped
    """
    if board.current_player == 'black':
        own_bits = board.black_pieces
        opp_bits = board.white_pieces
    else:
        own_bits = board.white_pieces
        opp_bits = board.black_pieces

    flips = 0

    # Check each direction for pieces to flip
    for direction in DIRECTIONS:
        # Get direction-specific mask
        if direction in [1, 9, -7]:
            edge_mask = NOT_H_FILE
        elif direction in [-1, -9, 7]:
            edge_mask = NOT_A_FILE
        else:
            edge_mask = 0xFFFFFFFFFFFFFFFF

        # Walk in direction to find pieces to flip
        candidates = 0
        pos = square

        for _ in range(6):
            if direction > 0:
                pos += direction
                if pos >= 64:
                    break
                # Check if we wrapped around an edge
                if direction in [1, 9, -7] and (1 << pos) & ~edge_mask:
                    break
                if direction in [-1, -9, 7] and (1 << square) & ~edge_mask:
                    break
            else:
                pos -= -direction
                if pos < 0:
                    break
                if direction in [1, 9, -7] and (1 << square) & ~edge_mask:
                    break
                if direction in [-1, -9, 7] and (1 << pos) & ~edge_mask:
                    break

            pos_bit = 1 << pos

            if pos_bit & opp_bits:
                candidates |= pos_bit
            elif pos_bit & own_bits:
                flips |= candidates
                break
            else:
                break

    # Convert bitmask to list of square indices
    flipped = []
    for sq in range(64):
        if flips & (1 << sq):
            flipped.append(sq)

    return flipped


def make_move(board: Board, square: int) -> Board:
    """Apply a move and return new board state (immutable).

    Places a piece at square and flips all opponent pieces that are
    bracketed by the new piece and existing friendly pieces.

    Args:
        board: Current board state
        square: Square to place piece (0-63)

    Returns:
        New board state after move
    """
    new_board = board.copy()

    if new_board.current_player == 'black':
        own_bits = new_board.black_pieces
        opp_bits = new_board.white_pieces
    else:
        own_bits = new_board.white_pieces
        opp_bits = new_board.black_pieces

    placed = 1 << square
    flips = 0

    # Check each direction for pieces to flip
    for direction in DIRECTIONS:
        # Get direction-specific mask
        if direction in [1, 9, -7]:
            edge_mask = NOT_H_FILE
        elif direction in [-1, -9, 7]:
            edge_mask = NOT_A_FILE
        else:
            edge_mask = 0xFFFFFFFFFFFFFFFF

        # Walk in direction to find pieces to flip
        candidates = 0
        pos = square

        for _ in range(6):
            if direction > 0:
                pos += direction
                if pos >= 64:
                    break
                # Check if we wrapped around an edge
                if direction in [1, 9, -7] and (1 << pos) & ~edge_mask:
                    break
                if direction in [-1, -9, 7] and (1 << square) & ~edge_mask:
                    break
            else:
                pos -= -direction
                if pos < 0:
                    break
                if direction in [1, 9, -7] and (1 << square) & ~edge_mask:
                    break
                if direction in [-1, -9, 7] and (1 << pos) & ~edge_mask:
                    break

            pos_bit = 1 << pos

            if pos_bit & opp_bits:
                candidates |= pos_bit
            elif pos_bit & own_bits:
                flips |= candidates
                break
            else:
                break

    # Apply flips
    own_bits |= placed | flips
    opp_bits &= ~flips

    # Update board
    if new_board.current_player == 'black':
        new_board.black_pieces = own_bits
        new_board.white_pieces = opp_bits
        new_board.current_player = 'white'
    else:
        new_board.white_pieces = own_bits
        new_board.black_pieces = opp_bits
        new_board.current_player = 'black'

    return new_board


def pass_turn(board: Board) -> Board:
    """Pass turn to opponent (used when no legal moves available).

    Args:
        board: Current board state

    Returns:
        New board with player switched
    """
    new_board = board.copy()
    new_board.current_player = 'white' if board.current_player == 'black' else 'black'
    return new_board


def is_game_over(board: Board) -> bool:
    """Check if game is over (no legal moves for either player).

    Args:
        board: Current board state

    Returns:
        True if game is over
    """
    if get_legal_moves(board):
        return False

    # Current player has no moves; check if opponent has any
    opponent_board = pass_turn(board)
    return len(get_legal_moves(opponent_board)) == 0


def get_winner(board: Board) -> Optional[str]:
    """Determine winner by counting pieces.

    Args:
        board: Board state (should be game over)

    Returns:
        'black', 'white', or None for tie
    """
    black_count = bin(board.black_pieces).count('1')
    white_count = bin(board.white_pieces).count('1')

    if black_count > white_count:
        return 'black'
    elif white_count > black_count:
        return 'white'
    else:
        return None


def board_to_string(board: Board) -> str:
    """Convert board to human-readable string.

    Args:
        board: Board state

    Returns:
        Multi-line string representation
    """
    lines = ['  A B C D E F G H']
    for row in range(8):
        line = f'{row + 1} '
        for col in range(8):
            sq = row * 8 + col
            piece = board.get_piece_at(sq)
            if piece == 'black':
                line += 'B '
            elif piece == 'white':
                line += 'W '
            else:
                line += '. '
        lines.append(line)
    return '\n'.join(lines)
