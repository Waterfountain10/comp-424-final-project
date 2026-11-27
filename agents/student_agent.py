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

# todo: search deeper with iterative deepening until the deadline
# current: every move searches exactly two plies
SEARCH_DEPTH = 2
SEARCH_MARGIN = 0.25
WIN_SCORE = 1_000_000


class _SearchTimeout(Exception):
    """stop search and return the best completed move"""


@register_agent("student_agent")  # do not change this string
class StudentAgent(Agent):
    def __init__(self):
        """Set up your agent. This runs once per game, before the first move, and must finish
        within INIT_TIME_LIMIT seconds."""
        super().__init__()
        self.name = "StudentAgent"

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
        try:
            # todo: detect forced blocks and fork threats before search
            # current: depth-two search only catches immediate opponent wins
            # todo: search wins, blocks, and threats before ordinary moves
            # current: immediate wins come first; other moves keep helper order
            wins = self._winning_moves(board, reserves, player, deadline)
            if wins:
                return wins[0]

            best_score = -WIN_SCORE
            alpha, beta = -WIN_SCORE, WIN_SCORE
            for move in moves:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout
                next_board, next_reserves = copy_state(board, reserves)
                execute_move(next_board, next_reserves, player, move)
                winner = check_winner(next_board, player)
                if winner == opponent:
                    score = -WIN_SCORE
                else:
                    score = self._minimax(
                        next_board,
                        next_reserves,
                        opponent,
                        player,
                        opponent,
                        SEARCH_DEPTH - 1,
                        alpha,
                        beta,
                        deadline,
                    )
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
        except _SearchTimeout:
            pass
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
            return -WIN_SCORE if to_move == player else WIN_SCORE

        maximizing = to_move == player
        best_score = -WIN_SCORE if maximizing else WIN_SCORE
        for move in moves:
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, to_move, move)
            winner = check_winner(next_board, to_move)
            if winner == player:
                score = WIN_SCORE
            elif winner == opponent:
                score = -WIN_SCORE
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
        Board score, positive is better for player
        Should stay relatively cheap as will be called many times during search

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
        - Double Threats: bonus for 2 or more distinct winning cells
        - Vulnerability: check the opponent's reserves and bigger pieces they can move from the board
        """
        # TODO: benchmark evaluation cost before increasing search depth
        #TODO find time / space complexities
        #TODO consider last mover
        
        score = self._score_lines(board, reserves, player, opponent)
        score += self._score_reserves(reserves, player, opponent)
        score += self._score_threats(board, reserves, player, opponent)
        score += self._score_vulnerability(board, reserves, player, opponent)
        
        return score

    def _score_lines(self, board, reserves, player, opponent):
        """how close we are to a line vs them"""
        owners, sizes = top_view(board)
        lines = self._line_features(owners, sizes, player, opponent)
        line_base = 10
        size_bonus = 2
        win_bonus = 10000
        
        score = 0
       
        # get score for both sides then subtract
        # so we dont have to increment and decrement as we go
        for side in [player, opponent]:
            side_score = 0
            moves = None
            
            for line in lines:
                if side == player:
                    piece_sizes = line["own_sizes"] # ex. (0,2) means 2 peices 1 small, 1 large in this line
                    other_sizes = line["opponent_sizes"]
                else: # opponent
                    piece_sizes = line["opponent_sizes"]
                    other_sizes = line["own_sizes"]
                    
                count = len(piece_sizes)
                
                # nothing in line -> no points, skip to next line
                if count == 0:
                    continue 
                
                # opponent has no pieces in this line
                if len(other_sizes) == 0:
                    side_score += line_base ** count # exponential
                    for size in piece_sizes: # bigger the better!
                        side_score += size_bonus * (size + 1)
                        
                # if all but one, keep adding to the score, otherwise stop for that line,
                if count != WIN_LENGTH - 1:
                    continue
               
                # get cell we need to cover to win
                for r, c in line["cells"]:
                    if owners[r, c] != side:
                        target = (r, c)
                        break # we already know 3 filled cells so finding an empty means we can break
                
                # only generate moves if gives useful info, doing at top would waste compute
                if moves is None:
                    moves = get_valid_moves(board, reserves, side)
                    
                # aiming to fill the target cell (or cover)
                for move in moves:
                    if move.dest != target:
                        continue
                    
                    # dont wanna corrupt, so copy then try 
                    next_board, next_reserves = copy_state(board, reserves)
                    execute_move(next_board, next_reserves, side, move)
                    next_owners, _ = top_view(next_board)
                    
                    # moving from this line might leave a new gap
                    complete = True
                    for r, c in line["cells"]:
                        if next_owners[r, c] != side:
                            complete = False
                            break
                        
                    # uncovered their line so no good
                    if complete and check_winner(next_board, side) == side:
                        side_score += win_bonus
                        break
                        
            if side == player:
                score += side_score
            else:
                score -= side_score
        return score

    def _score_reserves(self, reserves, player, opponent):
        """what the pieces left in reserve are worth"""
        ours = self._reserve_counts(reserves, player)
        theirs = self._reserve_counts(reserves, opponent)
        score = 0
        for size in range(NUM_SIZES):
            # difference in peices weighted by size
            score += (size + 1) * (ours[size] - theirs[size])

        # spare large can cover a medium w/o moving anything off our line
        if ours[LARGE] > 0:
            score += 2
        if theirs[LARGE] > 0:
            score -= 2
            
        return score

    def _score_threats(self, board, reserves, player, opponent):
        """a threat is where theres two or more ways to win on the next move"""
        
        score = 0
        for side, bonus in [(player, 1000), (opponent, -1000)]:
            targets = set() # DISTINCT winning cells, if len > 1 theres a fork
            
            for move in self._winning_moves(board, reserves, side):
                targets.add(move.dest)
                
            # weight 2 ways to win same as >2
            if len(targets) >= 2:
                score += bonus
                
        return score

    def _score_vulnerability(self, board, reserves, player, opponent):
        """
        asks for each side
            for each top piece that side has: 
                1. can opponent cover?
                2. if we can move it, what would that uncover?
        """
        
        owners, sizes = top_view(board)
        score = 0
        
        # our piece at risk -> -1
        # theirs piece at risk -> +1
        for side, other, penalty in ((player, opponent, -1), (opponent, player, 1)):
            available = self._available_sizes(owners, sizes, reserves, other)
            
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if owners[r, c] != side:
                        continue
                    
                    # other side has a bigger piece they can put here
                    if self._can_cover(sizes[r, c], available):
                        score += penalty
                        
                    if ALLOW_MOVES:
                        below, _ = self._piece_below(board, r, c)
                        # moving this piece would uncover one of theirs
                        if below == other:
                            score += penalty
        return score

    def _line_features(self, owners, sizes, player, opponent):
        """
        return list of dicts, keys: cells, own_sizes, opponent_sizes, empty_count
        skip if obstacle
        """
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
