1. Add iterative deepening to search until time runs out 
2. Search most promising moves first to improve alpha-beta pruning
3. Cache repeated positions
4. Tune heuristic weights using results against given agents
5. optimize the search strategy + operations it uses
6. Detect forced wins by checking that every legal opponent reply still lets us win next move, without letting them win first
7. Detect opponent forks before they happen -> check whether one move can stop both threats, including covering pieces or moving a shared piece
8. Try different heuristic weights by game stage: useful lines and reserves early, threats and forced wins as the board fills
9. Test short winning sequences against common openings: match the obstacle and reserves, and return to normal search when the opponent deviates
10. Try adapting heuristic weights to repeated opponent choices within a game, while still checking their strongest replies
