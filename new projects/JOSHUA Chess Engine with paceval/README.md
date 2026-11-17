# JOSHUA V10 | Adaptive Mathematical Chess Evaluation with paceval

![JOSHUA mathematical chess research](figures/JOSHUA_Chess_Research_Cover_2400x1200.png)

**Release:** 15 November 2026  
**Platform:** Linux x86-64, C++17, Python 3 match controller  
**Research status:** Verified paceval mathematical execution; **no demonstrated improvement in chess playing strength**.

JOSHUA is a research chess engine that uses the **original paceval Mathematical Engine** to execute reusable mathematical evaluation graphs. A native C++ host implements legal moves, board state and search. A Python controller conducts alternating-color matches against an external Stockfish UCI engine, captures diagnostics and tests bounded changes to versioned paceval score formulas. Source-code recompilation is **not required** when an allowed coefficient/template configuration is promoted.

The [V10 research whitepaper](JOSHUA_Chess_Research_Whitepaper_EN.pdf) is the **single current PDF** for this release. Earlier V4/V5 work remains identifiable in source and reproducible historical results, not as a second, misleadingly current whitepaper.

## 1. Scientific use case and state of the art

Chess move selection combines discrete legal-move generation, a large game tree and numerical evaluation of nonterminal positions. Modern Stockfish uses optimized alpha-beta search with an NNUE evaluation model; JOSHUA studies a different **mathematical execution boundary**, not a claim of equivalent strength. It tests which explicit heuristic, neural and composite score operations can be represented as reusable paceval graphs while a C++ engine retains legality, the search tree, state and control flow.

A typical experiment uses legal FEN positions, one frozen graph version, controlled Stockfish settings and the same preset opening with the colors exchanged. Outputs include recorded moves and outcomes, search diagnostics, versioned mathematical expressions, tactical findings and a trace of every adaptive candidate. Leela Chess Zero is **not integrated** into V10; it could serve as a future independent neural-search opponent.

Official context: [Stockfish](https://github.com/official-stockfish/Stockfish), [Stockfish NNUE documentation](https://official-stockfish.github.io/docs/stockfish-wiki/Advanced-topics.html), [paceval API](https://paceval.com/api/).

## 2. Verified status of the V10 release

| Capability | Evidence and status |
|---|---|
| Four compiled Linux x86-64 programs (`joshua`, `joshua_referee`, `joshua_selfplay`, `joshua_long_graph`) | Compiled; see `V10_RELEASE_VALIDATION.md` |
| Original paceval runtime and non-linear score graph | **Executed** with the original user-supplied runtime in a depth-1/two-ply smoke test |
| Human-readable mathematical execution register | **Executed**: 48 registered graphs, 19 executed graphs, 471 graph-point evaluations |
| Two-game alternating-color UCI controller | **Tested with real Joshua + paceval and a simulated UCI Stockfish peer**, not a real V10 Stockfish tournament |
| Matched-pair adaptation and promotion rules | Software tests passed; simulated teacher data were used for promotion-policy tests |
| Genuine Stockfish-versus-JOSHUA V10 results | **Not yet provided / not verified in this release** |
| Improved Elo, tournament score or general playing strength | **Not established** |

**Counting matters:** a graph created in a process is not necessarily evaluated. Graph-point evaluations are not unique positions or games. This evidence supports correct integration for the tested inputs, not a chess-strength claim. See [`results/v10_authentic_sdk_smoke/paceval_all_graphs.csv`](results/v10_authentic_sdk_smoke/paceval_all_graphs.csv) and [`V10_RELEASE_VALIDATION.md`](V10_RELEASE_VALIDATION.md).

## 3. Run V10 on Linux x86-64

### A. Minimal update to an existing flat installation

For a system already containing `~/Dropbox/joshua_autoplay/libpaceval_linux_sharedLIB.so`, use **`JOSHUA_V10_Flat_Linux_x64.zip`**, not the full GitHub source ZIP. Stop running engines before replacing executables; retain the existing session folders. After copying the separate *private installation archive* into `~/Downloads`:

```bash
cd "$HOME/Dropbox/joshua_autoplay"
unzip -o "$HOME/Downloads/JOSHUA_V10_Flat_Linux_x64.zip"
chmod 755 joshua joshua_referee joshua_selfplay joshua_long_graph run_stockfish_matches.sh
export PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so"
command -v python3
ls -l /usr/games/stockfish
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 2 --progress-seconds 5
```

If Stockfish is not installed, install it using the target distribution's package manager and confirm its exact executable path. **Do not start with `sudo`.** The first test uses two matches so each engine plays both colors. On success, use `--max-games 0` for continuous play. If files are owned by root from a previous `sudo` run, restore ownership of the existing session folders before starting without `sudo`.

```bash
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 0 --progress-seconds 5
```

The original paceval runtime is required. Stockfish is installed separately. **Neither is included in the public GitHub ZIP.** The optional private flat installation archive may contain an authorized copy of the user-supplied paceval runtime; do not republish it without permission.

### B. Full GitHub checkout or source rebuild

```bash
# Run at the repository root. Stockfish and the original paceval runtime must exist.
./scripts/run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 2

cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build -j 2
ctest --test-dir build --output-on-failure
```

The launcher in `scripts/` expects the compiled programs under `bin/`; use the flat launcher in the flat directory. The build uses the authentic SDK adapter and needs the external compatible shared library for actual chess mathematics.

## 4. What paceval actually computes

The chess rules, candidate move generation, feature extraction, alpha-beta search control, UCI communication and candidate selection are C++/Python host responsibilities. paceval evaluates suitable persistent graph expressions, including classical score components, the V4 trained residual network, the composite adaptive score and supported numerical reductions. Some legacy graphs may be created but unused in a particular search mode.

The V4 neural support has **48 inputs, 12 sigmoid hidden computations and one fused result**. V10 adds a versioned, bounded, white-perspective correction to the base score:

```math
S_{10}(s)=S_4(s)+\mathrm{clip}\left(\sum_{i=1}^{8}a_i f_i(s)+\sum_{j}b_j g_j(s),-160,160\right).
```

The equation above is the mathematical model. The **actual SDK expression** uses the supported infix `min`/`max` notation rather than calling a `clip` function. Eight fixed linear feature differences remain available, and V10 can add up to **six active nonzero nonlinear terms** chosen from eight whitelisted templates:

| Template | Example mathematical content / purpose |
|---|---|
| `king_alarm` | Squared king-danger difference |
| `king_tactics` | King danger weighted by queen/rook threats |
| `hanging_pressure` | Squared hanging-piece difference |
| `queen_exposure` | Queen threat multiplied by attacked-piece count |
| `rook_exposure` | Rook threat multiplied by attacked-piece count |
| `check_pressure` | Difference between check indicators |
| `pawn_race` | Squared passed-pawn counts |
| `active_captures` | Mobility multiplied by pseudo-legal capture count |

These are **position heuristics**, not forced-mate solvers or certified tactical proofs. Formula terms are selected from a fixed C++ grammar, with bounded numeric coefficients and domain checks. Arbitrary user-supplied expression strings are not accepted from the TSV file. The complete exact expressions appear in [`docs/V10_TACTICAL_GRAPH_EVOLUTION.md`](docs/V10_TACTICAL_GRAPH_EVOLUTION.md) and in the runtime graph exports.

## 5. Human-readable formulas and complete graph evidence

Every Joshua engine invocation can export these files to its own output directory:

| File | Meaning |
|---|---|
| `paceval_graph.txt` | Full versioned adaptive score expression and its input variables |
| `paceval_graph_terms.csv` | Term names, coefficients and their source expressions |
| `paceval_all_graphs.csv` | All registered graph formulas, graph IDs, variables and actual `evaluated_points` |
| `run_evidence.json` | Engine configuration and counters from the executed run |

The Stockfish controller also keeps convenient copies of the **latest** authentic formula under `stockfish_sessions/active_graph_expression.txt`, `active_graph_terms.csv` and `active_full_graph_catalog.csv`. Persistent configurations reside in `stockfish_sessions/active_graph.tsv`; the same version is read at the start of later games. Long V4 neural formulas are also in [`formulas/v4_graph_expressions.tsv`](formulas/v4_graph_expressions.tsv).

The graph IDs (`G0001`, etc.) are **process-local**, not stable universal identifiers. A zero in `evaluated_points` means registered but unused in that invocation. The per-game ZIP archives retain the underlying per-ply output, FEN transitions and candidate-trial evidence. Do not sum unique graph counts across separate engine processes as if they were one graph set.

## 6. Automated matches, tactical findings and bounded graph evolution

The controller alternates Joshua White and Joshua Black against Stockfish across a matched pair using the same scheduled opening. By default, Stockfish moves are limited to **1,000 nodes per move**, the separate reference teacher uses **2,500 nodes**, and Joshua uses **depth 2 / quiescence 2**. The default `Skill Level` is 20. Those settings define the experiment; they do **not** define a universally calibrated Elo rating.

The V9-style mean centipawn loss was excessively influenced by very large synthetic mate scores. V10 retains actual UCI `cp`/`mate` score types separately, flags mating failures and computes an **explicitly heuristic**, bounded decision-loss signal:

```math
p(c)=\frac{1}{1+\exp(-c/180)},\qquad L=100\max\{0,p_{\mathrm{before}}+p_{\mathrm{after,opp}}-1\}.
```

Here `L` is a percentage-point heuristic score loss, **not** Stockfish's calibrated WDL metric. Stockfish is only the reference teacher for real matches; policy unit tests employ labeled simulated data.

The default model stays fixed for **at least four complete color pairs per version** (`--minimum-pairs-per-version 4`). Afterward the controller can propose bounded changes to nonlinear templates and existing weights. It runs candidate models through real Joshua + paceval decisions on training FENs and disjoint control FENs, then grades those choices using Stockfish when present. A proposal must change a move, improve the training measure, satisfy holdout safeguards and execute without API errors. Acceptance remains **provisional**. The promoted TSV is saved atomically and used by later games **without recompiling the source**. Longer graphs are not accepted simply for being longer.

## 7. Measuring improvement versus Stockfish

Use `stockfish_sessions/strength_summary.json` to review results **by graph version and fixed opponent configuration**. A relevant comparison needs the same Stockfish identity, node budget and skill, the same Joshua search settings, paired colors and comparable opening sets. The code requires at least eight common distinct openings before reporting an exploratory paired trend. `NOT_ESTABLISHED` means insufficient or inconclusive evidence, **not** that chess strength is unchanged.

Reliable conclusions require many independent, held-out opening pairs and repeated matches with **frozen** model versions. Testing a model on the very positions used to select it is not evidence of general playing-strength gain. An improvement in evaluation loss is not automatically an improvement in completed-game results.

## 8. Real V10 Stockfish games, graph tests, and referee: 17 November 2026

**Outcome: graph evolution works as software, but higher chess strength has not been demonstrated.** The user-provided V10 session contains a **bounded index of 250 completed games (game IDs 10 to 259)** against **Stockfish 16** at Skill Level 20 and 1,000 nodes per played move. Joshua used depth 2 and quiescence depth 2. The session records **0 Joshua wins, 8 draws and 242 losses**. Model versions 0 to 7 were actually used, proving that persistent model data changed. None of the **28 exploratory version comparisons** is marked as establishing an improvement. This differs from the original release's mock-UCI software test: real Stockfish games have since been played on the user's Linux system.

![Observed Joshua match score by active graph version. Scores are descriptive, not independent strength claims.](figures/v10_real_stockfish_points_by_version.png)

| Active graph version | Recorded games | W / D / L | Joshua match score | Mean heuristic loss (pp) |
|---|---:|---:|---:|---:|
| 0 | 25 | 0 / 1 / 24 | 2.00% | 3.015 |
| 1 | 16 | 0 / 2 / 14 | 6.25% | 2.787 |
| 2 | 18 | 0 / 3 / 15 | 8.33% | 2.467 |
| 3 | 14 | 0 / 0 / 14 | 0.00% | 2.837 |
| 4 | 60 | 0 / 0 / 60 | 0.00% | 2.606 |
| 5 | 70 | 0 / 2 / 68 | 1.43% | 2.664 |
| 6 | 14 | 0 / 0 / 14 | 0.00% | 2.693 |
| **7, current** | **33** | **0 / 0 / 33** | **0.00%** | **2.883** |

The relatively better observed V2 score is not proof that V2 is stronger. Version samples are small, unequally sized, adaptively selected and share opening schedules. In the **33 surviving ZIP game archives (227 to 259)**, the controller logged **52 candidate trials with zero accepted**. All 33 ZIP files passed CRC verification, and their outcome/model metadata agree with the index. Older per-game archives were deleted under the 25 MB rolling quota; therefore the 250-game index can be analyzed statistically, but only 33 games still have full surviving move-by-move audit files. See [the complete observed-match method and referee explanation](docs/V10_REAL_MATCH_METHOD_AND_REFEREE_2026-11-17.md) and [the machine-readable audit](results/REAL_STOCKFISH_AUDIT_2026-11-17.json).

### How one chess position changes a paceval graph

1. The C++ referee validates the FEN state and the selected UCI move, then emits the resulting FEN, SAN and status. The Python controller also maintains threefold-repetition counts. Neither of these components assigns a Stockfish-quality score.
2. Joshua's C++ search builds its legal candidate tree and computes **48 chess features**. The original paceval library evaluates the V4 neural score plus the versioned adaptive formula. The engine returns a legal chosen move with `run_evidence.json` and its graph export.
3. A separate Stockfish UCI query grades the *before* and *after* positions at a fixed reference node budget (2,500 nodes in the retained session summaries). Centipawn and mate signals are retained separately. A bounded heuristic score loss identifies candidate mistakes, not certified blunders.
4. After a sufficient complete paired-color window, the controller proposes up to four bounded linear/nonlinear coefficient changes, builds real new paceval expressions and replays selected training FENs and separate fixed holdouts. A changed move, improved training loss and nonworsening holdouts are required before a **provisional** promotion.
5. The promoted version is written to the TSV for the *next* game. Actual improvement still requires a **separate, frozen-version head-to-head tournament** against an unchanged Stockfish opponent. Current automatic promotion does not require that final tournament and thus is not proof of greater strength.

### What exactly does the referee do?

`src/joshua_referee.cpp` is a chess-rule adjudicator written in C++ without paceval or Stockfish. It parses the six-field FEN, rejects invalid prior-side-in-check positions, enumerates legal moves, rejects illegal UCI moves, updates the board and produces a five-line response: `FEN`, `status`, `SAN`, `repetition key`, and `legal-move count`. It identifies checkmate, stalemate, a 50-move-rule claim threshold, and a limited insufficient-material rule. The Python host counts repeat position keys to report a claimable threefold repetition. The referee **does not evaluate tactical quality, choose moves, optimize graph coefficients, or independently validate Stockfish's evaluation**. Its draw and insufficient-material handling is a specific demonstrator policy, not a claim of full tournament-arbitration certification.

### Where to read the *actual* paceval expression

- **Whole current adaptive expression:** `stockfish_sessions/active_graph_expression.txt`. The supplied run contains **version 7**, with linear `mobility=2`, `captures=2`, plus nonzero nonlinear `king_tactics=0.5`, `hanging_pressure=0.5`, `active_captures=-0.5`. This is the actual exported parser expression, not merely the configuration.
- **Individual human-readable terms:** `stockfish_sessions/active_graph_terms.csv`.
- **Editable persistent coefficient/model version:** `stockfish_sessions/active_graph.tsv` (not a complete formula; changes require valid schema).
- **Every registered graph including long V4 neural expressions:** `stockfish_sessions/active_full_graph_catalog.csv`. The `evaluated_points` column distinguishes used graphs from registered-but-unused graphs.
- **Exact executed expression of a historic move:** `stockfish_sessions/archives/game_000259.zip`, for example `joshua_ply_002/paceval_graph.txt`, and the file `evaluated_graph_expression.txt` at the ZIP root. Each surviving game contains an immutable per-move record.
- **V4 original graph expressions:** [`formulas/v4_graph_expressions.tsv`](formulas/v4_graph_expressions.tsv). A verified snapshot of the user-run V7 adaptive graph is provided in [`formulas/observed_active_graph_v7.txt`](formulas/observed_active_graph_v7.txt).

For a flat Linux installation, run:

```bash
cat stockfish_sessions/active_graph_expression.txt
column -s, -t < stockfish_sessions/active_graph_terms.csv | less -S
head -n 5 stockfish_sessions/active_full_graph_catalog.csv
unzip -p stockfish_sessions/archives/game_000259.zip evaluated_graph_expression.txt
unzip -p stockfish_sessions/archives/game_000259.zip joshua_ply_002/paceval_graph.txt
```

**Next engineering improvements:** (i) freeze the strongest historical candidate and require independent color-balanced A/B matches before promotion; (ii) avoid picking the same fixed holdouts for every candidate by reserving unseen openings and positions; (iii) add mate-in-1/2 tactical regression suites and more informative features; (iv) study search depth and quiescence independently from the score model; (v) log graph hashes, decision changes, teacher node count and strict rollback reasons for every release. Increasing expression length alone is not an acceptance criterion.

## 9. Live diagnostics and bounded disk use

The console prints `GAME_START`, `SEARCH_START`, per-move records and periodic `HEARTBEAT` events. Time fields include `delta_s` (since prior printed event), `elapsed_s` (since the game start), and `move_s` (observed move computation and process overhead). Successful game records are compressed to `stockfish_sessions/archives/game_XXXXXX.zip`; old retained archives are deleted when the configured **25 MB archive quota** is exceeded. Active logs and temporary files can use additional transient space, so this quota is **not a global filesystem cap**. Logs can be exported with `scripts/export_stockfish_logs.py` or `export_stockfish_logs.py` in a flat installation.

## 10. Reproducibility, limitations and research roadmap

The release includes the documented SDK smoke output, a complete graph catalog and supporting scripts. Selected tests include the supervisor, V8 progress and V10 tactical-policy tests. The release SDK smoke and the mock UCI controller passed in the development environment. **Real V10 games have now been performed on the user system:** 250 bounded-index results are present, but a **separate frozen-model strength-validation tournament and a verified strength improvement are still open**. The original 48-feature model compresses board structure and may miss deeper tactics. Increasing graph length cannot by itself compensate for inadequate search depth or feature information.

The most informative next study is an independent Stockfish match series across a frozen baseline and a promoted V10 graph, with identical openings, balanced colors, predefined resource limits and a disjoint evaluation set. Report both game outcomes and candidate rejection reasons. See [`V10_RELEASE_VALIDATION.md`](V10_RELEASE_VALIDATION.md), [`docs/V10_TACTICAL_GRAPH_EVOLUTION.md`](docs/V10_TACTICAL_GRAPH_EVOLUTION.md), and the [current whitepaper](JOSHUA_Chess_Research_Whitepaper_EN.pdf).

**Primary technical references:** [Stockfish documentation](https://official-stockfish.github.io/docs/), [Stockfish source and license](https://github.com/official-stockfish/Stockfish), [paceval API](https://paceval.com/api/), [paceval developers](https://paceval.com/developers/).
