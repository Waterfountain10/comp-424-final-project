# Search runbook

Run commands from the repository root. Use the Python 3.11 virtual environment:

```bash
.venv/bin/python --version
```

## Test

Run every unit and tactical test:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Expected after the heuristic is implemented: all 21 tests pass. Until then, the six heuristic tests fail with `NotImplementedError` while the existing 15 tests pass.

Run only the search-related tests:

```bash
.venv/bin/python -m unittest tests.test_agent_contract tests.test_agent_wins tests.test_agent_defense tests.test_agent_search -v
```

Run only Jacob's heuristic acceptance tests:

```bash
.venv/bin/python -m unittest tests.test_agent_heuristic -v
```

Run the official submission checks and sandbox games:

```bash
.venv/bin/python validate_submission.py agents/student_agent.py
```

Expected: `RESULT: PASS`, zero strikes, zero forfeits, and no timing warning. macOS may warn that it cannot enforce the Linux memory limit.

## Run

Run one reproducible text game:

```bash
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --seed 0
```

Watch the same game in the GUI:

```bash
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --seed 0 --display --display_delay 0.5
```

Run paired games against both supplied baselines:

```bash
.venv/bin/python simulator.py --player_1 student_agent --player_2 random_agent --autoplay --autoplay_runs 20 --strict --seed 0
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0
```

Record W/D/L, results by seat, mean and maximum move time, strikes, and forfeits.

## Debug

Reproduce a failure with the seed printed by the simulator:

```bash
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --seed <seed>
```

Run one failing test directly:

```bash
.venv/bin/python -m unittest tests.test_agent_defense.DefensiveTacticsTests.test_blocks_opponents_immediate_win -v
```

Check the local changes before committing:

```bash
git diff --check
git diff
git status --short
```
