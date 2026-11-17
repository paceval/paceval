# V13 Depth-7 Search and Fused paceval Score Graph: Exact Implementation

V13 is an actual C++17 code change. It does not automatically create giant seven-ply mathematical minimax expressions, which would exponentially expand. The exact full-width research experiments in `joshua_long_graph` remain separate.

## Research motivation

JOSHUA's earlier deepening loop created an isolated transposition table for every search depth and the V4 feature evaluator executed the final neural and adaptive graphs sequentially. V13 preserves the semantics of independent root evaluation while carrying safe move-ordering hints across depths, reusing persistent paceval graph handles, and composing the existing V4 fused-output formula with the approved adaptive correction in one additional persistent graph. The C++ host still extracts the 48 board features, controls legal move generation and search, and manages time/node budgets.

The exact combined formula is generated at runtime from two approved source strings. An illustrative mathematical definition is:

```math
S_{13}(s)=S_{V4}(s)+\min\left(160,\max\left(-160,\sum_i a_i f_i(s)+\sum_j b_j g_j(s)\right)\right).
```

The final V4 expression is substituted for the `base` variable in the existing adaptive expression. The fused paceval graph inputs are twelve hidden outputs `h0` through `h11`, `base` (the V3 baseline score), and 48 V4 board features. The independently reusable twelve paceval sigmoid graphs remain unchanged. This is mathematical function composition, not native evaluation of the score.

The real formula can be inspected in `paceval_v13_fused_score.txt`; registered handles and evaluation points are recorded in `paceval_all_graphs.csv`.

## Search semantics

- Requested depth 7 is a cap/target. The search proceeds through completed iterations 1, 2, ..., 7 and prints a `DEPTH_COMPLETED` line after each.
- The Alpha-Beta host evaluates each legal root action with a full search window. PV move-ordering hints can alter the sequence of exploration but cannot change the exact fixed-horizon minimax value when that iteration finishes.
- Transposition entries are keyed by board, halfmove clock, remaining depth and ply. An ordering hint does not assert equality of different states or bound types.
- `--search-ms` and `--search-nodes` are per-move budgets. The incomplete candidate iteration is discarded in favor of the previous completed iteration. A limit reached even before the first completed iteration remains an explicit failure, not a fabricated move.
- The returned `search_depth_actual` in CSV tells the reader what happened, not what was requested. The graph catalog distinguishes registered graphs and actual evaluation-point counts.
- `--quiescence 2` adds bounded tactical search after the requested horizon; this does not mean the full-width legal tree is searched through an additional two complete plies everywhere.
- A separately invoked V12 verification stage is disabled by default for depth-7 runs because the initial depth-7 request is already the more demanding experimental path.

## Reproducible real SDK tests

The legal nonterminal input is:

`8/7k/8/8/8/6K1/7P/8 w - - 0 1`

The tested model is the regular V4 neural architecture plus an approved nonzero `feature.king_tactics` coefficient of `0.5000` solely for deterministic evaluation-graph coverage. It is **not** a learned or promoted stronger chess model. A genuine SDK run with `--depth 7 --quiescence 2` completed all seven iterations and played `g3f4` (SAN `Kf4`). The authentic run's iteration and graph-count evidence is provided in `results/v13_depth7`.

The independent fused versus unfused regression runs the same position through two separate genuine paceval execution paths. It compares the entire root move ranking and all reported root scores. The test additionally opens the exported graph catalog and checks that the compiled combined graph has genuinely evaluated points.

The opening-position budget regression requested depth 7, stopped at the configured 4,500-node cap and returned a completed depth-2 result. This safeguards an experimental continuous process; it is not an assurance that complex depth-7 opening searches finish under the user's hardware/time limits.

## Status and further research

This release establishes a completed seven-ply mathematical chess calculation and a correct reuse/composition path for original paceval graphs. It does **not** demonstrate that the new move is stronger by Stockfish reference, that merged paceval expressions reduce runtime, or that the neural model generalizes better. Test depth-7 Stockfish matches with frozen model and time/node budgets; compare identical openings with alternating colors, archive all model expressions, and consider speed or hardware studies only as separate experimental work when explicitly justified.
