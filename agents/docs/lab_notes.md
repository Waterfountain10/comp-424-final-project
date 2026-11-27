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

## 2026-11-27 — alpha-beta equivalence regression (commit `c469db2`)

Automated in GitHub Actions on Python 3.11, run [46048620988](https://github.com/Waterfountain10/comp-424-final-project/actions/runs/46048620988).

- New exhaustive-minimax equivalence checks: **3/3 passed** (1.444 s).
- Complete original+new unittest suite: **15/15 passed** (1.593 s).
- Official validator: **RESULT: PASS**.
- Scenarios: deterministic starting seeds 0 and 1, tactical win/defense/uncovering positions, both seats, depths 1 and 2.
- Tests include matching root moves under the same tie-break and fewer explored nodes for alpha-beta on a reference position.

These checks establish the correctness of terminal-only alpha-beta at the tested depths; they do **not** establish strategic win rates.

## 2026-11-27 — iterative deepening experiment

Implementation: run complete searches at depths 1 through 4, subject to a 0.25 s safety margin below the 2-second move limit. Preserve the last *fully completed* depth's move when deeper search times out; otherwise use the first legal move as fallback. Terminal-only leaves still score 0 pending the heuristic.

Planned verification:
- Forced timeout after depths 1 and 2 completes returns depth 2's move.
- Timeout before completing depth 1 returns a legal fallback.
- Limiting iterative deepening to depth 1 or 2 matches the exhaustive reference at the same depth.
- Run automated tests, official validation, and a small paired greedy-agent smoke benchmark under strict timing.

**Observed results (Python 3.11 / GitHub Actions):**
- Initial iterative deepening version (commit `b08241b`, run [46048780111](https://github.com/Waterfountain10/comp-424-final-project/actions/runs/46048780111)): all 6 new search tests passed, but the full suite failed 1/18 (defensive immediate-win regression). Validation and paired benchmark were skipped.
- Diagnosis: terminal-only search assigned the same `-1,000,000` to immediate losses and later forced losses. At deeper horizons a tie could replace a safe earlier-depth move with an immediate losing move.
- Correction (commit `f79ca0a`): add a small mate-distance preference inside terminal win/loss scoring, while keeping non-terminal leaves neutral. Update the exhaustive reference to verify the changed scores.
- Corrected version, run [46048935462](https://github.com/Waterfountain10/comp-424-final-project/actions/runs/46048935462): **6/6 search tests passed; 18/18 full-suite tests passed; official submission validation passed**.
- The paired greedy benchmark in this run was still running when these notes were updated; record W/D/L after completion. This is a smoke experiment, not a meaningful win-rate estimate.
