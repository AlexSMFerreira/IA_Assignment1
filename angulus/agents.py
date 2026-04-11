from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple
from copy import deepcopy
from .rules import GameState

Move = Tuple[Tuple[int, int], Tuple[int, int]]
GameOutcome = Tuple[str, Optional[int]]

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
    color: str

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
    max_think_ms: int = 1200
    
    def pick_move(self, state: GameState) -> Optional[Move]:
        if state.mode != "play" or state.turn != self.color:
            return None
        legal_moves = get_all_legal_moves(state)
        if not legal_moves:
            return None

        self._nodes_searched = 0
        self._deadline_s: Optional[float]
        if self.max_think_ms > 0:
            self._deadline_s = time.perf_counter() + (self.max_think_ms / 1000.0)
        else:
            self._deadline_s = None

        best_move = legal_moves[0]
        best_score = float("-inf")
        alpha = float("-inf")
        beta = float("inf")
        for move in legal_moves:
            if self._time_limit_reached():
                break
            child = _apply_move_to_copy(state, move)
            score = self._minimax(child, self.depth - 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
        return best_move

    def _time_limit_reached(self) -> bool:
        return self._deadline_s is not None and time.perf_counter() >= self._deadline_s

    def _minimax(self, state: GameState, depth: int, alpha: float, beta: float) -> float:
        if self._time_limit_reached():
            return _evaluate_state(state, self.color)

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
                eval = self._minimax(child, depth - 1, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in legal_moves:
                child = _apply_move_to_copy(state, move)
                eval = self._minimax(child, depth - 1, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
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
            return 1_000_000.0
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

# --- FUNCOES DE SELF-PLAY (NECESSARIAS PARA O MAIN.PY) ---

def _empty_report() -> dict[str, object]:
    return {
        "results": {"white": 0, "black": 0, "draw": 0},
        "avg_winner_moves_per_game": 0,
    }


def _record_outcome(report: dict[str, object], outcome: GameOutcome) -> None:
    winner, winner_moves = outcome
    results = report["results"]
    winner_moves_total = report["avg_winner_moves_per_game"]

    if not isinstance(results, dict) or not isinstance(winner_moves_total, int):
        raise ValueError("Invalid simulation report structure")

    results[winner] += 1
    if winner in {"white", "black"} and winner_moves is not None:
        report["avg_winner_moves_per_game"] = winner_moves_total + winner_moves

def run_ai_self_play(
    *,
    games: int = 100,
    white_ai: str = "random",
    white_depth: int = 1,
    black_ai: str = "random",
    black_depth: int = 1,
    seed: Optional[int] = None,
    max_plies: int = 500,
) -> dict[str, object]:
    report = _empty_report()
    rng = random.Random(seed)

    def _make_agent(agent_name: str, color: str, depth: int) -> RandomAgent | MinimaxAgent:
        normalized = agent_name.strip().lower()
        if normalized == "random":
            return RandomAgent(color=color, rng=rng)
        if normalized == "minimax":
            return MinimaxAgent(color=color, depth=max(1, depth))
        if normalized in {"mcst", "mcts"}:
            # manage_todo_list: ligar MCTSAgent aqui quando estiver implementado.
            raise NotImplementedError("MCST game mode is not implemented yet")
        raise ValueError(f"Invalid AI type: {agent_name}")

    for game_index in range(games):
        state = GameState()
        state.turn = "white" if game_index % 2 == 0 else "black"
        move_counts = {"white": 0, "black": 0}
        white_agent = _make_agent(white_ai, "white", white_depth)
        black_agent = _make_agent(black_ai, "black", black_depth)

        outcome: GameOutcome = ("draw", None)
        for _ in range(max_plies):
            current_agent = white_agent if state.turn == "white" else black_agent
            selected_move = current_agent.pick_move(state)
            if selected_move is None:
                break

            mover_color = state.turn
            src, dst = selected_move
            state.apply_move(src, dst)
            move_counts[mover_color] += 1

            if state.mode == "game_over":
                if state.winner is not None:
                    outcome = (state.winner, move_counts[state.winner])
                break

        _record_outcome(report, outcome)

    report["avg_winner_moves_per_game"] = report["avg_winner_moves_per_game"] / games if games > 0 else None
    return report


