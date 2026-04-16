from __future__ import annotations

import random
import time
import math
from dataclasses import dataclass, field
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

_EVAL_CACHE: dict[tuple[object, ...], float] = {}
_MAX_EVAL_CACHE_SIZE = 50000
_DIRECTIONS_8 = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

def get_all_legal_moves(state: GameState, include_repetition: bool = True) -> list[Move]:
    moves: list[Move] = []
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != state.turn:
                continue
            source = (row_index, col_index)
            for destination in state.get_legal_moves(row_index, col_index, include_repetition=include_repetition):
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
    depth: int = 3
    max_nodes: int = 250000
    max_think_ms: int = 5000
    _search_termination_reason: Optional[str] = field(default=None, init=False, repr=False)
    
    def pick_move(self, state: GameState) -> Optional[Move]:
        if state.mode != "play" or state.turn != self.color:
            return None
        legal_moves = get_all_legal_moves(state)
        if not legal_moves:
            return None

        self._nodes_searched = 0
        self._search_termination_reason = None
        self._deadline_s: Optional[float]
        if self.max_think_ms > 0:
            self._deadline_s = time.perf_counter() + (self.max_think_ms / 1000.0)
        else:
            self._deadline_s = None

        legal_moves = self._order_moves(state, legal_moves)
        best_move = legal_moves[0]
        best_score = float("-inf")
        alpha = float("-inf")
        beta = float("inf")
        for move in legal_moves:
            if self._time_limit_reached():
                self._search_termination_reason = "time limit"
                break
            if not state.apply_move_with_history(*move):
                continue
            try:
                score = self._minimax(state, self.depth - 1, alpha, beta)
            finally:
                state.undo_move()
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
        
        if self._search_termination_reason is None:
            self._search_termination_reason = "complete"
        return best_move

    def _time_limit_reached(self) -> bool:
        return self._deadline_s is not None and time.perf_counter() >= self._deadline_s

    def _order_moves(self, state: GameState, moves: list[Move]) -> list[Move]:
        """Sort moves by simple heuristic (descending) to improve alpha-beta pruning.
        Prioritizes: king captures > captures > neutral moves."""
        def move_score(move: Move) -> float:
            src, dst = move
            piece = state.board[src[0]][src[1]]
            target = state.board[dst[0]][dst[1]]
            
            if piece is None:
                return 0.0
            
            score = 0.0
            if target is not None and target.color != piece.color:
                if target.kind == "king":
                    score += 10_000.0
                else:
                    score += PIECE_VALUES.get(target.kind, 0) * 10.0
            return score
        
        return sorted(moves, key=lambda m: -move_score(m))

    def _minimax(self, state: GameState, depth: int, alpha: float, beta: float) -> float:
        if self._time_limit_reached():
            if self._search_termination_reason is None:
                self._search_termination_reason = "time limit"
            return _evaluate_state_search(state, self.color)

        self._nodes_searched += 1
        if self._nodes_searched >= self.max_nodes:
            if self._search_termination_reason is None:
                self._search_termination_reason = "node limit"
            return _evaluate_state_search(state, self.color)

        if depth == 0:
            if self._search_termination_reason is None:
                self._search_termination_reason = "depth limit"
            return _evaluate_state_search(state, self.color)
        
        if state.mode == "game_over":
            if self._search_termination_reason is None:
                self._search_termination_reason = "terminal"
            return _evaluate_state_search(state, self.color)
        
        legal_moves = get_all_legal_moves(state, include_repetition=False)
        if not legal_moves:
            return _evaluate_state_search(state, self.color)
        
        legal_moves = self._order_moves(state, legal_moves)
        maximizing = (state.turn == self.color)
        
        if maximizing:
            max_eval = float("-inf")
            for move in legal_moves:
                if not state.apply_move_with_history(*move, validate=False):
                    continue
                try:
                    eval = self._minimax(state, depth - 1, alpha, beta)
                finally:
                    state.undo_move()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in legal_moves:
                if not state.apply_move_with_history(*move, validate=False):
                    continue
                try:
                    eval = self._minimax(state, depth - 1, alpha, beta)
                finally:
                    state.undo_move()
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
    max_think_ms: int = 3000
    exploration_weight: float = 1.41
    turn_sensitive_uct: bool = True
    rollout_policy: str = "heuristic"
    rng: Optional[random.Random] = None
    _tree_root: Optional["_MCTSNode"] = field(default=None, init=False, repr=False)

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

        root = self._reuse_tree_root(state)

        while deadline_s is None or time.perf_counter() < deadline_s:
            node = root

            while not node.untried_moves and node.children:
                node = self._select_child_uct(node)

            if node.untried_moves:
                move = self._pop_best_expansion_move(node, local_rng)
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
        best_child.parent = None
        self._tree_root = best_child
        return best_child.move_from_parent

    def _reuse_tree_root(self, state: GameState) -> _MCTSNode:
        signature = _state_signature(state)
        if self._tree_root is None:
            self._tree_root = _MCTSNode(state=deepcopy(state))
            return self._tree_root

        if _state_signature(self._tree_root.state) == signature:
            return self._tree_root

        for child in self._tree_root.children:
            if _state_signature(child.state) == signature:
                child.parent = None
                self._tree_root = child
                return self._tree_root

        self._tree_root = _MCTSNode(state=deepcopy(state))
        return self._tree_root

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
        max_rollout_plies = max(4, self.depth * 5)

        for _ in range(max_rollout_plies):
            if deadline_s is not None and time.perf_counter() >= deadline_s:
                break

            if rollout_state.mode == "game_over":
                return self._terminal_reward(rollout_state)

            legal_moves = get_all_legal_moves(rollout_state)
            if not legal_moves:
                break

            src, dst = self._pick_rollout_move(rollout_state, legal_moves, rng)
            rollout_state.apply_move_with_history(src, dst, validate=False)

        if rollout_state.mode == "game_over":
            return self._terminal_reward(rollout_state)

        return _evaluate_state_normalized(rollout_state, self.color)

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
        tactical_move = self._pick_tactical_move(state, legal_moves)
        if tactical_move is not None:
            return tactical_move

        policy = self.rollout_policy.strip().lower()
        if policy == "random":
            return rng.choice(legal_moves)
        if policy in {"heuristic", "minimax1"}:
            return self._pick_heuristic_rollout_move(state, legal_moves, rng)
        return rng.choice(legal_moves)

    def _pick_tactical_move(self, state: GameState, legal_moves: list[Move]) -> Optional[Move]:
        best_move: Optional[Move] = None
        best_score = float("-inf")

        for move in legal_moves:
            score = self._score_tactical_move(state, move)
            if score > best_score:
                best_score = score
                best_move = move

        if best_move is None or best_score <= 0.0:
            return None
        return best_move

    def _score_tactical_move(self, state: GameState, move: Move) -> float:
        src, dst = move
        mover = state.board[src[0]][src[1]]
        target = state.board[dst[0]][dst[1]]
        if mover is None:
            return 0.0

        score = 0.0
        mover_value = PIECE_VALUES[mover.kind]
        if target is not None and target.color != mover.color:
            if target.kind == "king":
                score += 10_000.0
            score += 5.0 * PIECE_VALUES[target.kind]

        own_king_before = _find_king(state, mover.color)
        own_king_was_threatened = False
        opponent = _opp(mover.color)
        if own_king_before is not None:
            own_king_was_threatened = _is_square_capturable_next_turn(
                state,
                own_king_before[0],
                own_king_before[1],
                opponent,
            )

        next_state = _apply_move_to_copy(state, move)

        own_king = _find_king(next_state, mover.color)
        if own_king is not None and _is_square_capturable_next_turn(next_state, own_king[0], own_king[1], opponent):
            return -1_000.0

        if own_king_before is not None and own_king is not None:
            own_king_is_safe_now = not _is_square_capturable_next_turn(
                next_state,
                own_king[0],
                own_king[1],
                opponent,
            )
            if own_king_was_threatened and own_king_is_safe_now:
                score += 1000.0

        # Discourage moving into immediate recapture unless compensated by gain.
        if _is_square_capturable_next_turn(next_state, dst[0], dst[1], opponent):
            captured_value = PIECE_VALUES[target.kind] if target is not None else 0.0
            score -= max(0.0, 3.0 * mover_value - 2.0 * captured_value)

        opponent_king = _find_king(next_state, opponent)
        if opponent_king is not None and _can_attack_square(next_state, dst[0], dst[1], opponent_king[0], opponent_king[1]):
            score += 8.0

        return score

    def _pop_best_expansion_move(self, node: _MCTSNode, rng: random.Random) -> Move:
        if not node.untried_moves:
            raise ValueError("Cannot expand a node without untried moves")

        best_moves: list[Move] = []
        best_score = float("-inf")
        for move in node.untried_moves:
            score = self._score_tactical_move(node.state, move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        if best_moves:
            return rng.choice(best_moves)
        return rng.choice(node.untried_moves)

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


def _opp(color: str) -> str:
    return "black" if color == "white" else "white"


def _state_cache_key(state: GameState, color: str) -> tuple[object, ...]:
    board_signature: list[tuple[str, ...]] = []
    for row in state.board:
        signature_row: list[str] = []
        for piece in row:
            if piece is None:
                signature_row.append(".")
            else:
                signature_row.append(f"{piece.color[0]}{piece.kind[0]}")
        board_signature.append(tuple(signature_row))

    return (
        color,
        state.mode,
        state.turn,
        state.winner,
        tuple(board_signature),
    )


def _state_signature(state: GameState) -> tuple[object, ...]:
    board_signature: list[tuple[str, ...]] = []
    for row in state.board:
        signature_row: list[str] = []
        for piece in row:
            if piece is None:
                signature_row.append(".")
            else:
                signature_row.append(f"{piece.color[0]}{piece.kind[0]}")
        board_signature.append(tuple(signature_row))

    return (
        state.mode,
        state.turn,
        state.winner,
        tuple(board_signature),
    )


def _find_king(state: GameState, side_color: str) -> Optional[tuple[int, int]]:
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is not None and piece.color == side_color and piece.kind == "king":
                return row_index, col_index
    return None


def _estimate_game_phase(state: GameState) -> float:
    total_non_king_material = 0.0
    for row in state.board:
        for piece in row:
            if piece is None or piece.kind == "king":
                continue
            total_non_king_material += PIECE_VALUES[piece.kind]

    # Initial non-king material is 42 in the default setup.
    return max(0.0, min(1.0, total_non_king_material / 42.0))


def _approx_piece_mobility(state: GameState, row: int, col: int) -> int:
    piece = state.board[row][col]
    if piece is None:
        return 0

    moves = 0
    if piece.kind == "pawn":
        for dr, dc in _DIRECTIONS_8:
            nr = row + dr
            nc = col + dc
            if not (0 <= nr < len(state.board) and 0 <= nc < len(state.board[0])):
                continue
            target = state.board[nr][nc]
            is_diagonal = abs(dr) == 1 and abs(dc) == 1
            if is_diagonal:
                if target is not None and target.color != piece.color:
                    moves += 1
            else:
                if target is None:
                    moves += 1
        return moves

    max_steps = 2 if piece.kind == "piece" else 3
    for dr, dc in _DIRECTIONS_8:
        for step in range(1, max_steps + 1):
            nr = row + dr * step
            nc = col + dc * step
            if not (0 <= nr < len(state.board) and 0 <= nc < len(state.board[0])):
                break
            target = state.board[nr][nc]
            if target is None:
                moves += 1
                continue
            if target.color != piece.color:
                moves += 1
            break
    return moves


def _approx_mobility(state: GameState, side_color: str) -> int:
    mobility = 0
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is not None and piece.color == side_color:
                mobility += _approx_piece_mobility(state, row_index, col_index)
    return mobility


def _can_attack_square(
    state: GameState,
    row: int,
    col: int,
    target_row: int,
    target_col: int,
) -> bool:
    piece = state.board[row][col]
    if piece is None:
        return False

    dr = target_row - row
    dc = target_col - col
    abs_dr = abs(dr)
    abs_dc = abs(dc)

    if piece.kind == "pawn":
        return abs_dr == 1 and abs_dc == 1

    max_steps = 2 if piece.kind == "piece" else 3
    if not (dr == 0 or dc == 0 or abs_dr == abs_dc):
        return False

    step_count = max(abs_dr, abs_dc)
    if step_count == 0 or step_count > max_steps:
        return False

    step_r = 0 if dr == 0 else dr // abs_dr
    step_c = 0 if dc == 0 else dc // abs_dc

    for step in range(1, step_count):
        nr = row + step_r * step
        nc = col + step_c * step
        if state.board[nr][nc] is not None:
            return False
    return True


def _attack_pressure_on_square(
    state: GameState,
    target_row: int,
    target_col: int,
    attacker_color: str,
) -> float:
    pressure = 0.0
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != attacker_color:
                continue
            if _can_attack_square(state, row_index, col_index, target_row, target_col):
                pressure += 1.0 if piece.kind == "pawn" else (1.6 if piece.kind == "piece" else 1.2)
    return pressure


def _is_square_capturable_next_turn(
    state: GameState,
    target_row: int,
    target_col: int,
    attacker_color: str,
) -> bool:
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != attacker_color:
                continue
            if _can_attack_square(state, row_index, col_index, target_row, target_col):
                return True
    return False


def _capture_potential(state: GameState, side_color: str) -> float:
    score = 0.0
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != side_color:
                continue
            if piece.kind == "pawn":
                for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nr = row_index + dr
                    nc = col_index + dc
                    if 0 <= nr < len(state.board) and 0 <= nc < len(state.board[0]):
                        target = state.board[nr][nc]
                        if target is not None and target.color != side_color:
                            score += PIECE_VALUES[target.kind]
                continue

            max_steps = 2 if piece.kind == "piece" else 3
            for dr, dc in _DIRECTIONS_8:
                for step in range(1, max_steps + 1):
                    nr = row_index + dr * step
                    nc = col_index + dc * step
                    if not (0 <= nr < len(state.board) and 0 <= nc < len(state.board[0])):
                        break
                    target = state.board[nr][nc]
                    if target is None:
                        continue
                    if target.color != side_color:
                        score += PIECE_VALUES[target.kind]
                    break
    return score


def _king_pressure_from_proximity(state: GameState, attacker: str, defender: str) -> float:
    defender_king = _find_king(state, defender)
    if defender_king is None:
        return 0.0
    kr, kc = defender_king

    pressure = 0.0
    for row_index, row in enumerate(state.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != attacker or piece.kind == "king":
                continue
            chebyshev_dist = max(abs(kr - row_index), abs(kc - col_index))
            pressure += PIECE_VALUES[piece.kind] / (1.0 + chebyshev_dist)
    return pressure

def _evaluate_state(state: GameState, color: str) -> float:
    cache_key = _state_cache_key(state, color)
    cached = _EVAL_CACHE.get(cache_key)
    if cached is not None:
        return cached

    opponent = _opp(color)
    if state.mode == "game_over":
        if state.winner == color:
            terminal = 1_000_000.0
            _EVAL_CACHE[cache_key] = terminal
            return terminal
        elif state.winner is None:
            _EVAL_CACHE[cache_key] = 0.0
            return 0.0
        else:
            terminal = -1_000_000.0
            _EVAL_CACHE[cache_key] = terminal
            return terminal
        
    material_score = 0.0
    for row in state.board:
        for piece in row:
            if piece is not None:
                value = PIECE_VALUES[piece.kind]
                if piece.color == color:
                    material_score += value
                else:
                    material_score -= value

    phase = _estimate_game_phase(state)

    mobility_score = _approx_mobility(state, color) - _approx_mobility(state, opponent)
    capture_score = _capture_potential(state, color) - _capture_potential(state, opponent)

    own_king = _find_king(state, color)
    opp_king = _find_king(state, opponent)

    own_king_risk = 0.0
    opp_king_risk = 0.0
    if own_king is not None:
        own_king_risk = _attack_pressure_on_square(state, own_king[0], own_king[1], opponent)
        if _is_square_capturable_next_turn(state, own_king[0], own_king[1], opponent):
            own_king_risk += 8.0
    if opp_king is not None:
        opp_king_risk = _attack_pressure_on_square(state, opp_king[0], opp_king[1], color)
        if _is_square_capturable_next_turn(state, opp_king[0], opp_king[1], color):
            opp_king_risk += 8.0
    king_risk_score = opp_king_risk - own_king_risk

    pressure_score = _king_pressure_from_proximity(state, color, opponent) - _king_pressure_from_proximity(state, opponent, color)

    tactical_intensity = abs(capture_score) + abs(king_risk_score)
    tactical_scale = min(1.0, tactical_intensity / 10.0)

    material_weight = 1.0 + 0.2 * (1.0 - phase)
    mobility_weight = (0.18 * phase + 0.06 * (1.0 - phase)) * (1.0 - 0.65 * tactical_scale)
    capture_weight = (0.16 * phase + 0.12 * (1.0 - phase)) * (1.0 + 0.9 * tactical_scale)
    king_risk_weight = (0.12 * phase + 0.30 * (1.0 - phase)) * (1.0 + 0.7 * tactical_scale)
    pressure_weight = 0.08 * phase + 0.22 * (1.0 - phase)

    value = (
        material_weight * material_score
        + mobility_weight * mobility_score
        + capture_weight * capture_score
        + king_risk_weight * king_risk_score
        + pressure_weight * pressure_score
    )

    if len(_EVAL_CACHE) >= _MAX_EVAL_CACHE_SIZE:
        _EVAL_CACHE.clear()
    _EVAL_CACHE[cache_key] = value
    return value


def _evaluate_state_normalized(state: GameState, color: str) -> float:
    if state.mode == "game_over":
        if state.winner == color:
            return 1.0
        if state.winner is None:
            return 0.5
        return 0.0

    raw = _evaluate_state(state, color)
    # Smoothly maps unbounded evaluation values into [0, 1] for MCTS rewards.
    if raw >= 300.0:
        return 1.0
    if raw <= -300.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-raw / 6.0))


def _evaluate_state_search(state: GameState, color: str) -> float:
    opponent = _opp(color)

    if state.mode == "game_over":
        if state.winner == color:
            return 1_000_000.0
        if state.winner is None:
            return 0.0
        return -1_000_000.0

    material_score = 0.0
    for row in state.board:
        for piece in row:
            if piece is None:
                continue
            value = PIECE_VALUES[piece.kind]
            material_score += value if piece.color == color else -value

    own_king = _find_king(state, color)
    opp_king = _find_king(state, opponent)

    own_king_risk = 0.0
    opp_king_risk = 0.0
    if own_king is not None:
        if _is_square_capturable_next_turn(state, own_king[0], own_king[1], opponent):
            own_king_risk = 12.0
    if opp_king is not None:
        if _is_square_capturable_next_turn(state, opp_king[0], opp_king[1], color):
            opp_king_risk = 12.0

    return (material_score * 10.0) + (opp_king_risk - own_king_risk)

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


