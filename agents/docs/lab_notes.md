# Lab notes

## 2026-11-27 11:37 EST — random selection vs terminal alpha-beta

### Goal

Measure the behavior change from the random `student_agent` at commit `5c755df` to the terminal-only alpha-beta agent at commit `926e943`. Both versions played the same 20 seat-swapped games against `greedy_agent` using seeds 0–9 and strict tournament timing.

### Commands

```bash
git show 5c755df:agents/student_agent.py > /tmp/comp424_random_student.py
.venv/bin/python simulator.py --player_1 /tmp/comp424_random_student.py --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
```

### Results

| Agent | W | D | L | Score | P1 | P2 | Max step | Strikes | Forfeits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Random student (`5c755df`) | 0 | 0 | 20 | 0.0% | 0/10 | 0/10 | 0.00 s | 0 | 0 |
| Terminal alpha-beta (`926e943`) | 1 | 17 | 2 | 47.5% | 1/10 | 0/10 | 0.04 s | 0 | 0 |

The search agent improved by 47.5 percentage points and reduced losses from 20 to 2. Most improved games became draws because every safe non-terminal leaf still receives a score of zero.

### Single-game observation

```bash
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --seed 0
```

The student agent played legally with no strikes but lost by line after 86 plies. It repeatedly moved equally scored pieces between similar positions. This shows that terminal search avoids many immediate losses, but it has no strategic preference between safe non-terminal positions.

### Next hypothesis

Connecting Jacob's heuristic to the depth-limit leaf score should reduce repetitive draws and improve wins against greedy. After that, test iterative deepening, tactical move ordering, and fork detection as separate changes against this fixed-seed baseline.

## 2026-11-27 12:51 EST — alpha-beta regression test

### Goal

Confirm that alpha-beta pruning preserves the scores and selected moves of exhaustive terminal-only minimax at the same depth.

### Commands

```bash
.venv/bin/python -m unittest tests.test_agent_search -v
.venv/bin/python -m unittest tests.test_smoke tests.test_fixtures tests.test_agent_contract tests.test_agent_wins tests.test_agent_defense tests.test_agent_search -v
```

### Results

- Alpha-beta scores matched exhaustive minimax on eight deterministic positions.
- Selected root moves matched exhaustive minimax on six deterministic positions.
- The dedicated regression suite passed 2/2 tests in 0.567 seconds.
- The completed non-heuristic suite passed 14/14 tests in 0.624 seconds.

### Conclusion

The current pruning implementation changes search cost without changing terminal-only minimax decisions on the regression corpus. Keep this test as a correctness gate for iterative deepening, move ordering, and caching.
