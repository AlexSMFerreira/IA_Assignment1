from __future__ import annotations

from typing import List, Optional, Tuple

from .constants import BOARD_COLS, BOARD_ROWS, DIRECTIONS, INITIAL_LAYOUT
from .models import Piece


class GameState:
    def __init__(self, layout: Optional[List[str]] = None) -> None:
        source_layout = layout if layout is not None else INITIAL_LAYOUT
        self.board: List[List[Optional[Piece]]] = self._board_from_layout(source_layout)
        self.mode = "play"
        self.turn = "white"
        self.winner: Optional[str] = None
        self.status_message = "White to move"
        self._validate_initial_board()

    def apply_move(self, src: Tuple[int, int], dst: Tuple[int, int]) -> None:
        sr, sc = src
        dr, dc = dst
        moving_piece = self.board[sr][sc]
        target = self.board[dr][dc]

        if moving_piece is None:
            return

        self.board[dr][dc] = moving_piece
        self.board[sr][sc] = None

        if target is not None and target.kind == "king":
            self.winner = moving_piece.color
            self.mode = "game_over"
            self.status_message = f"{self.winner.capitalize()} captured the king and wins"
            return

        self.turn = "black" if self.turn == "white" else "white"
        self.status_message = f"{self.turn.capitalize()} to move"

    def get_legal_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        piece = self.board[row][col]
        if piece is None:
            return []

        if piece.kind == "pawn":
            return self.get_pawn_moves(row, col, piece.color)

        max_steps = 2 if piece.kind == "piece" else 3
        moves: List[Tuple[int, int]] = []

        for dr, dc in DIRECTIONS:
            for step in range(1, max_steps + 1):
                nr = row + dr * step
                nc = col + dc * step
                if not self.in_bounds(nr, nc):
                    break

                target = self.board[nr][nc]
                if target is None:
                    moves.append((nr, nc))
                    continue

                if target.color != piece.color:
                    moves.append((nr, nc))
                break

        return moves

    def get_pawn_moves(self, row: int, col: int, color: str) -> List[Tuple[int, int]]:
        moves: List[Tuple[int, int]] = []

        for dr, dc in DIRECTIONS:
            nr = row + dr
            nc = col + dc
            if not self.in_bounds(nr, nc):
                continue

            target = self.board[nr][nc]
            is_diagonal = abs(dr) == 1 and abs(dc) == 1

            if is_diagonal:
                if target is not None and target.color != color:
                    moves.append((nr, nc))
            else:
                if target is None:
                    moves.append((nr, nc))

        return moves

    @staticmethod
    def in_bounds(row: int, col: int) -> bool:
        return 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS

    def _board_from_layout(self, layout: List[str]) -> List[List[Optional[Piece]]]:
        if len(layout) != BOARD_ROWS:
            raise ValueError(f"INITIAL_LAYOUT must have {BOARD_ROWS} rows")

        mapping: dict[str, Optional[Piece]] = {
            "P": Piece("white", "pawn"),
            "A": Piece("white", "piece"),
            "K": Piece("white", "king"),
            "p": Piece("black", "pawn"),
            "a": Piece("black", "piece"),
            "k": Piece("black", "king"),
            ".": None,
        }

        board: List[List[Optional[Piece]]] = []
        for text_row in layout:
            if len(text_row) != BOARD_COLS:
                raise ValueError(f"Each INITIAL_LAYOUT row must have {BOARD_COLS} columns")
            row: List[Optional[Piece]] = []
            for ch in text_row:
                if ch not in mapping:
                    raise ValueError(f"Invalid layout character: {ch}")
                template = mapping[ch]
                if template is None:
                    row.append(None)
                else:
                    row.append(Piece(template.color, template.kind))
            board.append(row)
        return board

    def _validate_initial_board(self) -> None:
        white_kings = self.count_kind("white", "king")
        black_kings = self.count_kind("black", "king")
        if white_kings != 1 or black_kings != 1:
            raise ValueError("INITIAL_LAYOUT must contain exactly one white king and one black king")

        white_total = self.count_color("white")
        black_total = self.count_color("black")
        if white_total == 0 or black_total == 0:
            raise ValueError("INITIAL_LAYOUT must contain at least one piece for each side")

    def count_kind(self, color: str, kind: str) -> int:
        total = 0
        for row in self.board:
            for cell in row:
                if cell is not None and cell.color == color and cell.kind == kind:
                    total += 1
        return total

    def count_color(self, color: str) -> int:
        total = 0
        for row in self.board:
            for cell in row:
                if cell is not None and cell.color == color:
                    total += 1
        return total
