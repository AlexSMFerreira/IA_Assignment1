from __future__ import annotations

import importlib
import random
from typing import Any, Union

from .agents import MinimaxAgent, RandomAgent
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

AgentType = Union[MinimaxAgent, RandomAgent]

class AngulusGame:
    def __init__(
        self,
        *,
        mode: str = "human-vs-human",
        ai_color: str = "black",
        ai_depth: int = 1,
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
        self.white_depth = ai_depth
        self.black_depth = ai_depth
        
        self.ai_by_color: dict[str, AgentType] = {}
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
            piece_surface = pygame.image.load(str(image_path)).convert_alpha()
            width, height = piece_surface.get_size()
            scaled_size = (max(1, int(width * PIECE_SCALE)), max(1, int(height * PIECE_SCALE)))
            piece_surface = pygame.transform.smoothscale(piece_surface, scaled_size)
            images[key] = piece_surface
        return images

    def _initialize_agents_from_selection(self) -> None:
        self.ai_by_color = {}
        
        def create_agent(color: str, depth_level: int) -> AgentType:
            if depth_level == 1:
                return RandomAgent(rng=random.Random())
            elif depth_level == 2:
                return MinimaxAgent(color=color, depth=1, max_think_ms=self.ai_think_limit_ms)
            else:
                return MinimaxAgent(color=color, depth=2, max_think_ms=self.ai_think_limit_ms)

        if self.selected_mode == "human-vs-ai":
            self.ai_by_color[self.selected_ai_color] = create_agent(self.selected_ai_color, self.white_depth)
        elif self.selected_mode == "ai-vs-ai":
            self.ai_by_color["white"] = create_agent("white", self.white_depth)
            self.ai_by_color["black"] = create_agent("black", self.black_depth)

    def _menu_rects(self) -> dict[str, Any]:
        center_x = WINDOW_WIDTH // 2
        box_w = 280
        box_h = 46
        left_x = center_x - box_w // 2
        top = 150
        gap = 12

        rects = {
            "mode_hvh": pygame.Rect(left_x, top, box_w, box_h),
            "mode_hva": pygame.Rect(left_x, top + (box_h + gap), box_w, box_h),
            "mode_ava": pygame.Rect(left_x, top + 2 * (box_h + gap), box_w, box_h),
        }

        rects["hva_white"] = pygame.Rect(left_x, top + 3 * (box_h + gap) + 20, 134, 40)
        rects["hva_black"] = pygame.Rect(left_x + 146, top + 3 * (box_h + gap) + 20, 134, 40)
        rects["hva_minus"] = pygame.Rect(left_x, top + 4 * (box_h + gap) + 35, 60, 40)
        rects["hva_plus"] = pygame.Rect(left_x + box_w - 60, top + 4 * (box_h + gap) + 35, 60, 40)

        rects["ava_w_minus"] = pygame.Rect(left_x, top + 3 * (box_h + gap) + 30, 50, 35)
        rects["ava_w_plus"] = pygame.Rect(left_x + 80, top + 3 * (box_h + gap) + 30, 50, 35)
        rects["ava_b_minus"] = pygame.Rect(left_x + 150, top + 3 * (box_h + gap) + 30, 50, 35)
        rects["ava_b_plus"] = pygame.Rect(left_x + 230, top + 3 * (box_h + gap) + 30, 50, 35)

        rects["start_button"] = pygame.Rect(left_x, WINDOW_HEIGHT - 80, box_w, 54)
        return rects

    def _draw_button(self, rect: Any, text: str, *, selected: bool = False, small: bool = False) -> None:
        fill = (78, 118, 86) if selected else (57, 66, 82)
        border = (195, 220, 200) if selected else (140, 150, 168)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)
        font = self.tiny_font if small else self.small_font
        text_surface = font.render(text, True, (239, 243, 250))
        self.screen.blit(text_surface, (rect.x + (rect.width - text_surface.get_width()) // 2, rect.y + (rect.height - text_surface.get_height()) // 2))

    def _draw_start_menu(self) -> None:
        self.screen.fill((37, 43, 56))
        title = self.font.render("ANGULUS - Strategic Setup", True, (242, 246, 255))
        self.screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 50))
        rects = self._menu_rects()
        diff_map = {1: "Easy", 2: "Med", 3: "Hard"}

        self._draw_button(rects["mode_hvh"], "Human vs Human", selected=self.selected_mode == "human-vs-human")
        self._draw_button(rects["mode_hva"], "Human vs AI", selected=self.selected_mode == "human-vs-ai")
        self._draw_button(rects["mode_ava"], "AI vs AI", selected=self.selected_mode == "ai-vs-ai")

        if self.selected_mode == "human-vs-ai":
            self.screen.blit(self.tiny_font.render("AI Side", True, (180, 191, 210)), (rects["hva_white"].x, rects["hva_white"].y - 18))
            self._draw_button(rects["hva_white"], "White", selected=self.selected_ai_color == "white")
            self._draw_button(rects["hva_black"], "Black", selected=self.selected_ai_color == "black")
            
            self.screen.blit(self.tiny_font.render("Difficulty", True, (180, 191, 210)), (rects["hva_minus"].x, rects["hva_minus"].y - 18))
            self._draw_button(rects["hva_minus"], "-")
            self._draw_button(rects["hva_plus"], "+")
            depth_text = f"{self.white_depth}: {diff_map[self.white_depth]}"
            self.screen.blit(self.small_font.render(depth_text, True, (240, 244, 250)), (rects["hva_minus"].right + 15, rects["hva_minus"].y + 8))

        elif self.selected_mode == "ai-vs-ai":
            # Controles para White AI
            self.screen.blit(self.tiny_font.render("White AI Level", True, (180, 191, 210)), (rects["ava_w_minus"].x, rects["ava_w_minus"].y - 18))
            self._draw_button(rects["ava_w_minus"], "-", small=True)
            self._draw_button(rects["ava_w_plus"], "+", small=True)
            self.screen.blit(self.small_font.render(diff_map[self.white_depth], True, (240, 244, 250)), (rects["ava_w_minus"].x + 10, rects["ava_w_minus"].bottom + 5))

            # Controles para Black AI
            self.screen.blit(self.tiny_font.render("Black AI Level", True, (180, 191, 210)), (rects["ava_b_minus"].x, rects["ava_b_minus"].y - 18))
            self._draw_button(rects["ava_b_minus"], "-", small=True)
            self._draw_button(rects["ava_b_plus"], "+", small=True)
            self.screen.blit(self.small_font.render(diff_map[self.black_depth], True, (240, 244, 250)), (rects["ava_b_minus"].x + 10, rects["ava_b_minus"].bottom + 5))

        self._draw_button(rects["start_button"], "Launch Battle", selected=True)

    def _handle_menu_click(self, event: Any) -> None:
        mx, my = event.pos
        rects = self._menu_rects()

        if rects["mode_hvh"].collidepoint(mx, my): self.selected_mode = "human-vs-human"
        elif rects["mode_hva"].collidepoint(mx, my): self.selected_mode = "human-vs-ai"
        elif rects["mode_ava"].collidepoint(mx, my): self.selected_mode = "ai-vs-ai"

        if self.selected_mode == "human-vs-ai":
            if rects["hva_white"].collidepoint(mx, my): self.selected_ai_color = "white"
            elif rects["hva_black"].collidepoint(mx, my): self.selected_ai_color = "black"
            elif rects["hva_minus"].collidepoint(mx, my): self.white_depth = max(1, self.white_depth - 1)
            elif rects["hva_plus"].collidepoint(mx, my): self.white_depth = min(3, self.white_depth + 1)
        
        elif self.selected_mode == "ai-vs-ai":
            if rects["ava_w_minus"].collidepoint(mx, my): self.white_depth = max(1, self.white_depth - 1)
            elif rects["ava_w_plus"].collidepoint(mx, my): self.white_depth = min(3, self.white_depth + 1)
            elif rects["ava_b_minus"].collidepoint(mx, my): self.black_depth = max(1, self.black_depth - 1)
            elif rects["ava_b_plus"].collidepoint(mx, my): self.black_depth = min(3, self.black_depth + 1)

        if rects["start_button"].collidepoint(mx, my):
            self.state = GameState()
            self._initialize_agents_from_selection()
            self.menu_active = False

    def _is_human_turn(self) -> bool:
        return self.state.turn not in self.ai_by_color

    def _play_ai_turn_if_needed(self) -> None:
        if self.state.mode != "play": return
        ai_agent = self.ai_by_color.get(self.state.turn)
        if ai_agent:
            move = ai_agent.pick_move(self.state)
            if move: self.state.apply_move(*move)
            else: self.state.mode = "game_over"; self.state.winner = "black" if self.state.turn == "white" else "white"

    def _run_scheduled_ai_turn_if_ready(self) -> None:
        if self.ai_think_started_at_ms and pygame.time.get_ticks() - self.ai_think_started_at_ms > 500:
            self._play_ai_turn_if_needed()
            self.ai_think_started_at_ms = None

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.menu_active: self._handle_menu_click(event)
                    elif self._is_human_turn(): self.input_handler.handle_mouse(event, self.state)
            if self.menu_active: self._draw_start_menu()
            else:
                if not self._is_human_turn() and self.ai_think_started_at_ms is None:
                    self.ai_think_started_at_ms = pygame.time.get_ticks()
                self.renderer.draw(self.state, self.input_handler.selected_cell, self.input_handler.legal_moves)
                self._run_scheduled_ai_turn_if_ready()
            pygame.display.flip()
        pygame.quit()


