# Example diagnostic log from an archived result fixture

This example was produced **offline** from a V3 previously recorded 10-ply experiment. It is NOT a new genuine paceval execution, not a completed chess game and not evidence of a correct tactical diagnosis. In production, every completed game gets its own report and appends to `sessions/learning_log.md`.


## Game 1 | 2026-11-15T13:02:33Z

Game folder: `results/v3_ab_depth4_q1_10ply`  
Opening control: `offline-analysis`  
Result: *****; termination: **legacy_unclassified**; played plies: 10  
Observed search nodes (sum of recorded root searches): 2898556. Total paceval graph-point counter: 285627. These counts do not measure chess strength.  
Diagnostic summary: score reversals=7, near-tied root choices=4, recurring board states=0, captures=0.

### Review candidates (not automatically trained)

- **CLOSE_ROOT_CHOICES**, ply 1 e2e3: The top two candidate scores differ by at most 12 cp.  Suggested experiment: Test depth stability and evaluate alternative lines. Add controlled opening diversity rather than changing score coefficients from this signal alone.
- **CLOSE_ROOT_CHOICES**, ply 2 e7e6: The top two candidate scores differ by at most 12 cp.  Suggested experiment: Test depth stability and evaluate alternative lines. Add controlled opening diversity rather than changing score coefficients from this signal alone.
- **EVALUATION_REVERSAL**, ply 4 d8f6: White-perspective root score changed from 120 cp to -144 cp across adjacent turns; this is NOT independent proof of a blunder.  Suggested experiment: Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights.
- **EVALUATION_REVERSAL**, ply 5 f1c4: White-perspective root score changed from -144 cp to 146 cp across adjacent turns; this is NOT independent proof of a blunder.  Suggested experiment: Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights.
- **CLOSE_ROOT_CHOICES**, ply 5 f1c4: The top two candidate scores differ by at most 12 cp.  Suggested experiment: Test depth stability and evaluate alternative lines. Add controlled opening diversity rather than changing score coefficients from this signal alone.
- **EVALUATION_REVERSAL**, ply 6 f6g6: White-perspective root score changed from 146 cp to -193 cp across adjacent turns; this is NOT independent proof of a blunder.  Suggested experiment: Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights.
- **EVALUATION_REVERSAL**, ply 7 e1g1: White-perspective root score changed from -193 cp to 192 cp across adjacent turns; this is NOT independent proof of a blunder.  Suggested experiment: Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights.
- **EVALUATION_REVERSAL**, ply 8 g6e4: White-perspective root score changed from 192 cp to -166 cp across adjacent turns; this is NOT independent proof of a blunder.  Suggested experiment: Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights.
- **CLOSE_ROOT_CHOICES**, ply 8 g6e4: The top two candidate scores differ by at most 12 cp.  Suggested experiment: Test depth stability and evaluate alternative lines. Add controlled opening diversity rather than changing score coefficients from this signal alone.
- **EVALUATION_REVERSAL**, ply 9 d2d3: White-perspective root score changed from -166 cp to 261 cp across adjacent turns; this is NOT independent proof of a blunder.  Suggested experiment: Replay this FEN at depth d, d+2, with/without quiescence. Confirm a tactical error using an independent reference before changing weights.

**Limits:** Score jumps are heuristic alarms, not independently proven mistakes. The code does not update neural weights, evolve graphs, or prove that any proposed improvement works. All actual game evaluations must come from the original paceval runtime.
