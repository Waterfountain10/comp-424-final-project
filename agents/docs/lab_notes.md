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

## 2026-11-27 16:52 EST — stack-aware tactical ordering

### Goal

Compare `student-agent-tactical-ordering` at commit `50ff698` with the iterative-deepening snapshot at `7aa32da`. The new version orders every legal alpha-beta child, verifies complete root defenses, selectively verifies three-ply forks, detects anti-fork moves, and ranks stack-aware source/destination effects. Jacob's heuristic remains disconnected and unchanged.

### Commands

```bash
git show 7aa32da:agents/student_agent.py > /tmp/student_agent_iterative_deepening.py
git show 50ff698:agents/student_agent.py > /tmp/student_agent_tactical_ordering.py

.venv/bin/python simulator.py --player_1 /tmp/student_agent_tactical_ordering.py --player_2 /tmp/student_agent_iterative_deepening.py --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python simulator.py --player_1 /tmp/student_agent_tactical_ordering.py --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python simulator.py --player_1 /tmp/student_agent_iterative_deepening.py --player_2 greedy_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python simulator.py --player_1 /tmp/student_agent_tactical_ordering.py --player_2 random_agent --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
.venv/bin/python validate_submission.py agents/student_agent.py
```

### Match results

| Match | Tactical W-D-L | Tactical score | Opponent W-D-L | Max tactical step | Strikes / forfeits |
|---|---:|---:|---:|---:|---:|
| Tactical vs iterative-deepening snapshot | 2-16-2 | 50.0% | 2-16-2 | 1.75 s | 0 / 0 |
| Tactical vs greedy | 15-5-0 | 87.5% | 0-5-15 | 1.75 s | 0 / 0 |
| Iterative-deepening snapshot vs greedy | 15-3-2 | 82.5% | 2-3-15 | 0.35 s | 0 / 0 |
| Tactical vs random | 20-0-0 | 100.0% | 0-0-20 | 1.25 s | 0 / 0 |

The direct match against the previous alpha-beta snapshot was balanced. Against the same greedy baseline and seed range, tactical ordering improved score from 82.5% to 87.5% and changed two losses into draws or wins. Greedy can choose randomly among tied moves, so repeated W/D/L results may vary.

### Search-cost experiment

Depth-three root searches were run from the ten seed-0-through-seed-9 opening positions. Tactical ordering was compared with the same alpha-beta implementation using raw `get_valid_moves` order.

| Ordering | Total nodes | Total runtime |
|---|---:|---:|
| Tactical | 23,194 | 3.000 s |
| Helper order | 26,810 | 2.356 s |

Tactical ordering reduced nodes by **13.5%**, but pattern scoring increased total runtime by **27.3%** on empty openings. This is an important limitation: the current value is tactical safety and better cutoffs, not raw opening speed. Exact checks are therefore restricted to the root and bounded candidate sets. The 1.75-second maximum indicates that some deeper iterations reached the internal deadline, but the last completed move remained legal and no tournament soft timeout occurred.

### Correctness and tactical validation

```text
28 non-heuristic tests passed in 6.357 seconds
validator: RESULT: PASS
validator games: W4 D0 L0
validator maximum step: 1.26 seconds
validator strikes: 0
validator forfeits: 0
```

The deterministic tests cover immediate wins, strong and weak blocks, genuine and fake forks, Large intersections, pinned defenders, poisoned covers, safe uncover-and-recover moves, self-stack relays, defensive gobbles, obstacle-aware incidence, board-top size availability, anti-fork defense, legal-move preservation, minimax equivalence, and node reduction.

### Conclusion

The feature preserves same-depth minimax values and all legal moves, passes strict validation, balances the previous iterative-deepening agent head-to-head, and improves the paired greedy score in this run. Its main cost is ordering overhead. Before raising search depth, optimize or cache root pattern analysis; do not expand exact fork verification deeper into the tree.

## 2026-11-28 05:08 EST — Jacob heuristic integration experiment

### Goal

Merge Jacob's heuristic implementation from `origin/main` (`1348535`) into tactical ordering, verify its acceptance tests, and determine whether activating it improves the tactical agent enough to merge into `main`.

### Integration

Commit `5294ad5` merges `origin/main` into `william-tactical-ordering`. The resolved `student_agent.py` retains tactical ordering and Jacob's implementations of:

- `evaluate`;
- `_score_lines`;
- `_score_reserves`;
- `_score_threats`;
- `_score_vulnerability`;
- the configurable `WEIGHTS` dictionary.

All six heuristic acceptance tests pass. The production search still returns zero at non-terminal depth-limit leaves unless an activation experiment proves beneficial.

### Experiment 1: evaluation at every depth-limit leaf

The temporary variant replaced the neutral depth-limit score with:

```python
return self.evaluate(board, reserves, player, opponent)
```

On opening seeds 0–2, every first move reached the 1.75-second internal deadline without completing depth two:

| Seed | Step time | Last completed depth | Nodes reached |
|---:|---:|---:|---:|
| 0 | 1.751 s | 0 | 449 |
| 1 | 1.750 s | 0 | 456 |
| 2 | 1.753 s | 0 | 457 |

The expensive line and threat components generate and simulate legal moves inside evaluation. Calling them at every leaf is therefore incompatible with the current search budget. This activation was rejected.

### Experiment 2: cached root tie-break evaluation

A second temporary variant kept terminal-only minimax but evaluated each root child once, caching the score across iterative-deepening iterations. It completed depth three on openings in roughly 0.50 seconds, so it was tested directly against the previous tactical-ordering snapshot.

```bash
.venv/bin/python simulator.py --player_1 /tmp/student_agent_tactical_heuristic.py --player_2 /tmp/student_agent_tactical_ordering.py --autoplay --autoplay_runs 20 --strict --seed 0 --quiet
```

| Agent | W | D | L | Score | Max step | Strikes / forfeits |
|---|---:|---:|---:|---:|---:|---:|
| Tactical + heuristic root tie-break | 3 | 9 | 8 | 37.5% | 0.97 s | 0 / 0 |
| Tactical ordering snapshot | 8 | 9 | 3 | 62.5% | 1.75 s | 0 / 0 |

The heuristic tie-break strongly preferred opening Large pieces: on seed 0 at `(0,0)`, the total scores were Small `34`, Medium `39`, and Large `45`. This conflicts with the tactical agent's reserve-efficient tie policy and performed substantially worse head-to-head.

A small reserve-weight pilot (`WEIGHTS["reserves"] = 8`) reduced the Large-opening preference but still scored only 37.5% over four direct games. It was also rejected; four games are not enough to claim a tuned weight improvement.

### Decision

- Keep Jacob's completed heuristic methods integrated and tested.
- Do **not** call the full evaluator at every leaf.
- Do **not** use the current evaluator as a root tie-break.
- Do **not** merge `william-tactical-ordering` into `main` based on these heuristic results.
- Future work should make a genuinely cheap static evaluator, then tune weights on separate training seeds before rerunning held-out paired matches.

The rejected activation variants existed only in `/tmp`; neither was committed.
