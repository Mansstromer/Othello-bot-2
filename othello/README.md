# Othello Engine

A Python Othello (Reversi) engine optimized for iterative development and AI experimentation.

## Features

- **Bitboard representation**: Uses two 64-bit integers for fast move generation
- **Negamax search**: With alpha-beta pruning and move ordering
- **Iterative deepening**: Maximizes search depth within time constraints
- **Transposition tables**: Caches previously evaluated positions
- **CLI interface**: Play against the bot in your terminal

## Project Structure

```
othello/
├── src/
│   ├── board.py        # Bitboard representation + game rules
│   ├── evaluate.py     # Position evaluation
│   ├── search.py       # Negamax + alpha-beta
│   └── engine.py       # Public API
├── play.py             # CLI to play against the bot
├── tests/
│   └── test_board.py   # Correctness tests
└── README.md
```

## Usage

### Play Against the Bot

```bash
cd othello
python play.py
```

You play as Black, the bot plays as White. Enter moves in algebraic notation (e.g., `D3`, `C4`).

### Run Tests

```bash
cd othello
python tests/test_board.py
```

### Use as a Library

```python
from src.board import Board
from src.engine import OthelloEngine

# Create initial board
board = Board.initial()

# Create engine
engine = OthelloEngine()

# Get best move (with 5-second time limit)
move, score, depth = engine.get_best_move(board, time_limit_seconds=5.0)

print(f"Best move: {move}, Score: {score}, Depth: {depth}")
```

## Evaluation Function

The evaluation is based on several factors (all weights are tunable in `src/evaluate.py`):

1. **Mobility** (10 points per move): Number of legal moves available
2. **Corners** (100 points): Corner squares are stable and valuable
3. **X-squares** (-50 points): Squares adjacent to corners are risky
4. **Piece count** (1 point per piece): Raw piece advantage

### Tuning Weights

All evaluation weights are marked with `# TUNABLE` comments in `evaluate.py`. Adjust these to experiment with different playing styles:

```python
# TUNABLE: Evaluation weights
MOBILITY_WEIGHT = 10.0
CORNER_WEIGHT = 100.0
X_SQUARE_PENALTY = -50.0
PIECE_COUNT_WEIGHT = 1.0
```

## Implementation Details

### Board Representation

- 64-bit integers represent piece positions
- Bit N = 1 means a piece exists at square N
- Squares numbered 0-63 (row-major: 0 = A1, 7 = H1, 56 = A8, 63 = H8)

### Search Algorithm

- **Negamax**: Simplified minimax variant
- **Alpha-beta pruning**: Reduces search tree size
- **Move ordering**: Tries corners first, X-squares last
- **Iterative deepening**: Gradually increases depth until time limit

### Design Principles

- **Short functions**: Most functions under 30 lines for easy AI-assisted editing
- **Type hints**: Full type annotations throughout
- **Stateless operations**: Functions avoid side effects where possible
- **No external dependencies**: Uses only Python standard library

## Performance Tips

- Increase time limit in `engine.get_best_move()` for stronger play
- Adjust evaluation weights to emphasize different strategies
- Modify move ordering in `search.py` for better pruning
- Implement opening book for faster early game

## License

MIT License - Feel free to use and modify for your projects.
