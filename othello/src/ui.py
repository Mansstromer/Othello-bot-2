"""Enhanced UI module for Othello with colors and animations.

Uses the rich library for colorful terminal output and animations.
"""

import time
from typing import List, Optional, Set
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich import box

from board import Board


console = Console()


# Color schemes
BLACK_PIECE_STYLE = "black on white"
WHITE_PIECE_STYLE = "white on black"
EMPTY_SQUARE_STYLE = "dim green"
LEGAL_MOVE_STYLE = "bold yellow on dim"
BOARD_BORDER_STYLE = "cyan"


def create_piece_display(piece: Optional[str], is_legal_move: bool = False, flip_frame: int = 0) -> Text:
    """Create a colored display for a piece or empty square.

    Args:
        piece: 'black', 'white', or None for empty
        is_legal_move: Whether this square is a legal move
        flip_frame: Animation frame (0-4) for flip animation, 0 = no animation

    Returns:
        Rich Text object with appropriate styling
    """
    if flip_frame > 0:
        # Animation frames for flipping
        frames = ["◐", "◓", "◑", "◒"]
        char = frames[(flip_frame - 1) % 4]
        return Text(f" {char} ", style="bold magenta")

    if is_legal_move:
        return Text(" · ", style=LEGAL_MOVE_STYLE)
    elif piece == 'black':
        return Text(" ● ", style=BLACK_PIECE_STYLE)
    elif piece == 'white':
        return Text(" ○ ", style=WHITE_PIECE_STYLE)
    else:
        return Text("   ", style=EMPTY_SQUARE_STYLE)


def create_board_table(board: Board, legal_moves: Optional[List[int]] = None,
                       flipping_squares: Optional[Set[int]] = None, flip_frame: int = 0) -> Table:
    """Create a rich Table displaying the board.

    Args:
        board: Current board state
        legal_moves: Optional list of legal moves to highlight
        flipping_squares: Set of squares that are currently flipping
        flip_frame: Animation frame for flips

    Returns:
        Rich Table object
    """
    table = Table(show_header=True, show_edge=True, box=box.HEAVY,
                  border_style=BOARD_BORDER_STYLE, padding=(0, 0))

    # Add column headers
    table.add_column("", style="cyan bold", width=3)
    for col in "ABCDEFGH":
        table.add_column(col, style="cyan bold", justify="center", width=3)

    legal_moves_set = set(legal_moves) if legal_moves else set()
    flipping_set = flipping_squares if flipping_squares else set()

    # Add rows
    for row in range(8):
        row_cells = [Text(str(row + 1), style="cyan bold")]

        for col in range(8):
            sq = row * 8 + col
            piece = board.get_piece_at(sq)
            is_legal = sq in legal_moves_set
            is_flipping = sq in flipping_set

            cell = create_piece_display(
                piece,
                is_legal_move=is_legal,
                flip_frame=flip_frame if is_flipping else 0
            )
            row_cells.append(cell)

        table.add_row(*row_cells)

    return table


def display_board(board: Board, legal_moves: Optional[List[int]] = None,
                  title: str = "Othello") -> None:
    """Display the board with colors.

    Args:
        board: Current board state
        legal_moves: Optional list of legal moves to highlight
        title: Title to display above the board
    """
    console.clear()

    # Create board table
    table = create_board_table(board, legal_moves)

    # Wrap in a panel
    panel = Panel(
        table,
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print(panel)


def animate_flip(board_before: Board, board_after: Board, flipped_squares: Set[int],
                 legal_moves: Optional[List[int]] = None, frames: int = 4,
                 frame_delay: float = 0.15) -> None:
    """Animate pieces flipping from one color to another.

    Args:
        board_before: Board state before the move
        board_after: Board state after the move
        flipped_squares: Set of squares that flipped
        legal_moves: Optional list of legal moves to highlight
        frames: Number of animation frames
        frame_delay: Delay between frames in seconds
    """
    with Live(console=console, refresh_per_second=10) as live:
        # Show flipping animation
        for frame in range(1, frames + 1):
            table = create_board_table(board_before, legal_moves, flipped_squares, frame)
            panel = Panel(
                table,
                title="[bold cyan]Othello[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            live.update(panel)
            time.sleep(frame_delay)

        # Show final state
        table = create_board_table(board_after, legal_moves)
        panel = Panel(
            table,
            title="[bold cyan]Othello[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        live.update(panel)
        time.sleep(0.1)


def display_score(board: Board) -> None:
    """Display the current score with colors.

    Args:
        board: Current board state
    """
    black_count = bin(board.black_pieces).count('1')
    white_count = bin(board.white_pieces).count('1')

    score_text = Text()
    score_text.append("Score: ", style="bold")
    score_text.append(f"Black {black_count}", style=BLACK_PIECE_STYLE)
    score_text.append(" - ", style="bold")
    score_text.append(f"White {white_count}", style=WHITE_PIECE_STYLE)

    console.print(score_text)


def display_evaluation(status: str, bot_win_pct: float) -> None:
    """Display position evaluation with colors.

    Args:
        status: Status message about who's ahead
        bot_win_pct: Bot's win probability percentage
    """
    eval_text = Text()
    eval_text.append("Evaluation: ", style="bold")

    if "Bot ahead" in status:
        eval_text.append(status, style="bold red")
    elif "You are ahead" in status:
        eval_text.append(status, style="bold green")
    else:
        eval_text.append(status, style="bold yellow")

    eval_text.append(f" (bot win chance {bot_win_pct:.0f}%)", style="dim")
    console.print(eval_text)


def display_message(message: str, style: str = "bold") -> None:
    """Display a message with optional styling.

    Args:
        message: Message to display
        style: Rich style string
    """
    console.print(message, style=style)


def display_legal_moves(moves: List[int], square_to_notation) -> None:
    """Display legal moves in a colored format.

    Args:
        moves: List of legal move squares
        square_to_notation: Function to convert square to notation
    """
    if moves:
        move_text = Text()
        move_text.append("Legal moves: ", style="bold yellow")
        move_text.append(", ".join(square_to_notation(m) for m in moves), style="yellow")
        console.print(move_text)


def get_input(prompt: str) -> str:
    """Get user input with colored prompt.

    Args:
        prompt: Prompt message

    Returns:
        User input string
    """
    console.print(f"[bold cyan]{prompt}[/bold cyan]", end=" ")
    return input()


def display_game_over(board: Board, winner: Optional[str]) -> None:
    """Display game over screen with final results.

    Args:
        board: Final board state
        winner: Winner ('black', 'white', or None for tie)
    """
    console.clear()

    # Display final board
    table = create_board_table(board)
    panel = Panel(
        table,
        title="[bold red]Game Over[/bold red]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(panel)

    # Display final score
    black_count = bin(board.black_pieces).count('1')
    white_count = bin(board.white_pieces).count('1')

    console.print()
    result_text = Text()
    result_text.append("Final Score: ", style="bold")
    result_text.append(f"Black {black_count}", style=BLACK_PIECE_STYLE)
    result_text.append(" - ", style="bold")
    result_text.append(f"White {white_count}", style=WHITE_PIECE_STYLE)
    console.print(result_text)

    console.print()
    if winner == 'black':
        console.print("🎉 You win! 🎉", style="bold green", justify="center")
    elif winner == 'white':
        console.print("🤖 Bot wins! 🤖", style="bold red", justify="center")
    else:
        console.print("🤝 It's a tie! 🤝", style="bold yellow", justify="center")
