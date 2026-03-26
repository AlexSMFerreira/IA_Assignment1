from __future__ import annotations

import importlib
from typing import Any

from .agents import MinimaxAgent
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
    def __init__(
        self,
        *,
        mode: str = "human-vs-human",
        ai_color: str = "black",
        ai_depth: int = 2,
    ) -> None:
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
        self.menu_active = True
        self.selected_mode = mode
        self.selected_ai_color = ai_color
        self.selected_ai_depth = ai_depth
        self.ai_by_color: dict[str, MinimaxAgent] = {}
        self.ai_think_limit_ms = 1200
        self.ai_think_started_at_ms: int | None = None
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

    def _initialize_agents_from_selection(self) -> None:
        self.ai_by_color = {}
        if self.selected_mode == "human-vs-ai":
            self.ai_by_color[self.selected_ai_color] = MinimaxAgent(
                color=self.selected_ai_color,
                depth=self.selected_ai_depth,
                max_think_ms=self.ai_think_limit_ms,
            )
        elif self.selected_mode == "ai-vs-ai":
            self.ai_by_color["white"] = MinimaxAgent(
                color="white",
                depth=self.selected_ai_depth,
                max_think_ms=self.ai_think_limit_ms,
            )
            self.ai_by_color["black"] = MinimaxAgent(
                color="black",
                depth=self.selected_ai_depth,
                max_think_ms=self.ai_think_limit_ms,
            )

    def _menu_rects(self) -> dict[str, Any]:
        center_x = WINDOW_WIDTH // 2
        box_w = 280
        box_h = 46
        left_x = center_x - box_w // 2
        top = 170
        gap = 14

        mode_hvh = pygame.Rect(left_x, top, box_w, box_h)
        mode_hva = pygame.Rect(left_x, top + (box_h + gap), box_w, box_h)
        mode_ava = pygame.Rect(left_x, top + 2 * (box_h + gap), box_w, box_h)

        ai_color_white = pygame.Rect(left_x, top + 3 * (box_h + gap) + 26, 134, 42)
        ai_color_black = pygame.Rect(left_x + 146, top + 3 * (box_h + gap) + 26, 134, 42)

        depth_minus = pygame.Rect(left_x, top + 4 * (box_h + gap) + 46, 64, 42)
        depth_plus = pygame.Rect(left_x + box_w - 64, top + 4 * (box_h + gap) + 46, 64, 42)

        start_button = pygame.Rect(left_x, top + 5 * (box_h + gap) + 76, box_w, 54)
        return {
            "mode_hvh": mode_hvh,
            "mode_hva": mode_hva,
            "mode_ava": mode_ava,
            "ai_color_white": ai_color_white,
            "ai_color_black": ai_color_black,
            "depth_minus": depth_minus,
            "depth_plus": depth_plus,
            "start_button": start_button,
        }

    def _draw_button(self, rect: Any, text: str, *, selected: bool = False) -> None:
        fill = (78, 118, 86) if selected else (57, 66, 82)
        border = (195, 220, 200) if selected else (140, 150, 168)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)
        text_surface = self.small_font.render(text, True, (239, 243, 250))
        self.screen.blit(
            text_surface,
            (
                rect.x + (rect.width - text_surface.get_width()) // 2,
                rect.y + (rect.height - text_surface.get_height()) // 2,
            ),
        )

    def _draw_start_menu(self) -> None:
        self.screen.fill((37, 43, 56))
        title = self.font.render("ANGULUS - Choose Mode", True, (242, 246, 255))
        self.screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 70))

        rects = self._menu_rects()
        self._draw_button(rects["mode_hvh"], "Human vs Human", selected=self.selected_mode == "human-vs-human")
        self._draw_button(rects["mode_hva"], "Human vs AI", selected=self.selected_mode == "human-vs-ai")
        self._draw_button(rects["mode_ava"], "AI vs AI", selected=self.selected_mode == "ai-vs-ai")

        ai_label = self.tiny_font.render("AI color (Human vs AI only)", True, (180, 191, 210))
        self.screen.blit(ai_label, (rects["ai_color_white"].x, rects["ai_color_white"].y - 20))
        self._draw_button(
            rects["ai_color_white"],
            "White",
            selected=self.selected_ai_color == "white",
        )
        self._draw_button(
            rects["ai_color_black"],
            "Black",
            selected=self.selected_ai_color == "black",
        )

        depth_label = self.tiny_font.render("AI depth", True, (180, 191, 210))
        self.screen.blit(depth_label, (rects["depth_minus"].x, rects["depth_minus"].y - 22))
        self._draw_button(rects["depth_minus"], "-")
        self._draw_button(rects["depth_plus"], "+")
        depth_value = self.small_font.render(str(self.selected_ai_depth), True, (240, 244, 250))
        depth_center_x = (rects["depth_minus"].right + rects["depth_plus"].left) // 2
        self.screen.blit(
            depth_value,
            (depth_center_x - depth_value.get_width() // 2, rects["depth_minus"].y + 9),
        )

        self._draw_button(rects["start_button"], "Start Game", selected=True)

    def _handle_menu_click(self, event: Any) -> None:
        mx, my = event.pos
        rects = self._menu_rects()

        if rects["mode_hvh"].collidepoint(mx, my):
            self.selected_mode = "human-vs-human"
            return
        if rects["mode_hva"].collidepoint(mx, my):
            self.selected_mode = "human-vs-ai"
            return
        if rects["mode_ava"].collidepoint(mx, my):
            self.selected_mode = "ai-vs-ai"
            return

        if rects["ai_color_white"].collidepoint(mx, my):
            self.selected_ai_color = "white"
            return
        if rects["ai_color_black"].collidepoint(mx, my):
            self.selected_ai_color = "black"
            return

        if rects["depth_minus"].collidepoint(mx, my):
            self.selected_ai_depth = max(1, self.selected_ai_depth - 1)
            return
        if rects["depth_plus"].collidepoint(mx, my):
            self.selected_ai_depth = min(6, self.selected_ai_depth + 1)
            return

        if rects["start_button"].collidepoint(mx, my):
            self.state = GameState()
            self.input_handler.clear_selection()
            self._initialize_agents_from_selection()
            self.menu_active = False

    def _is_human_turn(self) -> bool:
        return self.state.turn not in self.ai_by_color

    def _play_ai_turn_if_needed(self) -> None:
        if self.state.mode != "play":
            return

        ai_agent = self.ai_by_color.get(self.state.turn)
        if ai_agent is None:
            return

        selected_move = ai_agent.pick_move(self.state)
        self.input_handler.clear_selection()
        if selected_move is None:
            self.state.mode = "game_over"
            self.state.winner = "black" if self.state.turn == "white" else "white"
            self.state.status_message = f"{self.state.winner.capitalize()} wins (no legal moves)"
            return

        src, dst = selected_move
        self.state.apply_move(src, dst)

    def _schedule_ai_thinking_if_needed(self) -> None:
        if self.state.mode != "play":
            self.ai_think_started_at_ms = None
            return

        if self._is_human_turn():
            self.ai_think_started_at_ms = None
            return

        if self.ai_think_started_at_ms is None:
            self.ai_think_started_at_ms = pygame.time.get_ticks()
            self.state.status_message = f"{self.state.turn.capitalize()} AI thinking..."

    def _run_scheduled_ai_turn_if_ready(self) -> None:
        if self.ai_think_started_at_ms is None:
            return

        self._play_ai_turn_if_needed()
        self.ai_think_started_at_ms = None

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.menu_active:
                    self._handle_menu_click(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and self._is_human_turn():
                    self.input_handler.handle_mouse(event, self.state)

            if self.menu_active:
                self._draw_start_menu()
            else:
                self._schedule_ai_thinking_if_needed()
                self.renderer.draw(
                    state=self.state,
                    selected_cell=self.input_handler.selected_cell,
                    legal_moves=self.input_handler.legal_moves,
                )
            pygame.display.flip()

            if not self.menu_active:
                self._run_scheduled_ai_turn_if_ready()

        pygame.quit()
