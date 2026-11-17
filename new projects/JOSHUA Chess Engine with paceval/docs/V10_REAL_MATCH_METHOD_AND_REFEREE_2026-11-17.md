# JOSHUA V10 real Stockfish matches and paceval-graph learning: technical explanation

**Evidence date:** 17 November 2026. **Source:** user-provided Linux `joshua_autoplay(1).zip`. **Code reviewed:** `scripts/stockfish_match.py`, `src/joshua_referee.cpp`, `src/adaptive_score_graph.h` in this repository. All observations below relate to the supplied run, not to a newly conducted Stockfish tournament in the documentation environment.

## 1. Outcome: software progress versus chess progress

The controller's bounded `match_index.json` holds 250 completed games, IDs 10 through 259. Against Stockfish 16 (Skill Level 20, 1,000 played-move nodes), JOSHUA (search depth 2 and quiescence 2) recorded zero wins, eight draws and 242 losses. This is a total score of 4.0/250, or 1.6% of possible match points. Models 0 to 7 appeared as active graph versions during this interval. All 28 version-to-version comparisons in `strength_summary.json` carry `NOT_ESTABLISHED` status. These figures do not justify a rating increase or a causal claim that adaptive graph changes improve chess strength.

The best observed points rate is version 2: 1.5/18 = 8.33%. Version 7 scored 0/33, worse descriptively than the initial version 0 (0.5/25 = 2%), but these were adaptively selected, distinct and small samples. The experiment has not randomized independent matches with frozen versions, so even the direction of strength change is **not statistically established**.

A critical distinction: the index holds the latest 250 entries; only 33 detailed `game_000227.zip` to `game_000259.zip` archives survived the rolling 25 MB quota. All 33 archives passed a ZIP CRC check and their results/graph versions matched the index. Those 33 games were losses and contained 52 documented formula candidate trials; none passed the full local promotion gate. The older per-move data cannot be re-audited from this input. The cumulative model summary therefore has a lower evidentiary level than the retained full per-game archive set.

## 2. Who does what? Three different decision systems

| Component | Mathematical/chess responsibility | Does *not* do |
|---|---|---|
| `joshua` (C++ search + paceval) | Legal search, board feature extraction, reused paceval score graphs, ranking and chosen move | Grade its own overall strength against Stockfish |
| `joshua_referee` (C++ rule engine) | Validate FEN and moves, apply the legal move, output new FEN, SAN, key and status | Score candidate moves, call paceval, judge whether a move is strategically good |
| `stockfish_match.py` (Python controller) | Alternate colors, manage UCI opponent and teacher, track history and repetition, collect losses, generate/test model candidates, archive/log | Perform the weighted position-scoring graph in place of real paceval |
| Stockfish 16 UCI | Play the opposing color; independently evaluate before/after positions under fixed reference node budgets | Serve as mathematical proof that a new JOSHUA graph is globally stronger |

The referee's implementation is explicit in `src/joshua_referee.cpp`: `joshua_referee --fen 'six fields' [--move e2e4]` parses the board, rejects a FEN with the previous side illegally in check, enumerates all legal moves, rejects any UCI move not among them, formats SAN, applies the selected move and emits **five lines in order**: resulting FEN, status, SAN, normalized repetition key and current legal move count.

The status routine recognizes `checkmate`, `stalemate`, `fifty_move_claim`, `insufficient_material`, and `ongoing`. **The Python controller**, not the referee process, maintains position-key counters and assigns `threefold_repetition_claim` after a key occurs three times. These are the rules actually implemented; some corner cases in claim handling and insufficient-material assessment would need additional validation before use as a complete FIDE tournament arbiter.

## 3. What one tactical chess situation contributes

The pipeline works as follows:

1. A legal FEN is received from the referee. The active mathematical model version, such as version 7, is read from `stockfish_sessions/active_graph.tsv`.
2. Joshua's native C++ chess search enumerates successor positions and extracts 48 interpretable board features. The original paceval library evaluates the classical score, neural residual and active adaptive formula; the search decides the move.
3. The referee validates and applies that actual move. The controller stores the legal transition as UCI, SAN and before/after FEN.
4. Stockfish performs a reference query for the pre-move position and another query for the resulting position from the opponent's viewpoint. In the retained session, the reference teacher budget is 2,500 nodes per query. Each reference query resets the search hash.
5. Centipawn and mate scores are retained separately. For ordinary scores a bounded, heuristic score loss is calculated in expected-point *percentage points* (not a calibrated probability). Suspected blunders are added to `tactical_findings.csv`.
6. After the required paired-color games, high-loss FENs become candidate training cases. The controller proposes up to four bounded coefficient changes, either a linear weight or a whitelisted nonlinear tactical term. Joshua recompiles a *new mathematical paceval expression* from this model data, not new C++ source.
7. Candidate and baseline play the same candidate FENs. Stockfish re-grades the resulting moves. Candidate approval requires an actual changed decision, a lower training loss, a nonworse average holdout loss and limits on regression at individual holdout positions. Otherwise the proposal is rejected.
8. If provisionally accepted, a new model TSV and exported exact formula are written atomically and loaded on subsequent games. A local acceptance result does **not** replace the missing separate, unbiased version-versus-version playing-strength tournament.

**Observed diagnostic example (not an optimal-move assertion):** the pending game pair includes the FEN `rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1`, Joshua's move `g8h6`, and a recorded bounded loss of 11.47 percentage points. This is one source-derived **candidate tactical regression**, not proof the selected move was a losing move under a deeper search. Any replacement move must be freshly tested against the same position and teacher settings.

## 4. Exact mathematics versus approximations

The stored white-perspective score is the V4 base plus a clipped adaptive correction. In readable notation:

```math
S_{10}(s)=S_4(s)+\min\left(160,\max\left(-160,\sum_i a_i f_i(s)+\sum_j b_j g_j(s)\right)\right).
```

The actual SDK parser uses **infix** `min` and `max` operators. The current version 7 has weights `mobility=2`, `captures=2`; nonlinear terms `king_tactics=+0.5`, `hanging_pressure=+0.5`, and `active_captures=-0.5`. Other linear coefficients are zero. These three nonlinear terms genuinely change the expression text; they are not a guarantee of lookahead or spatial understanding.

The UCI teacher loss is explicitly a heuristic:

```math
p(c)=\frac{1}{1+\exp(-c/180)},\qquad L=100\max(0,p_{\mathrm{before}}+p_{\mathrm{after,opponent}}-1).
```

The code caps the raw centipawn input for the transform and handles mate scores separately. This calculation is performed by the **Python grading controller**, not claimed as a paceval-evaluated chess score. Do not confuse lower training loss, better local move imitation, and proven higher full-game strength.

## 5. Exactly which files are readable and persistent?

| File | What it really contains | How it is used |
|---|---|---|
| `stockfish_sessions/active_graph.tsv` | Version number, whitelisted named terms and coefficients | Model **input** on next game; not the full formula |
| `stockfish_sessions/active_graph_expression.txt` | **Full active adaptive paceval parser expression** and all variable names | Readable expression last exported by a real Joshua invocation |
| `stockfish_sessions/active_graph_terms.csv` | Coefficients + algebraic source of each nonzero or listed term | Human inspection and diffs |
| `stockfish_sessions/active_full_graph_catalog.csv` | Formula text and `evaluated_points` for every registered graph in the latest exported invocation | Includes long V4 neural graphs as well as adaptive score |
| `stockfish_sessions/archives/game_000259.zip` | Immutable game-specific `evaluated_graph_expression.txt`, `model_used.tsv`, per-ply graph exports and grades | Reconstruction of a historic executed decision |
| `formulas/v4_graph_expressions.tsv` | Fixed historical V4 trained 12-neuron + fused model formulas | Original neural graph definitions |
| `formulas/observed_active_graph_v7.txt` | Snapshot from the actual user-supplied v7 output | Reproducible published example, not a source-code modification |

Example shell commands from the flat Linux installation directory:

```bash
cat stockfish_sessions/active_graph_expression.txt
cat stockfish_sessions/active_graph.tsv
head -n 5 stockfish_sessions/active_full_graph_catalog.csv
unzip -p stockfish_sessions/archives/game_000259.zip evaluated_graph_expression.txt
unzip -p stockfish_sessions/archives/game_000259.zip joshua_ply_002/paceval_graph.txt
```

The `.txt` file is **not a binary serialized internal SDK graph**. It is the exact mathematical expression submitted to paceval, with its variables and version. Graph creation from that expression happens again inside a new process. That distinction explains why saved model TSV files can be activated without modifying or recompiling the C++ source.

## 6. High-priority research and code improvements

**First: evaluation protocol.** Preserve the original baseline (V0), the historically most promising exploratory variant (V2), and the current V7 as frozen, immutable models. On a previously unused opening list, alternate colors and run sufficiently many games *without* changing coefficients. Record paired score, uncertainty and termination type. Do not promote a model based only on its own training data or the same four fixed holdout openings.

**Second: tactical coverage.** Build a library of positions requiring mate-in-one recognition, mate-in-two defense, hanging-piece avoidance, capture recapture, perpetual checks, pinned pieces, discovered attacks and quiet defensive moves. For each, save FEN, the legal candidates, Stockfish reference analysis, Joshua ranking, model version and direct paceval graph expression. Check changes at multiple search depths with fixed budgets. Because the engine uses depth 2 + quiescence 2 in the present benchmark, deeper tactical search is a major independent axis of improvement.

**Third: richer, still readable paceval mathematics.** Current features compress a complex chessboard into 48 values. Add *genuinely discriminating* spatial and tactical features, for example king ring attack multiplicities, pinned pieces, undefended recapture squares, passed-pawn race distances and moves-to-threat estimates. Let C++ derive board topology, and implement the resulting composed score, constraint margins, sensitivities and model-difference formulas as actual paceval graphs. Require independent numeric and chess regression checks for all new terms.

**Fourth: stronger model promotion and rollback.** Keep a persistent model registry of expression SHA-256 hashes, active version, baseline version, source FENs and acceptance criteria. Separate training, local validation and held-out complete-game tournaments. Implement an automatic rollback path when an independently measured regression is detected. The current controller marks promotion *provisional* and does not provide this final global gate.

**Fifth: scientific audit.** Maintain an immutable history of all generated graph expressions, not only the latest view; store precise Stockfish build identity, options, node counts, seeds, engine version, game result, durations and mate findings. Continue bounded ZIP retention, but export periodic immutable manifests if long-term per-game history is important. `match_index.json` stores only the latest 250 rows and old game ZIPs may be deleted.

## 7. Reproducibility and evidence limits

This study is retrospective on the provided run. The new assessment file `results/REAL_STOCKFISH_AUDIT_2026-11-17.json` is derived only from its included `match_index.json`, `strength_summary.json`, 33 surviving game archives, and source-code inspection. No new real Stockfish game was played while updating these documents. Stockfish 16 at 1,000 move nodes is a fixed reference setting, not unrestricted Stockfish. A 1.6% score is not a precise general-purpose Elo rating. Graph version comparisons are observational and the reported relative Elo figure in the controller is not a validated rating.
