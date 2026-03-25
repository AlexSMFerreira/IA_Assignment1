from __future__ import annotations

import importlib
from typing import Any

from .constants import (
    FPS,
    PIECES_DIR,
    PIECE_IMAGE_FILES,
    PIECE_SCALE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .input_handler import InputHandler
from .renderer import Renderer
from .rules import GameState

pygame: Any = importlib.import_module("pygame")


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

        self.state = GameState()
        self.input_handler = InputHandler()
        self.renderer = Renderer(
            pygame_module=pygame,
            screen=self.screen,
            font=self.font,
            small_font=self.small_font,
            tiny_font=self.tiny_font,
            piece_images=self.piece_images,
        )

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
                    self.input_handler.handle_mouse(event, self.state)

            self.renderer.draw(
                state=self.state,
                selected_cell=self.input_handler.selected_cell,
                legal_moves=self.input_handler.legal_moves,
            )
            pygame.display.flip()

        pygame.quit()
