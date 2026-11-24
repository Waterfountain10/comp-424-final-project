import unittest

from agents.student_agent import StudentAgent
from constants import PLAYER_1, PLAYER_2
from helpers import (check_winner, copy_state, execute_move, get_valid_moves)
from tests.fixtures import opponent_threat_state, uncovering_risk_state


def has_immediate_win(board, reserves, player):
    """Return whether player has a legal move that wins immediately."""
    for move in get_valid_moves(board, reserves, player):
        next_board, next_reserves = copy_state(board, reserves)
        execute_move(next_board, next_reserves, player, move)
        if check_winner(next_board, player) == player:
            return True
    return False


class DefensiveTacticsTests(unittest.TestCase):
    def choose_player_one_move(self, state):
        board, reserves = state
        call_board, call_reserves = copy_state(board, reserves)
        move = StudentAgent().step(call_board, call_reserves, PLAYER_1, PLAYER_2)

        result_board, result_reserves = copy_state(board, reserves)
        execute_move(result_board, result_reserves, PLAYER_1, move)
        return move, result_board, result_reserves

    def test_blocks_opponents_immediate_win(self):
        board, reserves = opponent_threat_state()
        self.assertTrue(has_immediate_win(board, reserves, PLAYER_2))

        move, result_board, result_reserves = self.choose_player_one_move((board, reserves))

        self.assertNotEqual(
            check_winner(result_board, PLAYER_1),
            PLAYER_2,
            f"defensive move {move} lost immediately",
        )
        self.assertFalse(
            has_immediate_win(result_board, result_reserves, PLAYER_2),
            f"move {move} left an immediate opponent win",
        )

    def test_does_not_uncover_opponents_winning_line(self):
        move, result_board, _ = self.choose_player_one_move(uncovering_risk_state())

        self.assertNotEqual(
            check_winner(result_board, PLAYER_1),
            PLAYER_2,
            f"move {move} uncovered an opponent winning line",
        )


if __name__ == "__main__":
    unittest.main()
