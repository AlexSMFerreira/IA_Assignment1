# Angulus (Pygame)

## Rules Implemented

- Board size: 9 columns x 8 rows.
- Goal: capture the opponent king.
- Each turn: move one piece.
- Pawn:
	- Moves exactly 1 square in any direction.
	- Captures only diagonally (1 square).
- Piece:
	- Moves and captures from 1 to 2 squares in any direction.
- King:
	- Moves and captures from 1 to 3 squares in any direction.
- Sliding pieces (piece/king) cannot jump over other pieces.

## Setup

Create and use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the game:

```bash
python main.py
```

## Controls

- Play mode:
	- Click one of your pieces to select it.
	- Click a highlighted square to move/capture.

## Set Initial Positions In Code

In `main.py`, edit the `INITIAL_LAYOUT` constant.

- 8 strings (rows), each with 9 characters (columns)
- Symbols:
	- `P` white pawn
	- `A` white piece
	- `K` white king
	- `p` black pawn
	- `a` black piece
	- `k` black king
	- `.` empty square

