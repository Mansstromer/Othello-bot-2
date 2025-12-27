#!/usr/bin/env python3
"""CLI to play Othello against the bot.

Human plays black, bot plays white.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from board import Board, get_legal_moves, make_move, pass_turn, is_game_over, get_winner, get_flipped_squares
from engine import OthelloEngine
from evaluate import EvaluationEngine
import ui


def square_to_notation(square: int) -> str:
    """Convert square index to algebraic notation (e.g., 19 -> 'D3').

    Args:
        square: Square index (0-63)

    Returns:
        Algebraic notation string
    """
    row = square // 8
    col = square % 8
    return f"{chr(ord('A') + col)}{row + 1}"


def notation_to_square(notation: str) -> int:
    """Convert algebraic notation to square index (e.g., 'D3' -> 19).

    Args:
        notation: Algebraic notation (e.g., 'D3')

    Returns:
        Square index (0-63)

    Raises:
        ValueError: If notation is invalid
    """
    if len(notation) != 2:
        raise ValueError("Notation must be 2 characters (e.g., 'D3')")

    col = ord(notation[0].upper()) - ord('A')
    row = int(notation[1]) - 1

    if not (0 <= col < 8 and 0 <= row < 8):
        raise ValueError("Invalid square notation")

    return row * 8 + col


def make_move_with_animation(board: Board, square: int) -> Board:
    """Make a move with flip animation.

    Args:
        board: Current board state
        square: Square to place piece

    Returns:
        New board state after move
    """
    # Get squares that will flip
    flipped = get_flipped_squares(board, square)
    flipped_set = set(flipped)
    flipped_set.add(square)  # Include the placed piece in animation

    # Make the actual move
    new_board = make_move(board, square)

    # Show animation if pieces were flipped
    if flipped_set:
        ui.animate_flip(board, new_board, flipped_set)

    return new_board


def get_human_move(board: Board) -> int:
    """Prompt human for move and validate it.

    Args:
        board: Current board state

    Returns:
        Selected square index
    """
    legal_moves = get_legal_moves(board)

    while True:
        try:
            notation = ui.get_input("\nYour move (e.g., D3):").strip()
            square = notation_to_square(notation)

            if square in legal_moves:
                return square
            else:
                ui.display_message(f"Illegal move! Legal moves: {', '.join(square_to_notation(m) for m in legal_moves)}", "bold red")

        except ValueError as e:
            ui.display_message(f"Invalid input: {e}", "bold red")
        except (KeyboardInterrupt, EOFError):
            ui.display_message("\nGame aborted.", "bold yellow")
            sys.exit(0)


def play_game():
    """Main game loop."""
    ui.console.clear()
    ui.display_message("=== Othello ===", "bold cyan")
    ui.display_message("You are Black (●), bot is White (○)", "bold")
    ui.display_message("Enter moves in algebraic notation (e.g., D3, C4)\n", "dim")

    board = Board.initial()
    engine = OthelloEngine()
    evaluation_engine = EvaluationEngine()

    while not is_game_over(board):
        legal_moves = get_legal_moves(board)

        # Display current position
        ui.display_board(board, legal_moves if board.current_player == 'black' else None,
                        title=f"Othello - {board.current_player.capitalize()}'s turn")

        # Display score
        ui.display_score(board)

        # Display evaluation
        prediction = evaluation_engine.evaluate_position(board)
        bot_win_pct = prediction.win_probability * 100
        if prediction.leader == 'even':
            status = "Balanced position"
        elif prediction.leader == 'bot':
            status = f"Bot ahead by {prediction.score:.1f}"
        else:
            status = f"You are ahead by {abs(prediction.score):.1f}"
        ui.display_evaluation(status, bot_win_pct)

        if not legal_moves:
            # Must pass
            ui.display_message(f"\n{board.current_player.capitalize()} has no legal moves. Passing...", "bold yellow")
            board = pass_turn(board)
            time.sleep(1.5)
            continue

        if board.current_player == 'black':
            # Human move
            ui.display_legal_moves(legal_moves, square_to_notation)
            square = get_human_move(board)
            ui.display_message(f"\nYou play {square_to_notation(square)}", "bold green")
            board = make_move_with_animation(board, square)

        else:
            # Bot move
            ui.display_message("\nBot is thinking...", "bold magenta")
            start = time.time()

            move, score, depth = engine.get_best_move(board, time_limit_seconds=3.0)

            elapsed = time.time() - start

            if move is None:
                ui.display_message("Bot has no legal moves. Passing...", "bold yellow")
                board = pass_turn(board)
            else:
                ui.display_message(f"Bot plays {square_to_notation(move)}", "bold red")
                ui.display_message(f"(depth: {depth}, eval: {score:.1f}, time: {elapsed:.2f}s)", "dim")
                board = make_move_with_animation(board, move)
                time.sleep(0.5)

    # Game over
    winner = get_winner(board)
    ui.display_game_over(board, winner)


if __name__ == '__main__':
    play_game()
