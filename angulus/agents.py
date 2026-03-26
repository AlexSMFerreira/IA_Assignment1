from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Tuple
from copy import deepcopy
from .rules import GameState

Move = Tuple[Tuple[int, int], Tuple[int, int]]

PIECE_VALUES = {
    "pawn": 1,
    "piece": 3,
    "king": 1000,
}

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

@dataclass
class MinimaxAgent:
    color: str
    depth: int = 2
    max_nodes: int = 25000
    
    def pick_move(self, state: GameState) -> Optional[Move]:
        if state.mode != "play" or state.turn != self.color:
            return None
        legal_moves = get_all_legal_moves(state)
        if not legal_moves:
            return None

        self._nodes_searched = 0
        best_move = legal_moves[0]
        best_score = float("-inf")
        for move in legal_moves:
            child = _apply_move_to_copy(state, move)
            score = self._minimax(child, self.depth - 1)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _minimax(self, state: GameState, depth: int) -> float:
        self._nodes_searched += 1
        if self._nodes_searched >= self.max_nodes:
            return _evaluate_state(state, self.color)

        if depth == 0 or state.mode == "game_over":
            return _evaluate_state(state, self.color)
        legal_moves = get_all_legal_moves(state)
        if not legal_moves:
            return _evaluate_state(state, self.color)
        
        maximizing = (state.turn == self.color)
        
        if maximizing:
            max_eval = float("-inf")
            for move in legal_moves:
                child = _apply_move_to_copy(state, move)
                eval = self._minimax(child, depth - 1)
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float("inf")
            for move in legal_moves:
                child = _apply_move_to_copy(state, move)
                eval = self._minimax(child, depth - 1)
                min_eval = min(min_eval, eval)
            return min_eval

def _apply_move_to_copy(state: GameState, move: Move):
    next_state = deepcopy(state)
    src, dst = move
    next_state.apply_move(src, dst)
    return next_state

def _evaluate_state(state: GameState, color: str) -> float:
    opponent = "black" if color == "white" else "white"
    if state.mode == "game_over":
        if state.winner == color:
            return 1_000_000.0 # instead of inf to avoid potential overflow issues
        elif state.winner is None:
            return 0
        else:
            return -1_000_000.0
        
    score = 0.0
    for row in state.board:
        for piece in row:
            if piece is not None:
                value = PIECE_VALUES[piece.kind]
                if piece.color == color:
                    score += value
                else:
                    score -= value
                    
    def count_mobility(side_color: str) -> int:
        mobility = 0
        for row_index, row in enumerate(state.board):
            for col_index, piece in enumerate(row):
                if piece is not None and piece.color == side_color:
                    mobility += len(state.get_legal_moves(row_index, col_index))
        return mobility

    mobility_score = count_mobility(color) - count_mobility(opponent)
    return score + 0.1 * mobility_score

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