# Baseline search runbook

## Current flow

1. `World` checks whether the game is over and gives the agent copies of the board and reserves.
2. `StudentAgent.step` must return one legal `Move` within two seconds.
3. Search should generate moves with `get_valid_moves`, copy states with `copy_state`, and apply moves with `execute_move`.
4. After every simulated move, `check_winner(next_board, last_mover)` handles normal wins and the opponent-first uncovering rule.
5. The referee checks time and legality, applies the move, and records times, strikes, and the result.

## Missing baseline pieces

- Replace the random move in `step` with a legal fallback and fixed-depth alpha-beta search.
- Add maximizing and minimizing recursion with terminal win/loss scores.
- Stop search before the two-second limit and return the fallback if search is incomplete.
- Handle positions with no legal moves.
- Use a neutral leaf score until Jacob's evaluation functions are complete, then connect `evaluate` in a separate integration commit.
- Order immediate wins and safe defenses before ordinary moves in a separate feature.

## Test runbook

Run from the repository root with the Python 3.11 virtual environment active.

| Check | Command | Expected baseline-search result |
|---|---|---|
| Unit and tactical tests | `python3.11 -m unittest discover -s tests -v` | All 11 tests pass. |
| Official validator | `python3.11 validate_submission.py agents/student_agent.py` | `RESULT: PASS`, zero strikes or forfeits, and no timing warning. |
| Random baseline | `python3.11 simulator.py --player_1 student_agent --player_2 random_agent --autoplay --autoplay_runs 20 --strict` | Completes all 20 games in both seats with zero strikes and forfeits; record W/D/L and move times. |
| Greedy baseline | `python3.11 simulator.py --player_1 student_agent --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict` | Completes all 20 games in both seats with zero strikes and forfeits; record W/D/L and move times. |

Passing the validator establishes compatibility, not playing strength. Random and greedy W/D/L are measurements rather than unit-test pass conditions. On macOS, `--strict` may warn that some Linux sandbox protections are unavailable.
