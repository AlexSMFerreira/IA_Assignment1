from __future__ import annotations

from typing import Any, List, Optional, Tuple, cast

from .constants import BOARD_COLS, BOARD_ROWS, BOARD_TOP_PADDING, SQUARE_SIZE
from .rules import GameState


class InputHandler:
    def __init__(self) -> None:
        self.selected_cell: Optional[Tuple[int, int]] = None
        self.legal_moves: List[Tuple[int, int]] = []

    def clear_selection(self) -> None:
        self.selected_cell = None
        self.legal_moves = []

    def handle_mouse(self, event: Any, state: GameState) -> None:
        mx, my = cast(tuple[int, int], event.pos)

        board_bottom = BOARD_TOP_PADDING + BOARD_ROWS * SQUARE_SIZE
        if mx < BOARD_COLS * SQUARE_SIZE and BOARD_TOP_PADDING <= my < board_bottom:
            row = (my - BOARD_TOP_PADDING) // SQUARE_SIZE
            col = mx // SQUARE_SIZE
            if state.mode == "play":
                self.handle_play_click(row, col, state)

    def handle_play_click(self, row: int, col: int, state: GameState) -> None:
        if self.selected_cell is not None:
            if self.selected_cell == (row, col):
                self.selected_cell = None
                self.legal_moves = []
                return
            if (row, col) in self.legal_moves:
                state.apply_move(self.selected_cell, (row, col))
                self.selected_cell = None
                self.legal_moves = []
                return

        piece = state.board[row][col]
        if piece is not None and piece.color == state.turn:
            self.selected_cell = (row, col)
            self.legal_moves = state.get_legal_moves(row, col)
        else:
            self.selected_cell = None
            self.legal_moves = []
