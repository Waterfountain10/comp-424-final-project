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


class _SearchTimeout(Exception):
    """stop search and return the best completed move"""


@register_agent("student_agent")  # do not change this string
class StudentAgent(Agent):
    def __init__(self):
        """Set up your agent. This runs once per game, before the first move, and must finish
        within INIT_TIME_LIMIT seconds."""
        super().__init__()
        self.name = "StudentAgent"
        self.last_completed_depth = 0

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
                candidate = self._search_root(
                    board, reserves, player, opponent, depth, deadline
                )
            except _SearchTimeout:
                break
            best_move = candidate
            self.last_completed_depth = depth
        return best_move

    def _search_root(self, board, reserves, player, opponent, depth, deadline):
        """Return the best move after one complete alpha-beta iteration."""
        moves = get_valid_moves(board, reserves, player)
        best_move = moves[0]
        best_score = -SEARCH_BOUND
        alpha, beta = -SEARCH_BOUND, SEARCH_BOUND
        for move in moves:
            if time.perf_counter() >= deadline:
                raise _SearchTimeout
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, player, move)
            winner = check_winner(next_board, player)
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
            if score > best_score:
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
        if depth == 0:
            # todo: return evaluate once the heuristic is ready, for now return neutral score <--- Jacob's work
            return 0
        # if depth == 0:
        #     return self.evaluate(
        #         board, reserves, player, opponent
        #     )

        # todo: apply tactical move ordering at every search node
        # current: recursive nodes keep get_valid_moves order
        # todo: cache scores by state, depth, and player to move
        # current: repeated states are searched again
        moves = get_valid_moves(board, reserves, to_move)
        if not moves:
            score = WIN_SCORE + depth
            return -score if to_move == player else score

        maximizing = to_move == player
        best_score = -SEARCH_BOUND if maximizing else SEARCH_BOUND
        for move in moves:
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, to_move, move)
            winner = check_winner(next_board, to_move)
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
                break
        return best_score

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
