from __future__ import annotations

import random
import time
import math
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


@dataclass
class _MCTSNode:
    state: GameState
    parent: Optional["_MCTSNode"] = None
    move_from_parent: Optional[Move] = None
    visits: int = 0
    value_sum: float = 0.0

    def __post_init__(self) -> None:
        self.untried_moves: list[Move] = get_all_legal_moves(self.state)
        self.children: list[_MCTSNode] = []


@dataclass
class MCSTAgent:
    color: str
    depth: int = 1
    max_think_ms: int = 1200
    exploration_weight: float = 1.41
    turn_sensitive_uct: bool = True
    rollout_policy: str = "heuristic"
    rng: Optional[random.Random] = None

    def pick_move(self, state: GameState) -> Optional[Move]:
        if state.mode != "play" or state.turn != self.color:
            return None

        legal_moves = get_all_legal_moves(state)
        if not legal_moves:
            return None

        if len(legal_moves) == 1:
            return legal_moves[0]

        local_rng = self.rng if self.rng is not None else random.Random()
        deadline_s: Optional[float]
        if self.max_think_ms > 0:
            deadline_s = time.perf_counter() + (self.max_think_ms / 1000.0)
        else:
            deadline_s = None

        root = _MCTSNode(state=deepcopy(state))

        while deadline_s is None or time.perf_counter() < deadline_s:
            node = root

            while not node.untried_moves and node.children:
                node = self._select_child_uct(node)

            if node.untried_moves:
                move = local_rng.choice(node.untried_moves)
                node.untried_moves.remove(move)
                next_state = _apply_move_to_copy(node.state, move)
                child = _MCTSNode(state=next_state, parent=node, move_from_parent=move)
                node.children.append(child)
                node = child

            reward = self._rollout(node.state, local_rng, deadline_s)

            while node is not None:
                node.visits += 1
                node.value_sum += reward
                node = node.parent

        if not root.children:
            return legal_moves[0]

        best_child = max(root.children, key=lambda child: child.visits)
        return best_child.move_from_parent

    def _select_child_uct(self, node: _MCTSNode) -> _MCTSNode:
        log_parent_visits = math.log(max(2, node.visits + 1))
        best_score = float("-inf")
        best_child = node.children[0]
        maximizing_turn = node.state.turn == self.color

        for child in node.children:
            if child.visits == 0:
                return child
            q_value = child.value_sum / child.visits
            if self.turn_sensitive_uct:
                exploit = q_value if maximizing_turn else -q_value
            else:
                exploit = q_value
            explore = self.exploration_weight * math.sqrt(log_parent_visits / child.visits)
            score = exploit + explore
            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def _rollout(
        self,
        state: GameState,
        rng: random.Random,
        deadline_s: Optional[float],
    ) -> float:
        rollout_state = deepcopy(state)
        max_rollout_plies = max(6, self.depth * 8)

        for _ in range(max_rollout_plies):
            if deadline_s is not None and time.perf_counter() >= deadline_s:
                break

            if rollout_state.mode == "game_over":
                return self._terminal_reward(rollout_state)

            legal_moves = get_all_legal_moves(rollout_state)
            if not legal_moves:
                break

            src, dst = self._pick_rollout_move(rollout_state, legal_moves, rng)
            rollout_state.apply_move(src, dst)

        if rollout_state.mode == "game_over":
            return self._terminal_reward(rollout_state)

        estimate = _evaluate_state(rollout_state, self.color)
        if estimate > 0:
            return 0.75
        if estimate < 0:
            return 0.25
        return 0.5

    def _terminal_reward(self, state: GameState) -> float:
        if state.winner == self.color:
            return 1.0
        if state.winner is None:
            return 0.5
        return 0.0

    def _pick_rollout_move(
        self,
        state: GameState,
        legal_moves: list[Move],
        rng: random.Random,
    ) -> Move:
        policy = self.rollout_policy.strip().lower()
        if policy == "random":
            return rng.choice(legal_moves)
        if policy in {"heuristic", "minimax1"}:
            return self._pick_heuristic_rollout_move(state, legal_moves, rng)
        return rng.choice(legal_moves)

    def _pick_heuristic_rollout_move(
        self,
        state: GameState,
        legal_moves: list[Move],
        rng: random.Random,
    ) -> Move:
        maximizing = state.turn == self.color
        best_score = float("-inf") if maximizing else float("inf")
        best_moves: list[Move] = []

        for move in legal_moves:
            next_state = _apply_move_to_copy(state, move)
            score = _evaluate_state(next_state, self.color)

            is_better = score > best_score if maximizing else score < best_score
            if is_better:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        if not best_moves:
            return rng.choice(legal_moves)
        return rng.choice(best_moves)

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

    def _make_agent(agent_name: str, color: str, depth: int) -> RandomAgent | MinimaxAgent | MCSTAgent:
        normalized = agent_name.strip().lower()
        if normalized == "random":
            return RandomAgent(color=color, rng=rng)
        if normalized == "minimax":
            return MinimaxAgent(color=color, depth=max(1, depth))
        if normalized in {"mcst", "mcts"}:
            return MCSTAgent(color=color, depth=max(1, depth), rng=rng)
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


