import types
import unittest
from unittest.mock import patch

from agents.student_agent import (_SearchTimeout, SEARCH_BOUND, SEARCH_DEPTH,
                                  WIN_SCORE, StudentAgent)
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
        score = WIN_SCORE + depth
        return -score if to_move == player else score

    scores = []
    for move in moves:
        next_board, next_reserves = copy_state(board, reserves)
        execute_move(next_board, next_reserves, to_move, move)
        winner = check_winner(next_board, to_move)
        if winner == player:
            score = WIN_SCORE + depth
        elif winner == opponent:
            score = -WIN_SCORE - depth
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


def exhaustive_move_score(board, reserves, move, player, opponent, depth):
    """Return one root move's score under exhaustive minimax."""
    next_board, next_reserves = copy_state(board, reserves)
    execute_move(next_board, next_reserves, player, move)
    winner = check_winner(next_board, player)
    if winner == player:
        return WIN_SCORE + depth
    if winner == opponent:
        return -WIN_SCORE - depth
    return exhaustive_minimax(
        next_board,
        next_reserves,
        opponent,
        player,
        opponent,
        depth - 1,
    )


def exhaustive_best_score(board, reserves, player, opponent, depth):
    """Return the best root score under exhaustive minimax."""
    return max(
        exhaustive_move_score(board, reserves, move, player, opponent, depth)
        for move in get_valid_moves(board, reserves, player)
    )


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
                    -SEARCH_BOUND,
                    SEARCH_BOUND,
                    float("inf"),
                )
                self.assertEqual(actual, expected)

    def test_selected_moves_are_exhaustive_minimax_optimal(self):
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
                expected_score = exhaustive_best_score(
                    board, reserves, PLAYER_1, PLAYER_2, SEARCH_DEPTH
                )
                actual_move = self.agent._search_root(
                    board,
                    reserves,
                    PLAYER_1,
                    PLAYER_2,
                    SEARCH_DEPTH,
                    float("inf"),
                )
                actual_score = exhaustive_move_score(
                    board,
                    reserves,
                    actual_move,
                    PLAYER_1,
                    PLAYER_2,
                    SEARCH_DEPTH,
                )
                self.assertEqual(actual_score, expected_score)

    def test_tactical_ordering_reduces_depth_three_opening_nodes(self):
        board, reserves, _, _ = new_game(seed=0)
        ordered = StudentAgent()
        ordered._search_root(
            board, reserves, PLAYER_1, PLAYER_2, 3, float("inf")
        )

        def helper_order_children(
            agent,
            state_board,
            state_reserves,
            to_move,
            deadline,
            preferred_move=None,
            exact=False,
        ):
            children = []
            for move in get_valid_moves(state_board, state_reserves, to_move):
                next_board, next_reserves = copy_state(state_board, state_reserves)
                execute_move(next_board, next_reserves, to_move, move)
                winner = check_winner(next_board, to_move)
                children.append((move, next_board, next_reserves, winner, {}))
            return children

        unordered = StudentAgent()
        unordered._ordered_children = types.MethodType(
            helper_order_children, unordered
        )
        unordered._search_root(
            board, reserves, PLAYER_1, PLAYER_2, 3, float("inf")
        )

        self.assertLess(ordered.search_nodes, unordered.search_nodes)

    def test_iterative_deepening_keeps_last_completed_move(self):
        board, reserves, _, _ = new_game(seed=0)
        moves = get_valid_moves(board, reserves, PLAYER_1)

        with patch.object(self.agent, "_winning_moves", return_value=[]), patch.object(
            self.agent,
            "_search_root",
            side_effect=(moves[0], moves[1], _SearchTimeout()),
        ), patch("agents.student_agent.MAX_SEARCH_DEPTH", 4):
            actual = self.agent.step(board, reserves, PLAYER_1, PLAYER_2)

        self.assertEqual(actual, moves[1])
        self.assertEqual(self.agent.last_completed_depth, 3)


if __name__ == "__main__":
    unittest.main()
