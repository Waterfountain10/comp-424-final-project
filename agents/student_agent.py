"""Student agent: edit ONLY this file."""

import time

import numpy as np

from agents.agent import Agent
from constants import *
from helpers import (
    LINES,
    Move,
    check_endgame,
    check_winner,
    copy_state,
    execute_move,
    get_valid_moves,
    top_view,
)
from store import register_agent

SEARCH_DEPTH = 2
MAX_SEARCH_DEPTH = 3  # todo: raise after evaluation and move ordering are faster
SEARCH_MARGIN = 0.25
WIN_SCORE = 1_000_000
SEARCH_BOUND = WIN_SCORE * 2
MAX_FORK_CANDIDATES = 4
MAX_ANTI_FORK_BRANCHING = 60


class _SearchTimeout(Exception):
    """stop search and return the best completed move"""


@register_agent("student_agent")  # do not change this string
class StudentAgent(Agent):
    def __init__(self):
        """Set up your agent. This runs once per game, before the first move, and must finish
        within INIT_TIME_LIMIT seconds."""
        super().__init__()
        self.name = "StudentAgentTacticalOrdering"
        self.last_completed_depth = 0
        self.search_nodes = 0
        self.search_cutoffs = 0
        self._pattern_key = None
        self._viable_lines = ()
        self._cell_lines = {}
        self._line_intersections = ()

    def step(self, board, reserves, player, opponent):
        """Return the Move you want to play.

        Takes: board, reserves - your own copies of the current position.
               player, opponent - your player number (1 or 2) and the other one.
        Agent.step in agents/agent.py explains each argument and the time limit.
        """
        start = time.perf_counter()
        deadline = start + STEP_TIME_LIMIT - SEARCH_MARGIN
        # ALLOW_MOVES and WIN_LENGTH (from constants) are the rule flags of this game.
        # helpers.get_valid_moves / check_winner already respect them; your own
        # move generator and evaluation function must too.

        # Keep a legal move ready before doing any tactical checks or search.
        moves = get_valid_moves(board, reserves, player)
        fallback = moves[0]

        best_move = fallback
        self.last_completed_depth = 0
        self.search_nodes = 0
        self.search_cutoffs = 0
        try:
            # todo: detect forced blocks and fork threats before search
            # current: depth-two search only catches immediate opponent wins
            # todo: search wins, blocks, and threats before ordinary moves
            # current: immediate wins come first; other moves keep helper order
            wins = self._winning_moves(board, reserves, player, deadline)
            if wins:
                return wins[0]
        except _SearchTimeout:
            return fallback

        for depth in range(SEARCH_DEPTH, MAX_SEARCH_DEPTH + 1):
            try:
                preferred_move = best_move if self.last_completed_depth else None
                candidate = self._search_root(
                    board,
                    reserves,
                    player,
                    opponent,
                    depth,
                    deadline,
                    preferred_move,
                )
            except _SearchTimeout:
                break
            best_move = candidate
            self.last_completed_depth = depth
        return best_move

    def _search_root(
        self,
        board,
        reserves,
        player,
        opponent,
        depth,
        deadline,
        preferred_move=None,
    ):
        """Return the best move after one complete alpha-beta iteration."""
        original_moves = get_valid_moves(board, reserves, player)
        original_order = {move: index for index, move in enumerate(original_moves)}
        children = self._ordered_children(
            board,
            reserves,
            player,
            deadline,
            preferred_move=preferred_move,
            exact=True,
        )
        best_move = children[0][0]
        best_score = -SEARCH_BOUND
        alpha, beta = -SEARCH_BOUND, SEARCH_BOUND
        for move, next_board, next_reserves, winner, _ in children:
            if time.perf_counter() >= deadline:
                raise _SearchTimeout
            alpha_before = alpha
            if winner == player:
                score = WIN_SCORE + depth
            elif winner == opponent:
                score = -WIN_SCORE - depth
            else:
                score = self._minimax(
                    next_board,
                    next_reserves,
                    opponent,
                    player,
                    opponent,
                    depth - 1,
                    alpha,
                    beta,
                    deadline,
                )
            if (
                winner == EMPTY
                and score <= alpha_before
                and original_order[move] < original_order[best_move]
            ):
                # A cutoff may return only an upper bound. Re-search an earlier
                # helper-order move before using it to resolve a root tie.
                score = self._minimax(
                    next_board,
                    next_reserves,
                    opponent,
                    player,
                    opponent,
                    depth - 1,
                    -SEARCH_BOUND,
                    SEARCH_BOUND,
                    deadline,
                )
            if score > best_score or (
                score == best_score
                and original_order[move] < original_order[best_move]
            ):
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
        return best_move

    def _minimax(
        self, board, reserves, to_move, player, opponent, depth, alpha, beta, deadline
    ):
        """Return a terminal-only alpha-beta score from player's perspective."""
        if time.perf_counter() >= deadline:
            raise _SearchTimeout
        self.search_nodes += 1
        if depth == 0:
            # todo: return evaluate once the heuristic is ready, for now return neutral score <--- Jacob's work
            return 0
        # if depth == 0:
        #     return self.evaluate(
        #         board, reserves, player, opponent
        #     )

        # todo: cache scores by state, depth, and player to move
        # current: repeated states are searched again
        children = self._ordered_children(
            board, reserves, to_move, deadline, exact=False
        )
        if not children:
            score = WIN_SCORE + depth
            return -score if to_move == player else score

        maximizing = to_move == player
        best_score = -SEARCH_BOUND if maximizing else SEARCH_BOUND
        for move, next_board, next_reserves, winner, _ in children:
            if winner == player:
                score = WIN_SCORE + depth
            elif winner == opponent:
                score = -WIN_SCORE - depth
            else:
                score = self._minimax(
                    next_board,
                    next_reserves,
                    3 - to_move,
                    player,
                    opponent,
                    depth - 1,
                    alpha,
                    beta,
                    deadline,
                )
            if maximizing:
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, score)
                beta = min(beta, best_score)
            if beta <= alpha:
                self.search_cutoffs += 1
                break
        return best_score

    def _prepare_pattern_bank(self, board):
        """Cache obstacle-aware lines, cell incidence, and line intersections."""
        obstacle_cells = tuple(
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if board[r, c, SMALL] == OBSTACLE
        )
        key = (WIN_LENGTH, obstacle_cells)
        if key == self._pattern_key:
            return

        viable_lines = []
        for line in LINES[WIN_LENGTH]:
            if not any(cell in obstacle_cells for cell in line):
                viable_lines.append(line)

        cell_lines = {
            (r, c): tuple(
                line for line in viable_lines if (r, c) in line
            )
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
        }
        intersections = []
        for index, first in enumerate(viable_lines):
            first_cells = set(first)
            for second in viable_lines[index + 1 :]:
                shared = first_cells.intersection(second)
                if shared:
                    intersections.append((first, second, tuple(shared)))

        self._pattern_key = key
        self._viable_lines = tuple(viable_lines)
        self._cell_lines = cell_lines
        self._line_intersections = tuple(intersections)

    def _has_winning_move(self, board, reserves, player, deadline):
        """Return whether player has a legal immediate win."""
        for move in get_valid_moves(board, reserves, player):
            if time.perf_counter() >= deadline:
                raise _SearchTimeout
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, player, move)
            if check_winner(next_board, player) == player:
                return True
        return False

    def _fork_lines(self, board, reserves, player):
        """Return viable three-piece lines and their possible winning cells."""
        self._prepare_pattern_bank(board)
        owners, sizes = top_view(board)
        available_sizes = self._available_sizes(owners, sizes, reserves, player)
        threats = []

        for line in self._viable_lines:
            own_count = sum(owners[cell] == player for cell in line)
            if own_count != WIN_LENGTH - 1:
                continue
            missing = [cell for cell in line if owners[cell] != player]
            if len(missing) != 1:
                continue
            cell = missing[0]
            owner = int(owners[cell])
            top_size = int(sizes[cell])
            if owner == EMPTY or (
                owner == 3 - player and self._can_cover(top_size, available_sizes)
            ):
                threats.append((line, cell))
        return tuple(threats)

    def _fork_candidate_moves(self, board, reserves, player, deadline, limit=None):
        """Return promising moves that create threats at two destinations."""
        candidates = []
        for index, move in enumerate(get_valid_moves(board, reserves, player)):
            if time.perf_counter() >= deadline:
                raise _SearchTimeout
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, player, move)
            if check_winner(next_board, player) != EMPTY:
                continue
            threats = self._fork_lines(next_board, next_reserves, player)
            destinations = {cell for _, cell in threats}
            if len(destinations) < 2:
                continue
            intersection = sum(move.dest in line for line, _ in threats) >= 2
            candidates.append(
                (
                    (move.size == LARGE and intersection, len(destinations), -index),
                    move,
                    next_board,
                    next_reserves,
                )
            )

        candidates.sort(key=lambda item: item[0], reverse=True)
        if limit is not None:
            candidates = candidates[:limit]
        return candidates

    def _is_forced_fork(self, board, reserves, player, deadline):
        """Verify that every opponent reply leaves player an immediate win."""
        opponent = 3 - player
        for reply in get_valid_moves(board, reserves, opponent):
            if time.perf_counter() >= deadline:
                raise _SearchTimeout
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, opponent, reply)
            winner = check_winner(next_board, opponent)
            if winner == opponent:
                return False
            if winner == player:
                continue
            if not self._has_winning_move(
                next_board, next_reserves, player, deadline
            ):
                return False
        return True

    def _pinned_defender_count(self, board, player):
        """Count opponent covers whose unrelated removal reveals player's line."""
        self._prepare_pattern_bank(board)
        owners, _ = top_view(board)
        opponent = 3 - player
        pinned = 0
        for cell, lines in self._cell_lines.items():
            r, c = cell
            if owners[cell] != opponent:
                continue
            below_owner, _ = self._piece_below(board, r, c)
            if below_owner != player:
                continue
            for line in lines:
                if all(other == cell or owners[other] == player for other in line):
                    pinned += 1
                    break
        return pinned

    def _line_progress(self, owners, player):
        """Return a cheap obstacle-aware line score used only for ordering."""
        score = 0
        opponent = 3 - player
        for line in self._viable_lines:
            own = sum(owners[cell] == player for cell in line)
            enemy = sum(owners[cell] == opponent for cell in line)
            score += own * own - enemy * enemy
        return score

    def _ordered_children(
        self,
        board,
        reserves,
        to_move,
        deadline,
        preferred_move=None,
        exact=False,
    ):
        """Simulate and tactically order every legal move without filtering."""
        moves = get_valid_moves(board, reserves, to_move)
        if not moves:
            return []

        self._prepare_pattern_bank(board)
        opponent = 3 - to_move
        owners, _ = top_view(board)
        before_progress = self._line_progress(owners, to_move) if exact else 0
        threatened = exact and self._has_winning_move(
            board, reserves, opponent, deadline
        )

        children = []
        for index, move in enumerate(moves):
            if time.perf_counter() >= deadline:
                raise _SearchTimeout
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, to_move, move)
            winner = check_winner(next_board, to_move)
            if exact:
                next_owners, _ = top_view(next_board)
                threats = self._fork_lines(next_board, next_reserves, to_move)
                threat_destinations = {cell for _, cell in threats}
                fork_shape = len(threat_destinations) >= 2
                large_intersection = (
                    move.size == LARGE
                    and sum(move.dest in line for line, _ in threats) >= 2
                )
                line_delta = (
                    self._line_progress(next_owners, to_move) - before_progress
                )
                pinned = self._pinned_defender_count(next_board, to_move)
            else:
                fork_shape = False
                large_intersection = (
                    move.size == LARGE and len(self._cell_lines[move.dest]) >= 2
                )
                line_delta = 0
                pinned = 0

            complete_defense = False
            if threatened and winner == EMPTY:
                complete_defense = not self._has_winning_move(
                    next_board, next_reserves, opponent, deadline
                )

            destination_owner = int(owners[move.dest])
            cover_pressure = 0
            if destination_owner == opponent:
                for line in self._cell_lines[move.dest]:
                    cover_pressure += sum(owners[cell] == opponent for cell in line)

            below_owner = EMPTY
            if move.src is not None:
                below_owner, _ = self._piece_below(board, *move.src)
            self_relay = below_owner == to_move
            safe_recovery = below_owner == opponent and winner == EMPTY
            incidence = len(self._cell_lines[move.dest])
            reserve_economy = (
                NUM_SIZES - 1 - move.size
                if move.is_placement() and destination_owner == EMPTY
                else 0
            )

            features = {
                "complete_defense": complete_defense,
                "verified_fork": False,
                "anti_fork": False,
                "fork_shape": fork_shape,
                "large_intersection": large_intersection,
                "preferred": move == preferred_move,
                "pinned": pinned,
                "safe_recovery": safe_recovery,
                "cover_pressure": cover_pressure,
                "self_relay": self_relay,
                "line_delta": line_delta,
                "incidence": incidence,
                "size": move.size,
                "reserve_economy": reserve_economy,
                "index": index,
            }
            children.append([move, next_board, next_reserves, winner, features])

        if exact:
            fork_candidates = [
                child
                for child in children
                if child[3] == EMPTY and child[4]["fork_shape"]
            ]
            fork_candidates.sort(
                key=lambda child: (
                    child[4]["large_intersection"],
                    child[4]["line_delta"],
                    child[4]["incidence"],
                ),
                reverse=True,
            )
            for child in fork_candidates[:MAX_FORK_CANDIDATES]:
                child[4]["verified_fork"] = self._is_forced_fork(
                    child[1], child[2], to_move, deadline
                )

            if not threatened and len(children) <= MAX_ANTI_FORK_BRANCHING:
                opponent_candidates = self._fork_candidate_moves(
                    board,
                    reserves,
                    opponent,
                    deadline,
                    limit=MAX_FORK_CANDIDATES,
                )
                forced_threat = any(
                    self._is_forced_fork(candidate[2], candidate[3], opponent, deadline)
                    for candidate in opponent_candidates
                )
                if forced_threat:
                    for child in children:
                        if child[3] != EMPTY:
                            continue
                        replies = self._fork_candidate_moves(
                            child[1], child[2], opponent, deadline, limit=1
                        )
                        child[4]["anti_fork"] = not replies

        def ordering_key(child):
            winner = child[3]
            features = child[4]
            terminal = 2 if winner == to_move else 0 if winner == opponent else 1
            return (
                terminal,
                features["complete_defense"],
                features["verified_fork"],
                features["anti_fork"],
                features["preferred"],
                features["large_intersection"],
                features["fork_shape"],
                features["pinned"],
                features["safe_recovery"],
                features["cover_pressure"],
                features["self_relay"],
                features["line_delta"],
                features["incidence"],
                features["reserve_economy"],
                features["size"],
                -features["index"],
            )

        children.sort(key=ordering_key, reverse=True)
        return [tuple(child) for child in children]

    def evaluate(self, board, reserves, player, opponent) -> int:
        """
        Return a score of the board from the perspective of player.
        Higher is better for player (us)
        Should stay relatively cheap as will be called many times during search.

        Strategy:
        - Line score:
            - exponentially score based on how many visible pieces of player and opponent are in a line
            - skip obstacle lines and start with no base points for mixed lines
            - Consider size of each block
                - a single large opponent block can completely trump a line
            - even more bonus if either side can win on that line (check for a legal winning move when
              they own all but one square, even if that last square has an opponent piece)
        - Reserves:
            - bigger pieces in reserves are worth more points as they give us great optionality in the future, small though cause we dont want to hoard
        - Double Threats: TBD
        - Vulnerability: check the opponent's reserves and bigger pieces they can move from the board
        """
        # todo: combine the four component scores into one cheap integer
        # current: search does not call evaluate and this method is unfinished
        # todo: benchmark evaluation cost before increasing search depth
        # current: terminal-only search avoids all heuristic work
        raise NotImplementedError

    def _score_lines(self, board, reserves, player, opponent):
        """how close we are to a line vs them"""
        # todo: reward our viable lines and penalize the opponent's
        # current: _line_features extracts line ownership but assigns no score
        raise NotImplementedError

    def _score_reserves(self, board, reserves, player, opponent):
        """what the pieces left in reserve are worth"""
        # todo: score the weighted reserve difference by piece size
        # current: _reserve_counts only returns the available counts
        raise NotImplementedError

    def _score_threats(self, board, reserves, player, opponent):
        """threats for us + them"""
        # todo: score immediate wins, forced blocks, and fork threats for both players
        # current: _winning_moves only lists immediate wins
        raise NotImplementedError

    def _score_vulnerability(self, board, reserves, player, opponent):
        """pieces that could get covered or uncovered"""
        # todo: score pieces that can be covered or reveal a dangerous piece below
        # current: _can_cover and _piece_below expose the needed facts without scoring them
        raise NotImplementedError

    def _line_features(self, owners, sizes, player, opponent):
        """line -> piece sizes + empty spots, obstacle -> skip"""
        features = []

        for cells in LINES[WIN_LENGTH]:
            own_sizes = []
            opponent_sizes = []
            empty_count = 0
            blocked = False

            for r, c in cells:
                owner = owners[r, c]
                if owner == OBSTACLE:
                    # one obstacle -> cant finish this line
                    blocked = True
                    break
                if owner == player:
                    own_sizes.append(int(sizes[r, c]))
                elif owner == opponent:
                    opponent_sizes.append(int(sizes[r, c]))
                else:
                    empty_count += 1

            if blocked:
                continue
            # keep mixed lines too, smaller opponent pieces can get covered
            features.append(
                {
                    "cells": cells,
                    "own_sizes": tuple(own_sizes),
                    "opponent_sizes": tuple(opponent_sizes),
                    "empty_count": empty_count,
                }
            )
        return features

    def _reserve_counts(self, reserves, player):
        """pieces left in reserve, small -> large"""
        counts = []
        for count in reserves[player]:
            counts.append(int(count))  # handle np int
        return tuple(counts)

    def _available_sizes(self, owners, sizes, reserves, player):
        """sizes in reserve or on top of stacks"""
        # one bool per size, no duplicates
        available = [False] * NUM_SIZES
        for size in range(NUM_SIZES):
            if reserves[player, size] > 0:
                available[size] = True

        if ALLOW_MOVES:
            # only top pieces count, covered ones cant move
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if owners[r, c] == player:
                        size = int(sizes[r, c])
                        available[size] = True

        available_sizes = []
        for size in range(NUM_SIZES):
            if available[size]:
                available_sizes.append(size)
        return tuple(available_sizes)

    def _can_cover(self, top_size, available_sizes):
        """just sizes. skip obstacles first, still check move safety"""
        for size in available_sizes:
            # same size wont fit, must be bigger
            if size > top_size:
                return True
        return False

    def _piece_below(self, board, row, col):
        """piece under the top one, nothing -> (EMPTY, -1)"""
        if board[row, col, SMALL] == OBSTACLE:
            return EMPTY, -1

        found_top = False
        # biggest -> smallest, skip the first piece we find
        for size in range(NUM_SIZES - 1, -1, -1):
            owner = int(board[row, col, size])
            if owner == EMPTY:
                continue
            if found_top:
                return owner, size
            found_top = True

        # nothing under
        return EMPTY, -1

    def _winning_moves(self, board, reserves, player, deadline=None):
        """moves that win, w/o uncovering a win for them"""
        wins = []
        for move in get_valid_moves(board, reserves, player):
            if deadline is not None and time.perf_counter() >= deadline:
                raise _SearchTimeout
            # try on copies, dont modify the actual position
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, player, move)
            # checks their revealed line first, even if we made a line too
            if check_winner(next_board, player) == player:
                wins.append(move)
        return wins
