# Minimax with alpha beta pruning

## Strategy

Replace random choices with a short search of possible moves.
Assume the opponent chooses their strongest response.
Choose the move with the best outcome under that response.

## Pruning

Stop exploring a branch once it cannot improve the decision.
Alpha-beta pruning saves work while preserving the minimax result at the same depth.

## Heuristics

Prioritize wins and avoid losses.
Reward progress toward a winning line and subtract the opponent's progress.
Give smaller bonuses for strong visible pieces and useful reserve pieces.
Careful: Only visible pieces count toward lines, blocked squares cant contribute.

## Constraints

Respect stacking rules and the pieces revealed by a move.
A move that leaves the opponent with a winning line loses, even if we also form one.
Finish within the two-second limit and keep a legal fallback ready.
Start with a fixed search depth (see next steps)

## Validation

Check immediate wins, defensive moves and moves that uncover opposing pieces.
Compare results with plain minimax to confirm pruning preserves the search result.
Test both seats against the supplied agents and check timing and legality.
