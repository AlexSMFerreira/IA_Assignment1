from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Tuple

from .rules import GameState

Move = Tuple[Tuple[int, int], Tuple[int, int]]


def get_all_legal_moves(state: GameState) -> list[Move]:
    moves: list[Move] = []
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != state.turn:
                continue
            source = (row_index, col_index)
            for destination in state.get_legal_moves(row_index, col_index):
                moves.append((source, destination))
    return moves


@dataclass
class RandomAgent:
    rng: random.Random

    def pick_move(self, state: GameState) -> Optional[Move]:
        legal_moves = get_all_legal_moves(state)
        if not legal_moves:
            return None
        return self.rng.choice(legal_moves)


def run_random_game(*, rng: random.Random, max_plies: int = 500) -> str:
    state = GameState()
    white_agent = RandomAgent(rng)
    black_agent = RandomAgent(rng)

    for _ in range(max_plies):
        current_agent = white_agent if state.turn == "white" else black_agent
        selected_move = current_agent.pick_move(state)
        if selected_move is None:
            return "draw"

        src, dst = selected_move
        state.apply_move(src, dst)

        if state.mode == "game_over":
            return state.winner if state.winner is not None else "draw"

    return "draw"


def run_random_self_play(
    *,
    games: int = 100,
    seed: Optional[int] = None,
    max_plies: int = 500,
) -> dict[str, int]:
    rng = random.Random(seed)
    results = {"white": 0, "black": 0, "draw": 0}

    for _ in range(games):
        result = run_random_game(rng=rng, max_plies=max_plies)
        results[result] += 1

    return results