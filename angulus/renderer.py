from __future__ import annotations

from typing import Any, Optional, Tuple

from .constants import (
    BOARD_COLS,
    BOARD_ROWS,
    BOARD_TOP_PADDING,
    CAPTURE_OVERLAY,
    DARK_SQUARE,
    LIGHT_SQUARE,
    MOVE_OVERLAY,
    PANEL_BG,
    PANEL_HEADER,
    PIECE_VERTICAL_OFFSETS,
    SELECTED_OVERLAY,
    SIDEBAR_WIDTH,
    SQUARE_SIZE,
    TEXT_DIM,
    TEXT_LIGHT,
    WINDOW_HEIGHT,
)
from .models import Piece
from .rules import GameState


class Renderer:
    def __init__(
        self,
        pygame_module: Any,
        screen: Any,
        font: Any,
        small_font: Any,
        tiny_font: Any,
        piece_images: dict[tuple[str, str], Any],
    ) -> None:
        self.pygame = pygame_module
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.tiny_font = tiny_font
        self.piece_images = piece_images

    def draw(
        self,
        state: GameState,
        selected_cell: Optional[Tuple[int, int]],
        legal_moves: list[Tuple[int, int]],
    ) -> None:
        self.screen.fill((45, 52, 64))
        self.draw_board(state, selected_cell, legal_moves)
        self.draw_sidebar(state)

    def draw_board(
        self,
        state: GameState,
        selected_cell: Optional[Tuple[int, int]],
        legal_moves: list[Tuple[int, int]],
    ) -> None:
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                rect = self.pygame.Rect(
                    col * SQUARE_SIZE,
                    BOARD_TOP_PADDING + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                )
                self.pygame.draw.rect(self.screen, color, rect)

                if selected_cell == (row, col):
                    overlay = self.pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), self.pygame.SRCALPHA)
                    overlay.fill(SELECTED_OVERLAY)
                    self.screen.blit(overlay, rect.topleft)
                elif (row, col) in legal_moves:
                    overlay = self.pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), self.pygame.SRCALPHA)
                    target = state.board[row][col]
                    overlay.fill(CAPTURE_OVERLAY if target is not None else MOVE_OVERLAY)
                    self.screen.blit(overlay, rect.topleft)

        for i in range(BOARD_COLS + 1):
            x = i * SQUARE_SIZE
            self.pygame.draw.line(
                self.screen,
                (0, 0, 0),
                (x, BOARD_TOP_PADDING),
                (x, BOARD_TOP_PADDING + BOARD_ROWS * SQUARE_SIZE),
                1,
            )
        for i in range(BOARD_ROWS + 1):
            y = BOARD_TOP_PADDING + i * SQUARE_SIZE
            self.pygame.draw.line(self.screen, (0, 0, 0), (0, y), (BOARD_COLS * SQUARE_SIZE, y), 1)

        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = state.board[row][col]
                if piece is None:
                    continue
                rect = self.pygame.Rect(
                    col * SQUARE_SIZE,
                    BOARD_TOP_PADDING + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                )
                self.draw_piece(piece, rect)

    def draw_piece(self, piece: Piece, rect: Any) -> None:
        piece_surface = self.piece_images[(piece.color, piece.kind)]
        destination = piece_surface.get_rect(center=rect.center)
        destination.y += PIECE_VERTICAL_OFFSETS[piece.kind]
        self.screen.blit(piece_surface, destination)

    def draw_sidebar(self, state: GameState) -> None:
        panel_rect = self.pygame.Rect(BOARD_COLS * SQUARE_SIZE, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        self.pygame.draw.rect(self.screen, PANEL_BG, panel_rect)

        header = self.pygame.Rect(panel_rect.x, 0, panel_rect.width, 90)
        self.pygame.draw.rect(self.screen, PANEL_HEADER, header)

        title = self.font.render("ANGULUS", True, TEXT_LIGHT)
        subtitle = self.tiny_font.render("9x8 Strategic Board Game", True, TEXT_DIM)
        self.screen.blit(title, (header.x + 20, 18))
        self.screen.blit(subtitle, (header.x + 20, 52))

        mode_text = f"Mode: {state.mode.replace('_', ' ').title()}"
        turn_text = f"Turn: {state.turn.title()}"
        self.screen.blit(self.small_font.render(mode_text, True, TEXT_LIGHT), (header.x + 20, 96))
        self.screen.blit(self.small_font.render(turn_text, True, TEXT_LIGHT), (header.x + 20, 118))

        status_lines = [
            "Left click board: select/move",
            state.status_message,
        ]

        y = WINDOW_HEIGHT - 120
        for line in status_lines:
            color = TEXT_DIM if line != state.status_message else TEXT_LIGHT
            surface = self.tiny_font.render(line, True, color)
            self.screen.blit(surface, (panel_rect.x + 20, y))
            y += 22
