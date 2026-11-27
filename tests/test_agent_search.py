import unittest

from agents.student_agent import SEARCH_DEPTH, WIN_SCORE, StudentAgent
from constants import PLAYER_1, PLAYER_2
from helpers import (check_winner, copy_state, execute_move, get_valid_moves,
                     new_game)
from tests.fixtures import (immediate_win_state, opponent_threat_state,
                            uncovering_risk_state)


def exhaustive_minimax(board, reserves, to_move, player, opponent, depth):
    """Return the terminal-only minimax score without pruning."""
    if depth == 0:
        return 0

    moves = get_valid_moves(board, reserves, to_move)
    if not moves:
        return -WIN_SCORE if to_move == player else WIN_SCORE

    scores = []
    for move in moves:
        next_board, next_reserves = copy_state(board, reserves)
        execute_move(next_board, next_reserves, to_move, move)
        winner = check_winner(next_board, to_move)
        if winner == player:
            score = WIN_SCORE
        elif winner == opponent:
            score = -WIN_SCORE
        else:
            score = exhaustive_minimax(
                next_board,
                next_reserves,
                3 - to_move,
                player,
                opponent,
                depth - 1,
            )
        scores.append(score)

    return max(scores) if to_move == player else min(scores)


def exhaustive_best_move(board, reserves, player, opponent, depth):
    """Return the first best root move from exhaustive minimax."""
    best_move = None
    best_score = -WIN_SCORE
    for move in get_valid_moves(board, reserves, player):
        next_board, next_reserves = copy_state(board, reserves)
        execute_move(next_board, next_reserves, player, move)
        winner = check_winner(next_board, player)
        if winner == player:
            score = WIN_SCORE
        elif winner == opponent:
            score = -WIN_SCORE
        else:
            score = exhaustive_minimax(
                next_board,
                next_reserves,
                opponent,
                player,
                opponent,
                depth - 1,
            )
        if score > best_score:
            best_score = score
            best_move = move
    return best_move


class AlphaBetaRegressionTests(unittest.TestCase):
    def setUp(self):
        self.agent = StudentAgent()

    def test_alpha_beta_scores_match_exhaustive_minimax(self):
        positions = [
            (*opponent_threat_state(), PLAYER_1),
            (*uncovering_risk_state(), PLAYER_1),
        ]
        for seed in range(3):
            board, reserves, _, _ = new_game(seed)
            positions.append((board, reserves, PLAYER_1))
            positions.append((board, reserves, PLAYER_2))

        for index, (board, reserves, player) in enumerate(positions):
            opponent = 3 - player
            with self.subTest(position=index, player=player):
                expected = exhaustive_minimax(
                    board, reserves, player, player, opponent, SEARCH_DEPTH
                )
                actual = self.agent._minimax(
                    board,
                    reserves,
                    player,
                    player,
                    opponent,
                    SEARCH_DEPTH,
                    -WIN_SCORE,
                    WIN_SCORE,
                    float("inf"),
                )
                self.assertEqual(actual, expected)

    def test_selected_moves_match_exhaustive_minimax(self):
        positions = [
            immediate_win_state(),
            opponent_threat_state(),
            uncovering_risk_state(),
        ]
        for seed in range(3):
            board, reserves, _, _ = new_game(seed)
            positions.append((board, reserves))

        for index, (board, reserves) in enumerate(positions):
            with self.subTest(position=index):
                expected = exhaustive_best_move(
                    board, reserves, PLAYER_1, PLAYER_2, SEARCH_DEPTH
                )
                call_board, call_reserves = copy_state(board, reserves)
                actual = self.agent.step(
                    call_board, call_reserves, PLAYER_1, PLAYER_2
                )
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
