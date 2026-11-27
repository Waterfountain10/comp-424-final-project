"""Student agent: edit ONLY this file."""
from agents.agent import Agent
from store import register_agent
from helpers import (Move, get_valid_moves, execute_move, check_winner,
                     check_endgame, copy_state, top_view, LINES)
from constants import *
import numpy as np
import time

SEARCH_DEPTH = 2
WIN_SCORE = 1_000_000

@register_agent("student_agent")          # do not change this string
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
        # ALLOW_MOVES and WIN_LENGTH (from constants) are the rule flags of this game.
        # helpers.get_valid_moves / check_winner already respect them; your own
        # move generator and evaluation function must too.
        
        # Keep a legal move ready before doing any tactical checks or search.
        moves = get_valid_moves(board, reserves, player)
        fallback = moves[0]

        wins = self._winning_moves(board, reserves, player)
        if wins:
            return wins[0]

        best_move = fallback
        best_score = -WIN_SCORE
        alpha, beta = -WIN_SCORE, WIN_SCORE
        for move in moves:
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, player, move)
            winner = check_winner(next_board, player)
            if winner == opponent:
                score = -WIN_SCORE
            else:
                score = self._minimax(next_board, next_reserves, opponent,
                                      player, opponent, SEARCH_DEPTH - 1,
                                      alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
        return best_move

    def _minimax(self, board, reserves, to_move, player, opponent, depth,
                 alpha, beta):
        """Return a terminal-only alpha-beta score from player's perspective."""
        if depth == 0:
            return 0

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
                score = self._minimax(next_board, next_reserves, 3 - to_move,
                                      player, opponent, depth - 1,
                                      alpha, beta)
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
        #TODO find time / space complexities
        #TODO consider last mover
        raise NotImplementedError

    def _score_lines(self, board, reserves, player, opponent):
        """how close we are to a line vs them"""
        #TODO
        raise NotImplementedError

    def _score_reserves(self, board, reserves, player, opponent):
        """what the pieces left in reserve are worth"""
        #TODO tune how much we value each size and if we want to take in any more context 
        raise NotImplementedError

    def _score_threats(self, board, reserves, player, opponent):
        """threats for us + them"""
        #TODO score threats
        raise NotImplementedError

    def _score_vulnerability(self, board, reserves, player, opponent):
        """pieces that could get covered or uncovered"""
        #TODO work out how vulnerable we are to them + vice versa
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
            features.append({
                "cells": cells,
                "own_sizes": tuple(own_sizes),
                "opponent_sizes": tuple(opponent_sizes),
                "empty_count": empty_count,
            })
        return features

    def _reserve_counts(self, reserves, player):
        """pieces left in reserve, small -> large"""
        counts = []
        for count in reserves[player]:
            counts.append(int(count)) # handle np int
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

    def _winning_moves(self, board, reserves, player):
        """moves that win, w/o uncovering a win for them"""
        wins = []
        for move in get_valid_moves(board, reserves, player):
            # try on copies, dont modify the actual position
            next_board, next_reserves = copy_state(board, reserves)
            execute_move(next_board, next_reserves, player, move)
            # checks their revealed line first, even if we made a line too
            if check_winner(next_board, player) == player:
                wins.append(move)
        return wins
