"""Deterministic board positions shared by agent acceptance tests."""

import numpy as np

from constants import (BOARD_SIZE, EMPTY, LARGE, MEDIUM, NUM_SIZES, OBSTACLE,
                       PLAYER_1, PLAYER_2, SMALL)
from helpers import Move


def empty_state(obstacle=(3, 3)):
    """Return an otherwise empty board and empty reserves."""
    board = np.full((BOARD_SIZE, BOARD_SIZE, NUM_SIZES), EMPTY, dtype=np.int8)
    board[obstacle[0], obstacle[1], :] = OBSTACLE
    reserves = np.zeros((3, NUM_SIZES), dtype=np.int8)
    return board, reserves


def immediate_win_state():
    """Player 1 can complete row 0 by placing at (0, 3)."""
    board, reserves = empty_state()
    board[0, 0, SMALL] = PLAYER_1
    board[0, 1, MEDIUM] = PLAYER_1
    board[0, 2, LARGE] = PLAYER_1
    reserves[PLAYER_1, SMALL] = 1
    return board, reserves


def board_move_win_state():
    """Player 1 can complete row 0 by moving its small from (1, 0)."""
    board, reserves = empty_state()
    board[0, 0, SMALL] = PLAYER_1
    board[0, 1, MEDIUM] = PLAYER_1
    board[0, 2, LARGE] = PLAYER_1
    board[1, 0, SMALL] = PLAYER_1
    return board, reserves


def opponent_threat_state():
    """Player 2 threatens to complete row 1; Player 1 can occupy (1, 3)."""
    board, reserves = empty_state()
    board[1, 0, SMALL] = PLAYER_2
    board[1, 1, MEDIUM] = PLAYER_2
    board[1, 2, LARGE] = PLAYER_2
    reserves[PLAYER_1, MEDIUM] = 1
    reserves[PLAYER_2, SMALL] = 1
    return board, reserves


def uncovering_risk_state():
    """Moving Player 1's medium from (2, 3) uncovers Player 2's row."""
    board, reserves = empty_state()
    board[2, 0, SMALL] = PLAYER_2
    board[2, 1, MEDIUM] = PLAYER_2
    board[2, 2, LARGE] = PLAYER_2
    board[2, 3, SMALL] = PLAYER_2
    board[2, 3, MEDIUM] = PLAYER_1
    reserves[PLAYER_1, SMALL] = 1
    return board, reserves


IMMEDIATE_WIN = Move(None, (0, 3), SMALL)
BOARD_MOVE_WIN = Move((1, 0), (0, 3), SMALL)
OPPONENT_WIN = Move(None, (1, 3), SMALL)
DANGEROUS_UNCOVER = Move((2, 3), (3, 0), MEDIUM)
