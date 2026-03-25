from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple, cast

pygame: Any = importlib.import_module("pygame")

BOARD_COLS = 9
BOARD_ROWS = 8
SQUARE_SIZE = 80
BOARD_TOP_PADDING = 50
SIDEBAR_WIDTH = 340
WINDOW_WIDTH = BOARD_COLS * SQUARE_SIZE + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_TOP_PADDING + BOARD_ROWS * SQUARE_SIZE
FPS = 60

LIGHT_SQUARE = (240, 217, 181)  # chess.com light square
DARK_SQUARE = (181, 136, 99)  # chess.com dark square
SELECTED_OVERLAY = (90, 160, 255, 120)
MOVE_OVERLAY = (85, 170, 110, 130)
CAPTURE_OVERLAY = (210, 70, 70, 160)
PANEL_BG = (28, 32, 40)
PANEL_HEADER = (45, 52, 64)
TEXT_LIGHT = (236, 240, 247)
TEXT_DIM = (165, 173, 186)
BUTTON_BG = (58, 67, 82)
BUTTON_ACTIVE = (90, 160, 255)
BUTTON_DANGER = (175, 70, 72)

WHITE_FILL = (247, 247, 247)
WHITE_OUTLINE = (30, 32, 38)
BLACK_FILL = (37, 40, 46)
BLACK_OUTLINE = (222, 227, 236)

PIECES_STYLE = "3d_wood"
PIECES_DIR = Path("chess.com-boards-and-pieces-master") / "pieces" / PIECES_STYLE
PIECE_SCALE = 0.7
PIECE_IMAGE_FILES = {
    ("white", "pawn"): "wp.png",
    ("white", "piece"): "wb.png",
    ("white", "king"): "wk.png",
    ("black", "pawn"): "bp.png",
    ("black", "piece"): "bb.png",
    ("black", "king"): "bk.png",
}
PIECE_VERTICAL_OFFSETS = {
    "pawn": 0,
    "piece": -12,
    "king": -18,
}

DIRECTIONS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]

# Edit this layout in code to change starting positions.
# Symbols: P/A/K = white pawn/piece/king, p/a/k = black pawn/piece/king, . = empty
INITIAL_LAYOUT = [
    "p.p.k.p.p",
    ".a.a.a.a.",
    "p.p.p.p.p",
    ".........",
    ".........",
    "P.P.P.P.P",
    ".A.A.A.A.",
    "P.P.K.P.P",
]


@dataclass
class Piece:
    color: str  # "white" or "black"
    kind: str  # "pawn", "piece", "king"


class AngulusGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Angulus (Pygame)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("dejavuserif", 22)
        self.small_font = pygame.font.SysFont("dejavuserif", 18)
        self.tiny_font = pygame.font.SysFont("dejavuserif", 15)
        self.piece_images: dict[tuple[str, str], Any] = self._load_piece_images()

        self.board: List[List[Optional[Piece]]] = self._board_from_layout(INITIAL_LAYOUT)
        self.mode = "play"  # play | game_over
        self.turn = "white"
        self.winner: Optional[str] = None

        self.selected_cell: Optional[Tuple[int, int]] = None
        self.legal_moves: List[Tuple[int, int]] = []
        self.status_message = "White to move"
        self._validate_initial_board()

    def _load_piece_images(self) -> dict[tuple[str, str], Any]:
        if not PIECES_DIR.exists():
            raise FileNotFoundError(f"Pieces directory not found: {PIECES_DIR}")

        images: dict[tuple[str, str], Any] = {}
        for key, filename in PIECE_IMAGE_FILES.items():
            image_path = PIECES_DIR / filename
            if not image_path.exists():
                raise FileNotFoundError(f"Piece image not found: {image_path}")

            piece_surface = pygame.image.load(str(image_path)).convert_alpha()
            width, height = piece_surface.get_size()
            scaled_size = (max(1, int(width * PIECE_SCALE)), max(1, int(height * PIECE_SCALE)))
            piece_surface = pygame.transform.smoothscale(piece_surface, scaled_size)
            images[key] = piece_surface

        return images

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event)

            self.draw()
            pygame.display.flip()

        pygame.quit()

    def handle_mouse(self, event: Any) -> None:
        mx, my = cast(tuple[int, int], event.pos)

        board_bottom = BOARD_TOP_PADDING + BOARD_ROWS * SQUARE_SIZE
        if mx < BOARD_COLS * SQUARE_SIZE and BOARD_TOP_PADDING <= my < board_bottom:
            row = (my - BOARD_TOP_PADDING) // SQUARE_SIZE
            col = mx // SQUARE_SIZE
            if self.mode == "play":
                self.handle_play_click(row, col)
            return

    def handle_play_click(self, row: int, col: int) -> None:
        if self.selected_cell is not None:
            if self.selected_cell == (row, col):
                self.selected_cell = None
                self.legal_moves = []
                return
            if (row, col) in self.legal_moves:
                self.apply_move(self.selected_cell, (row, col))
                return

        piece = self.board[row][col]
        if piece is not None and piece.color == self.turn:
            self.selected_cell = (row, col)
            self.legal_moves = self.get_legal_moves(row, col)
        else:
            self.selected_cell = None
            self.legal_moves = []

    def apply_move(self, src: Tuple[int, int], dst: Tuple[int, int]) -> None:
        sr, sc = src
        dr, dc = dst
        moving_piece = self.board[sr][sc]
        target = self.board[dr][dc]

        if moving_piece is None:
            self.selected_cell = None
            self.legal_moves = []
            return

        self.board[dr][dc] = moving_piece
        self.board[sr][sc] = None
        self.selected_cell = None
        self.legal_moves = []

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

    def draw(self) -> None:
        self.screen.fill((45, 52, 64))
        self.draw_board()
        self.draw_sidebar()

    def draw_board(self) -> None:
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                rect = pygame.Rect(
                    col * SQUARE_SIZE,
                    BOARD_TOP_PADDING + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                )
                pygame.draw.rect(self.screen, color, rect)

                if self.selected_cell == (row, col):
                    overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    overlay.fill(SELECTED_OVERLAY)
                    self.screen.blit(overlay, rect.topleft)
                elif (row, col) in self.legal_moves:
                    overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    target = self.board[row][col]
                    overlay.fill(CAPTURE_OVERLAY if target is not None else MOVE_OVERLAY)
                    self.screen.blit(overlay, rect.topleft)

        for i in range(BOARD_COLS + 1):
            x = i * SQUARE_SIZE
            pygame.draw.line(
                self.screen,
                (0, 0, 0),
                (x, BOARD_TOP_PADDING),
                (x, BOARD_TOP_PADDING + BOARD_ROWS * SQUARE_SIZE),
                1,
            )
        for i in range(BOARD_ROWS + 1):
            y = BOARD_TOP_PADDING + i * SQUARE_SIZE
            pygame.draw.line(self.screen, (0, 0, 0), (0, y), (BOARD_COLS * SQUARE_SIZE, y), 1)

        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.board[row][col]
                if piece is None:
                    continue
                rect = pygame.Rect(
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

    def draw_sidebar(self) -> None:
        panel_rect = pygame.Rect(BOARD_COLS * SQUARE_SIZE, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)

        header = pygame.Rect(panel_rect.x, 0, panel_rect.width, 90)
        pygame.draw.rect(self.screen, PANEL_HEADER, header)

        title = self.font.render("ANGULUS", True, TEXT_LIGHT)
        subtitle = self.tiny_font.render("9x8 Strategic Board Game", True, TEXT_DIM)
        self.screen.blit(title, (header.x + 20, 18))
        self.screen.blit(subtitle, (header.x + 20, 52))

        mode_text = f"Mode: {self.mode.replace('_', ' ').title()}"
        turn_text = f"Turn: {self.turn.title()}"
        self.screen.blit(self.small_font.render(mode_text, True, TEXT_LIGHT), (header.x + 20, 96))
        self.screen.blit(self.small_font.render(turn_text, True, TEXT_LIGHT), (header.x + 20, 118))

        status_lines = [
            "Left click board: select/move",
            self.status_message,
        ]

        y = WINDOW_HEIGHT - 120
        for line in status_lines:
            color = TEXT_DIM if line != self.status_message else TEXT_LIGHT
            surface = self.tiny_font.render(line, True, color)
            self.screen.blit(surface, (panel_rect.x + 20, y))
            y += 22

if __name__ == "__main__":
    AngulusGame().run()
