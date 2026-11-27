import unittest

import numpy as np

from agents.student_agent import WIN_SCORE, StudentAgent
from constants import LARGE, MEDIUM, PLAYER_1, PLAYER_2, SMALL
from helpers import copy_state
from tests.fixtures import (
    empty_state,
    immediate_win_state,
    opponent_threat_state,
    uncovering_risk_state,
)


def line_state(player, row, obstacle=(3, 3)):
    """Return three visible pieces belonging to player in one row."""
    board, reserves = empty_state(obstacle)
    board[row, 0, SMALL] = player
    board[row, 1, MEDIUM] = player
    board[row, 2, LARGE] = player
    return board, reserves


class HeuristicEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.agent = StudentAgent()

    def test_evaluate_combines_component_scores(self):
        board, reserves = immediate_win_state()
        expected = sum(
            (
                self.agent._score_lines(board, reserves, PLAYER_1, PLAYER_2),
                self.agent._score_reserves(board, reserves, PLAYER_1, PLAYER_2),
                self.agent._score_threats(board, reserves, PLAYER_1, PLAYER_2),
                self.agent._score_vulnerability(board, reserves, PLAYER_1, PLAYER_2),
            )
        )

        self.assertEqual(
            self.agent.evaluate(board, reserves, PLAYER_1, PLAYER_2),
            expected,
        )

    def test_viable_line_scores_above_obstacle_blocked_line(self):
        viable_board, viable_reserves = line_state(PLAYER_1, row=0)
        blocked_board, blocked_reserves = line_state(PLAYER_1, row=3, obstacle=(3, 3))

        viable = self.agent._score_lines(
            viable_board, viable_reserves, PLAYER_1, PLAYER_2
        )
        blocked = self.agent._score_lines(
            blocked_board, blocked_reserves, PLAYER_1, PLAYER_2
        )
        opponent = self.agent._score_lines(
            viable_board, viable_reserves, PLAYER_2, PLAYER_1
        )

        self.assertGreater(viable, blocked)
        self.assertLess(opponent, 0)

    def test_large_reserve_scores_above_small_reserve(self):
        board, small_reserves = empty_state()
        large_reserves = small_reserves.copy()
        small_reserves[PLAYER_1, SMALL] = 1
        large_reserves[PLAYER_1, LARGE] = 1

        small_score = self.agent._score_reserves(
            board, small_reserves, PLAYER_1, PLAYER_2
        )
        large_score = self.agent._score_reserves(
            board, large_reserves, PLAYER_1, PLAYER_2
        )

        self.assertGreater(large_score, small_score)

    def test_threat_score_rewards_us_and_penalizes_opponent(self):
        own_board, own_reserves = immediate_win_state()
        opponent_board, opponent_reserves = opponent_threat_state()

        own_score = self.agent._score_threats(
            own_board, own_reserves, PLAYER_1, PLAYER_2
        )
        opponent_score = self.agent._score_threats(
            opponent_board, opponent_reserves, PLAYER_1, PLAYER_2
        )

        self.assertGreater(own_score, 0)
        self.assertLess(opponent_score, 0)

    def test_dangerous_covered_piece_scores_below_safe_stack(self):
        dangerous_board, reserves = uncovering_risk_state()
        safe_board = dangerous_board.copy()
        safe_board[2, 3, SMALL] = 0

        dangerous = self.agent._score_vulnerability(
            dangerous_board, reserves, PLAYER_1, PLAYER_2
        )
        safe = self.agent._score_vulnerability(safe_board, reserves, PLAYER_1, PLAYER_2)

        self.assertLess(dangerous, safe)

    def test_evaluate_is_bounded_and_does_not_mutate_state(self):
        board, reserves = immediate_win_state()
        original_board, original_reserves = copy_state(board, reserves)

        score = self.agent.evaluate(board, reserves, PLAYER_1, PLAYER_2)

        self.assertLess(abs(score), WIN_SCORE)
        np.testing.assert_array_equal(board, original_board)
        np.testing.assert_array_equal(reserves, original_reserves)


if __name__ == "__main__":
    unittest.main()
