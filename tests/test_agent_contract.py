import unittest

from agents.student_agent import StudentAgent
from constants import PLAYER_1, PLAYER_2
from helpers import Move, check_move_validity, copy_state, new_game
from tests.fixtures import (immediate_win_state, opponent_threat_state,
                            uncovering_risk_state)


class AgentContractTests(unittest.TestCase):
    def assert_returns_legal_move(self, board, reserves, player):
        original_board, original_reserves = copy_state(board, reserves)
        call_board, call_reserves = copy_state(board, reserves)
        move = StudentAgent().step(call_board, call_reserves, player, 3 - player)

        self.assertIsInstance(move, Move)
        self.assertTrue(
            check_move_validity(original_board, original_reserves, player, move),
            f"agent returned illegal move for Player {player}: {move}",
        )

    def test_legal_opening_moves_in_both_seats(self):
        for seed in range(5):
            for player in (PLAYER_1, PLAYER_2):
                with self.subTest(seed=seed, player=player):
                    board, reserves, _, _ = new_game(seed)
                    self.assert_returns_legal_move(board, reserves, player)

    def test_legal_moves_in_tactical_positions(self):
        positions = (
            immediate_win_state(),
            opponent_threat_state(),
            uncovering_risk_state(),
        )
        for index, (board, reserves) in enumerate(positions):
            with self.subTest(position=index):
                self.assert_returns_legal_move(board, reserves, PLAYER_1)


if __name__ == "__main__":
    unittest.main()
