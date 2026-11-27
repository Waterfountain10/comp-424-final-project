"""Regression checks: alpha-beta must match exhaustive terminal minimax."""

import time
import unittest
from unittest.mock import patch

from agents.student_agent import StudentAgent, WIN_SCORE, _SearchTimeout
from constants import PLAYER_1, PLAYER_2
from helpers import (
    check_winner, copy_state, execute_move, get_valid_moves, new_game,
)
from tests.fixtures import (
    board_move_win_state, immediate_win_state, opponent_threat_state,
    uncovering_risk_state,
)


def exhaustive_minimax(board, reserves, to_move, player, opponent, depth, nodes=None):
    """Exact reference for our current terminal-only, depth-limited scoring."""
    if nodes is not None:
        nodes[0] += 1
    if depth == 0:
        return 0
    moves = get_valid_moves(board, reserves, to_move)
    if not moves:
        return -WIN_SCORE if to_move == player else WIN_SCORE
    scores = []
    for move in moves:
        child_board, child_reserves = copy_state(board, reserves)
        execute_move(child_board, child_reserves, to_move, move)
        winner = check_winner(child_board, to_move)
        if winner == player:
            score = WIN_SCORE
        elif winner == opponent:
            score = -WIN_SCORE
        else:
            score = exhaustive_minimax(
                child_board, child_reserves, 3 - to_move,
                player, opponent, depth - 1, nodes,
            )
        scores.append(score)
    return max(scores) if to_move == player else min(scores)


def exhaustive_root(board, reserves, player, depth):
    """Use the same first-win and first-equal-score tie-break rules as step()."""
    opponent = 3 - player
    moves = get_valid_moves(board, reserves, player)
    for move in moves:
        child_board, child_reserves = copy_state(board, reserves)
        execute_move(child_board, child_reserves, player, move)
        if check_winner(child_board, player) == player:
            return move

    best_move, best_score = moves[0], -WIN_SCORE
    for move in moves:
        child_board, child_reserves = copy_state(board, reserves)
        execute_move(child_board, child_reserves, player, move)
        winner = check_winner(child_board, player)
        if winner == opponent:
            score = -WIN_SCORE
        else:
            score = exhaustive_minimax(
                child_board, child_reserves, opponent, player,
                opponent, depth - 1,
            )
        if score > best_score:
            best_score, best_move = score, move
    return best_move


class AlphaBetaEquivalenceTests(unittest.TestCase):
    def test_subtree_scores_match_exhaustive_minimax(self):
        positions = [
            new_game(seed=0)[:2],
            new_game(seed=1)[:2],
            immediate_win_state(),
            board_move_win_state(),
            opponent_threat_state(),
            uncovering_risk_state(),
        ]
        agent = StudentAgent()
        for index, (board, reserves) in enumerate(positions):
            for to_move in (PLAYER_1, PLAYER_2):
                for depth in (1, 2):
                    with self.subTest(position=index, to_move=to_move, depth=depth):
                        reference = exhaustive_minimax(
                            board, reserves, to_move, PLAYER_1, PLAYER_2, depth
                        )
                        actual = agent._minimax(
                            board, reserves, to_move, PLAYER_1, PLAYER_2,
                            depth, -WIN_SCORE, WIN_SCORE, float("inf"),
                        )
                        self.assertEqual(actual, reference)

    def test_root_move_matches_exhaustive_minimax(self):
        for seed in (0, 1):
            board, reserves = new_game(seed)[:2]
            for player in (PLAYER_1, PLAYER_2):
                with self.subTest(seed=seed, player=player):
                    expected = exhaustive_root(board, reserves, player, depth=2)
                    call_board, call_reserves = copy_state(board, reserves)
                    # Hold the new iterative agent at the legacy depth-2
                    # limit to compare identical search horizons.
                    with patch("agents.student_agent.MAX_SEARCH_DEPTH", 2):
                        actual = StudentAgent().step(
                            call_board, call_reserves, player, 3 - player
                        )
                    self.assertEqual(actual, expected)

    def test_alpha_beta_reduces_work_without_changing_score(self):
        board, reserves = new_game(seed=0)[:2]
        nodes = [0]
        reference = exhaustive_minimax(
            board, reserves, PLAYER_1, PLAYER_1, PLAYER_2, 2, nodes
        )
        agent = StudentAgent()
        actual_calls = [0]
        original = agent._minimax

        def counted(*args, **kwargs):
            actual_calls[0] += 1
            return original(*args, **kwargs)

        agent._minimax = counted
        score = agent._minimax(
            board, reserves, PLAYER_1, PLAYER_1, PLAYER_2,
            2, -WIN_SCORE, WIN_SCORE, float("inf"),
        )
        self.assertEqual(score, reference)
        self.assertLess(
            actual_calls[0], nodes[0],
            "Expected alpha-beta to prune some branches at depth 2",
        )


class IterativeDeepeningTests(unittest.TestCase):
    def test_timeout_returns_last_completed_depth(self):
        board, reserves = new_game(seed=0)[:2]
        moves = get_valid_moves(board, reserves, PLAYER_1)
        agent = StudentAgent()

        with patch.object(agent, "_winning_moves", return_value=[]), \
             patch.object(agent, "_search_root", side_effect=[
                 (moves[0], 0), (moves[1], 0), _SearchTimeout()
             ]) as search:
            selected = agent.step(board, reserves, PLAYER_1, PLAYER_2)

        self.assertEqual(selected, moves[1])
        self.assertEqual([call.args[4] for call in search.call_args_list],
                         [1, 2, 3])

    def test_timeout_before_first_completed_depth_uses_fallback(self):
        board, reserves = new_game(seed=1)[:2]
        fallback = get_valid_moves(board, reserves, PLAYER_1)[0]
        agent = StudentAgent()

        with patch.object(agent, "_winning_moves", return_value=[]), \
             patch.object(agent, "_search_root", side_effect=_SearchTimeout()):
            selected = agent.step(board, reserves, PLAYER_1, PLAYER_2)
        self.assertEqual(selected, fallback)

    def test_completed_depth_one_matches_reference(self):
        board, reserves = new_game(seed=2)[:2]
        expected = exhaustive_root(board, reserves, PLAYER_1, depth=1)
        with patch("agents.student_agent.MAX_SEARCH_DEPTH", 1):
            actual = StudentAgent().step(board, reserves, PLAYER_1, PLAYER_2)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
