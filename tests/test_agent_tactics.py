import unittest

from agents.student_agent import StudentAgent
from constants import LARGE, MEDIUM, PLAYER_1, PLAYER_2, SMALL
from helpers import (Move, check_winner, copy_state, execute_move,
                     get_valid_moves, top_view)
from tests.fixtures import empty_state, immediate_win_state, uncovering_risk_state


def play(state, player, move):
    board, reserves = copy_state(*state)
    execute_move(board, reserves, player, move)
    return board, reserves


def large_fork_state(intersection_size=LARGE):
    board, reserves = empty_state()
    board[0, 1, SMALL] = PLAYER_1
    board[1, 0, MEDIUM] = PLAYER_1
    board[1, 2, SMALL] = PLAYER_1
    board[2, 1, MEDIUM] = PLAYER_1
    reserves[PLAYER_1, SMALL] = 1
    reserves[PLAYER_1, intersection_size] += 1
    reserves[PLAYER_2, :] = 3
    return board, reserves


def forced_block_state():
    board, reserves = empty_state()
    board[0, 0, SMALL] = PLAYER_2
    board[0, 1, MEDIUM] = PLAYER_2
    board[0, 2, LARGE] = PLAYER_2
    reserves[PLAYER_1, SMALL] = 1
    reserves[PLAYER_1, LARGE] = 1
    reserves[PLAYER_2, MEDIUM] = 1
    return board, reserves


def pinned_defender_state():
    board, reserves = empty_state()
    board[0, 0, SMALL] = PLAYER_1
    board[0, 1, MEDIUM] = PLAYER_1
    board[0, 2, LARGE] = PLAYER_1
    board[0, 3, SMALL] = PLAYER_1
    board[0, 3, LARGE] = PLAYER_2
    return board, reserves


class TacticalMoveOrderingTests(unittest.TestCase):
    def setUp(self):
        self.agent = StudentAgent()
        self.deadline = float("inf")

    def ordered(self, state, player=PLAYER_1, exact=True):
        return self.agent._ordered_children(
            *state, player, self.deadline, exact=exact
        )

    def test_ordering_preserves_every_legal_move_once(self):
        for state in (immediate_win_state(), forced_block_state(), uncovering_risk_state()):
            with self.subTest(state=state):
                expected = get_valid_moves(*state, PLAYER_1)
                actual = [child[0] for child in self.ordered(state)]
                self.assertEqual(len(actual), len(expected))
                self.assertEqual(set(actual), set(expected))

    def test_immediate_win_is_first(self):
        first = self.ordered(immediate_win_state())[0]
        self.assertEqual(first[0], Move(None, (0, 3), SMALL))
        self.assertEqual(first[3], PLAYER_1)

    def test_large_block_precedes_coverable_small_block(self):
        children = self.ordered(forced_block_state())
        moves = [child[0] for child in children]
        large_block = Move(None, (0, 3), LARGE)
        small_block = Move(None, (0, 3), SMALL)

        self.assertLess(moves.index(large_block), moves.index(small_block))
        self.assertTrue(children[moves.index(large_block)][4]["complete_defense"])
        self.assertFalse(children[moves.index(small_block)][4]["complete_defense"])

    def test_large_intersection_is_a_verified_fork(self):
        state = large_fork_state()
        move = Move(None, (1, 1), LARGE)
        after = play(state, PLAYER_1, move)

        self.assertTrue(
            self.agent._is_forced_fork(*after, PLAYER_1, self.deadline)
        )
        child = next(child for child in self.ordered(state) if child[0] == move)
        self.assertTrue(child[4]["large_intersection"])
        self.assertTrue(child[4]["verified_fork"])

    def test_small_intersection_is_a_fake_fork(self):
        state = large_fork_state(SMALL)
        move = Move(None, (1, 1), SMALL)
        after = play(state, PLAYER_1, move)

        self.assertFalse(
            self.agent._is_forced_fork(*after, PLAYER_1, self.deadline)
        )
        response = Move(None, (1, 1), MEDIUM)
        final = play(after, PLAYER_2, response)
        self.assertFalse(
            self.agent._has_winning_move(*final, PLAYER_1, self.deadline)
        )

    def test_pinned_defender_is_constrained_but_can_escape_along_line(self):
        state = pinned_defender_state()
        self.assertEqual(self.agent._pinned_defender_count(state[0], PLAYER_1), 1)

        unsafe = play(state, PLAYER_2, Move((0, 3), (1, 3), LARGE))
        escape = play(state, PLAYER_2, Move((0, 3), (0, 1), LARGE))
        self.assertEqual(check_winner(unsafe[0], PLAYER_2), PLAYER_1)
        self.assertEqual(check_winner(escape[0], PLAYER_2), 0)

    def test_poisoned_cover_is_last_but_recovery_is_safe(self):
        board, reserves = empty_state()
        board[2, 0, SMALL] = PLAYER_2
        board[2, 1, MEDIUM] = PLAYER_2
        board[2, 2, LARGE] = PLAYER_2
        board[2, 3, SMALL] = PLAYER_2
        board[2, 3, LARGE] = PLAYER_1
        children = self.ordered((board, reserves), exact=False)
        moves = [child[0] for child in children]
        poisoned = Move((2, 3), (1, 3), LARGE)
        recovery = Move((2, 3), (2, 0), LARGE)

        self.assertEqual(children[-1][3], PLAYER_2)
        self.assertLess(moves.index(recovery), moves.index(poisoned))
        recovery_child = children[moves.index(recovery)]
        self.assertEqual(recovery_child[3], 0)
        self.assertTrue(recovery_child[4]["safe_recovery"])

    def test_self_stack_relay_evaluates_source_and_destination(self):
        board, reserves = empty_state()
        board[1, 0, MEDIUM] = PLAYER_1
        board[1, 1, SMALL] = PLAYER_1
        board[1, 1, LARGE] = PLAYER_1
        board[1, 2, SMALL] = PLAYER_1
        move = Move((1, 1), (1, 3), LARGE)
        children = self.ordered((board, reserves), exact=False)
        child = next(child for child in children if child[0] == move)

        self.assertTrue(child[4]["self_relay"])
        self.assertEqual(child[3], PLAYER_1)
        self.assertEqual(children[0][0], move)

    def test_defensive_gobble_precedes_irrelevant_move(self):
        board, reserves = empty_state()
        board[0, 0, SMALL] = PLAYER_2
        board[0, 1, MEDIUM] = PLAYER_2
        board[0, 2, SMALL] = PLAYER_2
        reserves[PLAYER_1, LARGE] = 1
        reserves[PLAYER_2, SMALL] = 1
        children = self.ordered((board, reserves))
        moves = [child[0] for child in children]
        gobble = Move(None, (0, 1), LARGE)
        irrelevant = Move(None, (2, 2), LARGE)

        self.assertLess(moves.index(gobble), moves.index(irrelevant))
        self.assertTrue(children[moves.index(gobble)][4]["complete_defense"])

    def test_obstacle_aware_incidence_uses_only_viable_lines(self):
        board, reserves = empty_state(obstacle=(3, 3))
        self.agent._prepare_pattern_bank(board)

        self.assertEqual(len(self.agent._cell_lines[(2, 1)]), 3)
        self.assertEqual(len(self.agent._cell_lines[(3, 2)]), 1)
        self.assertFalse(
            any((3, 3) in line for line in self.agent._viable_lines)
        )

    def test_available_sizes_include_movable_board_tops(self):
        board, reserves = empty_state()
        board[2, 0, LARGE] = PLAYER_2
        board[1, 1, MEDIUM] = PLAYER_1
        owners, sizes = top_view(board)

        self.assertIn(
            LARGE,
            self.agent._available_sizes(owners, sizes, reserves, PLAYER_2),
        )

    def test_anti_fork_move_occupies_dangerous_intersection(self):
        board, reserves = empty_state()
        board[0, 1, SMALL] = PLAYER_2
        board[1, 0, MEDIUM] = PLAYER_2
        board[1, 2, SMALL] = PLAYER_2
        board[2, 1, MEDIUM] = PLAYER_2
        reserves[PLAYER_1, LARGE] = 1
        reserves[PLAYER_2, SMALL] = 1
        reserves[PLAYER_2, LARGE] = 1
        defense = Move(None, (1, 1), LARGE)
        children = self.ordered((board, reserves))
        moves = [child[0] for child in children]
        defense_child = children[moves.index(defense)]

        irrelevant = Move(None, (3, 0), LARGE)
        self.assertTrue(defense_child[4]["anti_fork"])
        self.assertLess(moves.index(defense), moves.index(irrelevant))


if __name__ == "__main__":
    unittest.main()
