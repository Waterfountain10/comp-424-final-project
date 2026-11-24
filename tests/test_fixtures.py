import unittest

from constants import PLAYER_1, PLAYER_2
from helpers import check_move_validity, check_winner, copy_state, execute_move
from tests.fixtures import (DANGEROUS_UNCOVER, IMMEDIATE_WIN, OPPONENT_WIN,
                            immediate_win_state, opponent_threat_state,
                            uncovering_risk_state)


class TacticalFixtureTests(unittest.TestCase):
    def assert_move_wins(self, state, player, move):
        board, reserves = state
        self.assertEqual(check_winner(board, 3 - player), 0)
        self.assertTrue(check_move_validity(board, reserves, player, move))

        result_board, result_reserves = copy_state(board, reserves)
        execute_move(result_board, result_reserves, player, move)
        self.assertEqual(check_winner(result_board, player), player)

    def test_immediate_win_fixture(self):
        self.assert_move_wins(immediate_win_state(), PLAYER_1, IMMEDIATE_WIN)

    def test_opponent_threat_fixture(self):
        self.assert_move_wins(opponent_threat_state(), PLAYER_2, OPPONENT_WIN)

    def test_uncovering_fixture_awards_opponent_the_win(self):
        board, reserves = uncovering_risk_state()
        self.assertEqual(check_winner(board, PLAYER_2), 0)
        self.assertTrue(check_move_validity(board, reserves, PLAYER_1, DANGEROUS_UNCOVER))

        result_board, result_reserves = copy_state(board, reserves)
        execute_move(result_board, result_reserves, PLAYER_1, DANGEROUS_UNCOVER)
        self.assertEqual(check_winner(result_board, PLAYER_1), PLAYER_2)


if __name__ == "__main__":
    unittest.main()
