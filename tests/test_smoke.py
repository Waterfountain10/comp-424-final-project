import unittest

from constants import BOARD_SIZE, NUM_SIZES, OBSTACLE
from helpers import get_valid_moves, new_game


class FrameworkSmokeTests(unittest.TestCase):
    def test_new_game_has_expected_shape_and_legal_openings(self):
        board, reserves, obstacle, _ = new_game(seed=0)

        self.assertEqual(board.shape, (BOARD_SIZE, BOARD_SIZE, NUM_SIZES))
        self.assertEqual(reserves.shape, (3, NUM_SIZES))
        self.assertTrue((board[obstacle] == OBSTACLE).all())
        self.assertTrue(get_valid_moves(board, reserves, player=1))
        self.assertTrue(get_valid_moves(board, reserves, player=2))


if __name__ == "__main__":
    unittest.main()
