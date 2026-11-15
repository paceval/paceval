# JOSHUA: A Chess Research Engine powered by local paceval

![JOSHUA: conceptual chess and mathematical search graph](figures/JOSHUA_Chess_Research_Cover_2400x1200.png)

**JOSHUA** is a Linux C++ research program that plays chess **against itself**. The name is a personal tribute to the fictional Joshua in the film *WarGames* (1983). This independent project is not affiliated with the film or its owners. It does not include any movie content.

## Optimized Linux release: two local paceval search modes (15 November 2026)

**New executable default:** `--mode research` is a compact, complete fixed-depth
reference search. The host uses lossless C++ make/unmake, a compact node and flat
edge pool, target-centric attack checks and allocation-free piece direction
lookup. **All distinct leaf features are evaluated through actual local paceval
multi-graph batches**, while grouped internal min/max reductions are executed
through persistent local paceval computation graphs.

**Optional mode:** `--mode alphabeta` enables iterative deepening, alpha-beta
cutoffs, move ordering and a conservative, depth-aware transposition table. It
still uses persistent **local paceval** graphs for leaf evaluation and final
root-value reduction; intermediate alpha-beta bounds are maintained in C++.
Because the search often needs leaf values immediately, this mode calls paceval
*scalar* evaluation for cache misses rather than claiming the same large batches
as the research mode. Neither mode uses an MCP server.

### Run on Linux

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build --target joshua -j
./build/joshua --mode research --depth 3 --plies 20 --model 2 --no-board --output results/manual_research
./build/joshua --mode alphabeta --depth 3 --plies 20 --model 2 --no-board --output results/manual_alphabeta
ctest --test-dir build --output-on-failure
```

The binary prints elapsed seconds, candidate move and German piece name, SAN,
actual search nodes, and real paceval calls. Use `--mode research` for the
maximal cached batch approach and for reproducible whole-tree experiments.
Use `--mode alphabeta` to investigate pruning at larger depths.

### Repeated, independently compared self-play

On the same Linux machine and with identical CMake Release settings, the old
full-width implementation took **3.87 s**, optimized full-width **1.26 s**, and
alpha-beta **1.29 s** over 20 self-play halfmoves at depth 3, model V2.
Both new modes reproduced **all 20 selected moves** and **all 478 root move
scores** from the original. At this shallow depth, large paceval batches are
competitive with alpha-beta's reduced search, a finding specific to this
experiment, not a universal performance claim.

See [the optimization study](OPTIMIZATION_VALIDATION.md),
[the exact CSV comparison](results/optimization_summary.csv),
[three real Linux console logs](docs/JOSHUA_optimized_research_release_console_20plies.txt),
and the revised [English whitepaper](JOSHUA_Chess_Research_Whitepaper_EN.pdf).
The original source code for independent baseline reproduction is retained
under `validation/baseline_source/`.

## Current scope

The same JOSHUA chess engine controls **both White and Black**. Before every move it builds a **complete, legal, fixed-depth** search tree (no pruning), evaluates the leaf feature vectors using persistent **local paceval** computation graphs, and evaluates grouped `min`/`max` parent reductions using additional persistent paceval graphs. JOSHUA selects the best move **under its chosen finite-depth evaluation function**. It does not claim objectively optimal play, a chess solution, or a professional playing strength.

**No MCP server is used. No Stockfish, Leela Chess Zero, UCI opponent, external engine binary or online opponent is part of this release.** A future engine-versus-engine edition is an explicit separate research milestone.

## How to compile on Linux

Requirements: a C++17 compiler, CMake 3.16 or newer, Python 3, and a separately licensed, compatible Linux `libpaceval_linux_sharedLIB.so`.

```bash
cmake -S src -B build \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j4
ctest --test-dir build --output-on-failure
```

The archive includes the original `paceval_main.h` and `paceval_main.cpp` SDK interface sources. The executable shared library must be supplied separately under its applicable rights and is **not** distributed here.

## JOSHUA versus JOSHUA

```bash
# Each side automatically selects its own move. Results and timings are saved.
./build/joshua --depth 3 --plies 8 --batch-rows 8192 \
  --output results/my_selfplay

# For reproducing a particular opening study, the first move can be forced.
# Unlike the default mode, that one initial move is not selected by JOSHUA.
./build/joshua --first-move e2e4 --depth 3 --plies 8 \
  --output results/my_e4_study

# One complete-depth-four root search (uses substantially more memory).
./build/joshua --depth 4 --plies 1 --output results/my_depth4
```

Options: `--depth 1..4`, `--plies 1..200`, `--model 1|2`, `--fen '6-field FEN'`, `--first-move e2e4`, `--batch-rows 1..65536`, `--max-nodes N`, `--no-board`, `--output DIR`, `--selftest`, `--help`. A maximum node budget (default 600,000 nodes) prevents unconstrained allocation. A depth-four full-width tree from the starting position has **206,604 cumulative nodes and 197,281 leaves**; deeper full-width searches are not supported in this release.

## Measured self-play evidence

The included research runs were executed and audited on Linux. Output seconds refer to the clock **since process start**, not a hypothetical cost estimate.

| Run | Automatically selected plies | Local paceval graphs created | Batches | Graph-point evaluations | Observed elapsed seconds |
|---|---:|---:|---:|---:|---:|
| [selfplay_depth2_6plies](results/selfplay_depth2_6plies/selfplay_timeline.csv) | 6 | 33 | 23 | 7362 | 0.220 |
| [selfplay_depth3_8plies](results/selfplay_depth3_8plies/selfplay_timeline.csv) | 8 | 77 | 178 | 56117 | 5.907 |
| [selfplay_forced_e4_depth3_6plies](results/selfplay_forced_e4_depth3_6plies/selfplay_timeline.csv) | 6 | 68 | 123 | 44213 | 7.935 |
| [selfplay_depth4_1ply](results/selfplay_depth4_1ply/selfplay_timeline.csv) | 1 | 52 | 34 | 24863 | 12.190 |

The `selfplay_forced_e4_depth3_6plies` run includes the externally forced first move `e2e4`; the remaining moves are chosen automatically. For every run, the exact console transcript is preserved in [`docs/`](docs/JOSHUA_console_depth3_8plies.txt), together with `selfplay_timeline.csv`, `root_move_rankings.csv`, `run_evidence.json`, and `game_uci.txt`.

The self-play trace prints the move number, side, number of legal choices, graph count, actual batch calls, leaf and internal node checks, **best UCI move, German piece name, origin and destination, Standard Algebraic Notation (SAN)**, resulting FEN, and monotonic elapsed time in seconds. Text board coordinates have White at the bottom. 

For example, a newly verified Linux run prints:

```text
[+0.026034s] JOSHUA BEST WHITE b1c3 | Figur=Springer (Pferd) b1 -> c3 | SAN=Nc3 | score_white=0cp
[+0.049789s] JOSHUA BEST BLACK b8c6 | Figur=Springer (Pferd) b8 -> c6 | SAN=Nc6 | score_white=30cp
```

Times are from the specifically linked depth-2 sample and must not be confused with the original depth-3 or depth-4 runs. See [the actual new trace](docs/JOSHUA_console_piece_names_depth2_4plies.txt) and [its machine-readable timeline](results/selfplay_depth2_4plies_piece_names/selfplay_timeline.csv). **The figure name always comes from the board before the move**: `Bauer` (pawn), `Springer (Pferd)` (knight), `Läufer` (bishop), `Turm` (rook), `Dame` (queen), and `König` (king). SAN uses the conventional English letters `N`, `B`, `R`, `Q`, `K`. Captures, castling, promotions, checks, and checkmates have their normal SAN notation; root-level descriptions also identify the relevant piece and action.

The extended `selfplay_timeline.csv` has `chosen_piece`, `chosen_san`, `from_square`, `to_square`, `is_capture`, and `promotion` columns. The older recorded depth-3 and depth-4 traces are preserved as historical evidence from before this display enhancement, rather than being silently altered.

## What paceval actually calculates

The C++ host owns the legal chess rules (including castling, en passant, promotion), board transitions, move sequences, tree construction, deduplication of numerical feature vectors, grouping, and output. The local paceval runtime evaluates **20 persistent feature/score graphs**, including the following example score:

```text
100*(wp-bp)+320*(wn-bn)+330*(wb-bb)+500*(wr-br)+900*(wq-bq)
```

The second model adds center control, development, activity and king-safety feature terms. Numeric weights are illustrative, fixed, and in approximate centipawn units. They do not represent a learned evaluation model or game-theoretic truth.

The engine groups parent nodes at each depth by legal fan-out and side to move, dynamically creates a reusable expression such as

```text
(v0 max v1 max v2)  # White chooses the highest White-oriented score
(v0 min v1 min v2)  # Black chooses the lowest White-oriented score
```

and batches all compatible parent nodes using the original SDK. Each returned score is checked against native arithmetic at runtime. Numerical feature-vector reuse **does not merge chess positions or resolve repetition rules**. The host's configured maximum of 65,536 rows is an application guardrail, not a proven universal SDK limit.

## Chessboard and graph illustrations

The white/black board sequences in the report were rendered from actual recorded FEN states, not manually invented pieces or moves. The cover is concept art rather than a legal position depiction.

[White's actual first move](figures/02_white_b1c3.png) · [Black's actual response](figures/03_black_b8c6.png) · [Graph architecture](figures/10_architecture.png) · [Measured stage times](figures/06_measured_stage_durations.png) · [Minimax rollback example](figures/11_minmax_example.png)

## Research verification and honest limitations

- Legal move generation passes Perft regression values 20, 400, 8,902, and 197,281 from the standard initial board at depths 1 to 4.
- Each automatically selected move is included in the full legal root move list and validated against the before/after FEN in Python.
- Evaluations and min/max reductions are checked independently against native arithmetic.
- The move history, output numbering, elapsed-time monotonicity, root rankings, and batch inventory are audited.
- Historical draw claims in the root game are handled under a stated research policy. **Full path-sensitive threefold-repetition adjudication within each internal search node is not implemented.** Therefore the application is a computational research prototype, not a complete tournament-grade chess engine.
- Full-width search becomes prohibitively large at deeper horizons. The current static evaluation is intentionally simple and contains no trained NNUE model or Stockfish/Lc0 search technology.

Read the full [English research whitepaper](JOSHUA_Chess_Research_Whitepaper_EN.pdf) and [validation statement](RESEARCH_VALIDATION.md). See [licensing](LICENSE_NOTICES.md).

## Future research: JOSHUA against Stockfish / Leela

**Not implemented in this version.** A later, separate edition may add a UCI interface, match scheduling, strict clocks and draw rules, reproducible hardware/settings, and statistically powered match comparisons against properly licensed and sourced Stockfish or Leela Chess Zero. That future research should be reported separately from the present self-play measurements; no superiority is claimed.

## Source structure

`src/joshua.cpp` is the public self-play executable. `src/chess_rules.h`, `src/paceval_math.h` and original `src/paceval_main.*` provide rules, features and the SDK interface. `src/chess_decision.cpp` and `src/chess_search.cpp` are auxiliary internal verification/research executables, **not other opponents**. `scripts/` contains the independent checks, figure creation and whitepaper generator; `results/` contains actual recorded runs; `docs/` contains actual full console logs; `figures/` contains the conceptual cover and data-driven board/math figures.

To regenerate the combined 18-page report after re-running the original whitepaper
script, use `python scripts/append_optimization_pdf.py
JOSHUA_Chess_Research_Base_Whitepaper_EN.pdf`. The optimization addendum
is also included separately under `docs/`.
