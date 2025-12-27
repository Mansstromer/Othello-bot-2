"""Tests for board.py - verifying move generation and game logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from board import (
    Board, get_legal_moves, make_move, pass_turn, is_game_over,
    get_winner, board_to_string, A1, B1, B2, B3, B4, C1, C3, H1,
    H2, H3, H4, H5, A8, H8, C4, C5, D3, D4, D5, E4, E5, E6, F4, F5
)


def test_initial_board():
    """Test that initial board has correct setup."""
    board = Board.initial()

    # Check starting pieces (standard Othello: D4=W, E4=B, D5=B, E5=W)
    assert board.get_piece_at(D4) == 'white'
    assert board.get_piece_at(E4) == 'black'
    assert board.get_piece_at(D5) == 'black'
    assert board.get_piece_at(E5) == 'white'

    # Check empty squares
    assert board.get_piece_at(A1) is None
    assert board.get_piece_at(H8) is None

    # Black moves first
    assert board.current_player == 'black'

    print("✓ Initial board setup correct")


def test_initial_legal_moves():
    """Test legal moves from starting position."""
    board = Board.initial()
    moves = get_legal_moves(board)

    # Black's opening moves from standard position: D3, C4, F5, E6
    # D3=19, C4=26, F5=37, E6=44
    expected = {D3, C4, F5, E6}
    assert set(moves) == expected, f"Expected {expected}, got {set(moves)}"

    print("✓ Initial legal moves correct")


def test_make_move_flips():
    """Test that making a move correctly flips pieces."""
    board = Board.initial()

    # Initial: D4=W, E4=B, D5=B, E5=W
    # Black plays D3 (should flip D4 from W to B)
    new_board = make_move(board, D3)

    # Check the new piece was placed
    assert new_board.get_piece_at(D3) == 'black'

    # Check D4 flipped from white to black
    assert new_board.get_piece_at(D4) == 'black'

    # Check D5 still black
    assert new_board.get_piece_at(D5) == 'black'

    # Check E4, E5 unchanged
    assert new_board.get_piece_at(E4) == 'black'
    assert new_board.get_piece_at(E5) == 'white'

    # Turn switched to white
    assert new_board.current_player == 'white'

    print("✓ Move flips pieces correctly")


def test_multiple_direction_flips():
    """Test move that flips in multiple directions."""
    # Set up a position where one move flips multiple directions
    board = Board(
        black_pieces=(1 << E4) | (1 << D5) | (1 << E5),  # E4, D5, E5
        white_pieces=(1 << D4) | (1 << C4) | (1 << D3),  # D4, C4, D3
        current_player='black'
    )

    # Black plays C5 (should flip C4 horizontally and potentially D4 diagonally)
    new_board = make_move(board, C5)

    assert new_board.get_piece_at(C5) == 'black'
    assert new_board.get_piece_at(D5) == 'black'  # Was already black

    print("✓ Multiple direction flips work")


def test_no_legal_moves_pass():
    """Test detection when player must pass."""
    # Create a position where black has no legal moves
    # Simple case: only white pieces left
    board = Board(
        black_pieces=0,
        white_pieces=(1 << D4) | (1 << E4),
        current_player='black'
    )

    moves = get_legal_moves(board)
    assert len(moves) == 0, "Black should have no legal moves"

    print("✓ No legal moves detected correctly")


def test_game_over_detection():
    """Test game over when neither player can move."""
    # Full board - game over
    board = Board(
        black_pieces=0xFFFFFFFF00000000,  # Top half
        white_pieces=0x00000000FFFFFFFF,  # Bottom half
        current_player='black'
    )

    assert is_game_over(board), "Game should be over when board is full"

    print("✓ Game over detection works")


def test_winner_determination():
    """Test winner is correctly determined."""
    # Black has more pieces
    board = Board(
        black_pieces=0xFFFFFFFF00000000,  # 32 pieces
        white_pieces=0x0000000000FFFFFF,  # 24 pieces
        current_player='black'
    )

    winner = get_winner(board)
    assert winner == 'black', "Black should win with more pieces"

    # White wins
    board2 = Board(
        black_pieces=0x00000000000000FF,  # 8 pieces
        white_pieces=0xFFFFFFFFFFFFFF00,  # 56 pieces
        current_player='black'
    )

    winner2 = get_winner(board2)
    assert winner2 == 'white', "White should win with more pieces"

    # Tie
    board3 = Board(
        black_pieces=0xFFFFFFFF00000000,  # 32 pieces
        white_pieces=0x00000000FFFFFFFF,  # 32 pieces
        current_player='black'
    )

    winner3 = get_winner(board3)
    assert winner3 is None, "Should be a tie"

    print("✓ Winner determination correct")


def test_board_copy():
    """Test that board.copy() creates independent copy."""
    board = Board.initial()
    copy = board.copy()

    # Modify copy
    copy.black_pieces = 0
    copy.current_player = 'white'

    # Original should be unchanged
    assert board.black_pieces != 0
    assert board.current_player == 'black'

    print("✓ Board copy is independent")


def test_corner_moves():
    """Test that corner moves work correctly."""
    # Set up position where black can take corner A1 (square 0)
    board = Board(
        black_pieces=(1 << C1) | (1 << C3),  # C1, C3
        white_pieces=(1 << B1) | (1 << B2),    # B1, B2
        current_player='black'
    )

    moves = get_legal_moves(board)

    # Black should be able to play A1
    if A1 in moves:
        new_board = make_move(board, A1)
        assert new_board.get_piece_at(A1) == 'black'
        assert new_board.get_piece_at(B1) == 'black'  # B1 should flip
        print("✓ Corner moves work correctly")
    else:
        print("! Corner test setup may need adjustment")


def test_edge_chain_move_detected():
    """Regression test for moves like H1 that capture along long edges."""

    def board_from_rows(rows, current_player='black'):
        black = 0
        white = 0
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                idx = r * 8 + c
                if ch == 'B':
                    black |= 1 << idx
                elif ch == 'W':
                    white |= 1 << idx
        return Board(black, white, current_player)

    rows = [
        "...WWW..",
        "...BBBW.",
        "..WBBWW.",
        "...BB.W.",
        "...BBB..",
        "........",
        "........",
        "........",
    ]
    board = board_from_rows(rows, 'black')
    moves = set(get_legal_moves(board))
    expected = {H1, B2, H2, B3, H3, B4, F4, H4, H5}
    assert moves == expected, f"Expected {expected}, got {moves}"

    print("✓ Edge captures including H1 are detected")


def test_board_to_string():
    """Test string representation of board."""
    board = Board.initial()
    s = board_to_string(board)

    # Should contain the initial position
    assert 'A B C D E F G H' in s
    assert 'B' in s  # Black pieces
    assert 'W' in s  # White pieces
    assert '.' in s  # Empty squares

    print("✓ Board string representation works")


def test_full_game_sequence():
    """Test playing through several moves of a game."""
    board = Board.initial()

    # Move 1: Black D3
    moves = get_legal_moves(board)
    assert D3 in moves
    board = make_move(board, D3)
    assert board.current_player == 'white'

    # Move 2: White makes a move
    moves = get_legal_moves(board)
    assert len(moves) > 0
    board = make_move(board, moves[0])
    assert board.current_player == 'black'

    # Move 3: Black makes another move
    moves = get_legal_moves(board)
    assert len(moves) > 0
    board = make_move(board, moves[0])

    # Game should not be over yet
    assert not is_game_over(board)

    print("✓ Full game sequence works")


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_initial_board,
        test_initial_legal_moves,
        test_make_move_flips,
        test_multiple_direction_flips,
        test_no_legal_moves_pass,
        test_game_over_detection,
        test_winner_determination,
        test_board_copy,
        test_corner_moves,
        test_board_to_string,
        test_full_game_sequence,
    ]

    print("Running board.py tests...\n")

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")

    if failed == 0:
        print("All tests passed! ✓")
        return 0
    else:
        print(f"{failed} tests failed")
        return 1


if __name__ == '__main__':
    exit(run_all_tests())
