import unittest

from agents.student_agent import StudentAgent
from constants import PLAYER_1, PLAYER_2
from helpers import check_winner, copy_state, execute_move
from tests.fixtures import board_move_win_state, immediate_win_state


class ImmediateWinTests(unittest.TestCase):
    def assert_agent_takes_win(self, state):
        board, reserves = state
        call_board, call_reserves = copy_state(board, reserves)
        move = StudentAgent().step(call_board, call_reserves, PLAYER_1, PLAYER_2)

        result_board, result_reserves = copy_state(board, reserves)
        execute_move(result_board, result_reserves, PLAYER_1, move)
        self.assertEqual(
            check_winner(result_board, PLAYER_1),
            PLAYER_1,
            f"agent ignored an immediate win and chose {move}",
        )

    def test_takes_immediate_placement_win(self):
        self.assert_agent_takes_win(immediate_win_state())

    def test_takes_immediate_board_move_win(self):
        self.assert_agent_takes_win(board_move_win_state())


if __name__ == "__main__":
    unittest.main()
