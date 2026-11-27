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

## 2026-11-27 13:14 EST — iterative deepening to depth three

### Goal

Compare the fixed depth-two terminal search at commit `f657ae6` with iterative deepening that completes depths two and three while preserving the last fully completed move on timeout.

### Commands

```bash
git show f657ae6:agents/student_agent.py > /tmp/comp424_fixed_depth_agent.py
.venv/bin/python -m unittest tests.test_smoke tests.test_fixtures tests.test_agent_contract tests.test_agent_wins tests.test_agent_defense tests.test_agent_search -v
.venv/bin/python simulator.py --player_1 /tmp/comp424_fixed_depth_agent.py --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python simulator.py --player_1 student_agent --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python validate_submission.py agents/student_agent.py
```

### Results

| Agent | W | D | L | Score | Max step | Strikes | Forfeits |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed depth two (`f657ae6`) | 1 | 18 | 1 | 50.0% | 0.03 s | 0 | 0 |
| Iterative depths two and three | 18 | 1 | 1 | 92.5% | 0.23 s | 0 | 0 |

- The completed non-heuristic suite passed 15/15 tests.
- The validator passed 4/4 games against random with a 0.20-second maximum step.
- The iterative-deepening regression test confirmed that timeout returns the move from the last completed depth.
- Both benchmarks used seeds 0–9 and swapped seats, but greedy may break equal choices randomly, so W/D/L can vary slightly between runs.

### Debugging observation

The first depth-three version treated every forced loss as the same `-WIN_SCORE`. When all moves eventually lost, it could replace a depth-two defensive move with an immediate loss. Terminal scores now include remaining depth, preferring faster wins and slower losses. The forced-defense and exhaustive-minimax tests pass with this rule.

### Conclusion

One additional terminal-search ply produced a large improvement against greedy without approaching the time limit. Keep depth three enabled. The next optimizations should preserve these decisions while reducing node count or enabling deeper completed iterations.
