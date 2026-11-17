# JOSHUA V11: Immutable Champion Evaluation and Tactical Graph Research

## Motivation

The 17 November 2026 audit of V10 recorded 250 real Stockfish games, with 0 wins, 8 draws and 242 losses by Joshua. Model versions 0 through 7 occurred; the graph update process worked but improvement was **not** established. One weakness was the earlier policy of promoting after only local FEN checks. This document describes the *implemented* new safeguard and its tested limits, not a hypothetical next project.

## Components

- `src/joshua.cpp`: genuine paceval-based numerical evaluation; includes bounded non-capturing checking continuations at the first quiescence horizon when budget is at least 2.
- `src/adaptive_score_graph.h`: approved whitelisted formulas. V11 adds `king_check_combo` and `hanging_capture_combo` to the previous eight permitted nonlinear templates. At most six are active in a given graph.
- `scripts/stockfish_match.py`: main Stockfish-versus-Joshua coordinator; local candidate-generation and training/holdout screens.
- `scripts/v11_champion_gate.py`: **actual** candidate-versus-incumbent games with paired colors on fixed openings, deterministic settings, process-isolated computations, C++ referee adjudication and complete match-result decision gate.
- `scripts/v11_restore_graph.py`: manual safe restoration of a previously frozen version, preserving backup and version monotonicity. Never apply while a game is active.

## Human-readable scientific graph evidence

`active_graph.tsv` is the persistent numeric model, while `active_graph_expression.txt` is the exact expression compiled by paceval, and `active_full_graph_catalog.csv` includes the *full collection* of registered formulas with actual evaluation counts. Persistent `model_versions/` snapshots keep the most recent 16 distinct frozen TSVs. The old/new models and every challenger game are also archived inside the final game ZIP.

## Exact release decision chain

```
Real Stockfish match -> legal FEN -> Stockfish cp/mate grading
 -> selected failed positions + fixed withheld FEN set
 -> bounded proposed coefficients/templates -> real paceval evaluation
 -> independent local loss/mate checks -> freeze champion and challenger TSV
 -> matched candidate vs incumbent games, alternate colors
 -> legal referee SAN/FEN and terminal result on every move
 -> ALL games must finish -> score threshold + wins margin
 -> atomic model publication OR explicit rejection
```

Default new options: `--champion-pairs 4`, `--champion-max-plies 100`, `--champion-min-score 0.625`. A candidate must win at least two more games than it loses and achieve at least 62.5% of the available points. All paired games must finish with an explicitly recognized chess result. Draws cannot silently count as proof of improvement. A threshold on a small deterministic series is a *local safety filter*, not a statistically validated rating increase.

The challenger openings are six predetermined opening moves not in the Stockfish-match rotation: `b2b4`, `c2c3`, `f2f3`, `g2g4`, `b1a3`, `g1h3`. No candidate selects its preferred test openings. The exact legal move sequence, side, model version, per-move wall time and final result are written into `champion_duel/pair_XX_{white|black}.json` and the corresponding gate verdict. These remain in the per-game compressed ZIP. The old `active_graph.tsv` is never changed if tests fail or time out.

## Boundaries and threats to validity

- The reference Stockfish game controller and the new champion-versus-challenger comparison are **different test types**. The latter does not use Stockfish to play either side.
- True improvements may fail this conservative filter. A candidate that is always identical to its parent, or whose match is truncated, is rejected. Four paired openings are a small, correlated sample and cannot establish general Elo gains.
- Increased formula length does not add missing board information. The inherited 48 inputs are coarse position features and the search horizon may still be too shallow.
- Mate warnings and teacher losses are finite-node heuristics. The C++ referee certifies legality of tested moves only under the implemented rule set and specific FEN history.
- Recorded V10 Stockfish results were real historic runs supplied by the user, **not new V11 Stockfish tournament results**.
- Restoring a past version is a manual management operation. There is no verified automated post-promotion statistical rollback yet. The V11 gate prevents untested provisional promotions.

## Actual test evidence

- Linux x64 compiled from the modified sources; authentic original paceval library loaded and executed the two newly whitelisted nonlinear components.
- One controlled authentic comparison (champion graph version 0 vs challenger version 1) selected **38 real Joshua engine moves across two color-swapped tests**. Both were intentionally truncated at 20 plies and the gate correctly rejected promotion.
- Dedicated negative policy tests for truncated games, model/color identity mismatch and insufficient margins passed.
- Historical V10 results: [audit JSON](../results/REAL_STOCKFISH_AUDIT_2026-11-17.json).

## Extending the experiment

Use completed paired games with a higher ply cap to explore actual promotion behavior, then freeze each accepted model and independently evaluate it against Stockfish on fresh openings. This should distinguish `NO_CHANGE`, `LOCAL_GATE_PASS`, `MATCH_GATE_PASS`, `STRENGTH_NOT_ESTABLISHED`, and `INDEPENDENT_STRENGTH_IMPROVEMENT` as fundamentally different scientific claims.
