# Tactical ordering strategy

The agent uses these patterns to order alpha-beta moves. They are ordering hints, not forward pruning: every legal move remains searchable.

Notation: `B` = Blue, `R` = Brown, `S/M/L` = size, `.` = empty, and `x<Y` = `x` buried under top piece `Y`.

| Pattern | Small position | Strategy |
|---|---|---|
| Immediate win | `BS BM BL .` | Place or relocate onto the fourth square. Verify with `check_winner()` because an uncovering loss takes priority. |
| Forced block | `RS RM RL .` | Prefer moves leaving Brown no legal immediate win. A Blue Large on the endpoint is safer than a coverable Small. |
| Verified fork | `row: B X B .` and `column: B X B .` | `X` creates two endpoints. It is forced only when every Brown reply leaves an immediate Blue win. |
| Large intersection | `X = BL` | A Large intersection cannot be covered, making it the strongest fork candidate. It still requires exact verification. |
| Fake fork | `X = BS`, then Brown covers with `M` | Covering the shared intersection can break both apparent threats. |
| Pinned defender | `BS BM BL BS<RL` | Brown’s Large cannot move away safely because it reveals Blue’s row, but it may escape by covering another Blue piece in that row. |
| Poisoned cover | `RS RM RL RS<BL` | Moving Blue’s Large elsewhere reveals Brown’s win. Exact opponent-first winner checking puts this move last. |
| Uncover-and-recover | Move `BL` from `RS<BL` onto another `RS` in the revealed line | The source reveals Brown, but the destination breaks Brown’s completed line. Evaluate the final board, not only the source. |
| Self-stack relay | `BM BS<BL BS .` | Move the Large to the empty endpoint; the buried Blue Small preserves source control while the Large controls the destination. |
| Defensive gobble | `RS RM RS .`, cover `RM` with `BL` | Valuable when the cover removes a concrete threat. Ordinary covers receive no automatic priority. |
| Obstacle-aware control | `(2,1)` belongs to three viable lines while `(3,2)` may belong to one | Count only lines in `LINES[WIN_LENGTH]` that do not contain the obstacle. |
| Size superiority | A visible enemy Large can still cover our Medium | Check both reserves and movable top pieces when deciding whether a piece is secure. |
| Anti-fork defense | Opponent can occupy a dangerous line intersection | Prefer moves that remove all promising opponent fork candidates before the double threat exists. |

## Game phases

### Opening

- Build the obstacle-aware line index.
- Use viable-line incidence only as a tie-breaker; the center is not always strongest.
- Preserve Large pieces when otherwise equal, but never above a win or necessary defense.

### Midgame

- Search immediate wins and complete defenses first.
- Build intersecting threats around secure pieces.
- Reward defensive gobbles, safe relays, and source-and-destination line improvement.
- Verify only the strongest fork candidates to control runtime.

### Endgame

- Expect relocations, buried-piece reveals, and pinned covers.
- Put opponent-first reveal losses last.
- Recognize safe uncover-and-recover moves.
- Prefer forced sequences over static line appearance.

## Ordering pipeline

Cheap checks run at every alpha-beta node:

1. simulate the legal move and call `check_winner()`;
2. inspect destination owner and source-under-piece owner;
3. recognize covers, relays, piece size, and viable-line incidence;
4. keep original helper order as the final stable tie-breaker.

Expensive checks run selectively at the root:

1. determine whether a complete forced defense is required;
2. find geometric double-threat candidates;
3. verify at most the strongest fork candidates against every opponent reply;
4. check anti-fork defenses only when branching is bounded.

Final priority:

1. immediate wins;
2. complete defenses;
3. verified forks and anti-fork defenses;
4. previous-depth best move and promising tactical improvements;
5. ordinary legal moves;
6. immediate opponent wins and poisoned reveal losses.

The implementation assumes the COMP 424 rules: three immediately available reserve sizes, unrestricted legal board movement, one obstacle, complete stack visibility, and opponent-first line checking after a move.
