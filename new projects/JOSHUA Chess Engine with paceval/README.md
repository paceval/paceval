# JOSHUA V10: Adaptive paceval Chess Graphs vs Stockfish

![JOSHUA chess research](figures/JOSHUA_Chess_Research_Cover_2400x1200.png)

JOSHUA is an experimental chess engine written in C++17. It uses the **original paceval Mathematical Engine** to evaluate mathematical chess-position models and reusable decision computations. Stockfish acts as an independent UCI opponent and diagnostic reference. The project explores whether carefully tested, versioned mathematical evaluation graphs can improve chess decisions without rewriting or recompiling the engine after every experiment.

This is a chess research demonstrator, **not** a claim of professional playing strength or proof that paceval replaces a production chess engine. The included historical PDF documents earlier JOSHUA research, not V10 Stockfish performance.

## 1. Scientific use case and current state of the art

Chess engines must evaluate legal moves while searching a large branching tree. Conventional alpha-beta engines such as Stockfish use advanced search heuristics and learned evaluation. JOSHUA investigates an alternative combination: a C++ chess-rule/search host with persistent paceval computation graphs for the numeric position scoring. Separate UCI games test the resulting decisions and record their limitations. Stockfish is the chosen reference because its Linux UCI interface supports reproducible searches with controlled settings. Leela Chess Zero could be added as a separate neural-network-based opponent in future work.

The inputs are legal FEN positions, a versioned model TSV, a fixed opening schedule and configuration for both engines. The main outputs are SAN/PGN games, per-move timing, independent reference scores, tactical error reports, complete paceval graph expressions and graph-version acceptance records.

## 2. Ready-to-run Linux x86-64 installation

**For an existing `~/Dropbox/joshua_autoplay` directory containing your original `libpaceval_linux_sharedLIB.so`:** use the separate V10 flat binary ZIP and extract it directly there. No rebuild is necessary. Keep existing `stockfish_sessions/` and `selfplay_sessions/` untouched. Stop running engines before the update. Linux commands:

```bash
cd "$HOME/Dropbox/joshua_autoplay"
unzip -o "$HOME/Downloads/JOSHUA_V10_Flat_Linux_x64.zip"
chmod 755 joshua joshua_referee joshua_selfplay joshua_long_graph run_stockfish_matches.sh
# Only if not already installed: sudo apt-get install stockfish
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 2 --progress-seconds 5
# Unlimited matches after a successful two-game check:
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 0 --progress-seconds 5
```

Run without `sudo`. The scripts default to the existing library in the same directory. You can also set `PACEVAL_RUNTIME` to its absolute path. Stockfish is an external GPLv3 program and is **not** bundled. The original paceval `.so` is not distributed in this public GitHub repository; keep your authorized copy in place. The binaries require compatible Linux x86-64 and glibc.

**For a full GitHub checkout**, use:

```bash
./scripts/install_flat_linux.sh "$HOME/Dropbox/joshua_autoplay"
# Or directly from the full repo after supplying runtime:
PACEVAL_RUNTIME=/absolute/path/libpaceval_linux_sharedLIB.so \
  ./scripts/run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 2
```

For a source rebuild, use `cmake -S src -B build -DCMAKE_BUILD_TYPE=Release`, `cmake --build build -j 2`, then `ctest --test-dir build --output-on-failure`. The default dynamic forwarding adapter still requires a **real**, compatible paceval shared object when running.

## 3. Human-readable paceval graphs: TXT and CSV

Each actual Joshua engine invocation now exports:

| File | Content |
|---|---|
| `paceval_graph.txt` | Actual adaptive expression, formula version and variable list |
| `paceval_graph_terms.csv` | Coefficients and component expressions, including nonlinear terms |
| `paceval_all_graphs.csv` | **Every graph registered** during that engine process, all variables and full formula text, plus `evaluated_points` for actual execution |
| `run_evidence.json` | Reconciliation of graph and evaluation counts, search mode and version |

For automatic Stockfish sessions the **latest authentic graph** can be inspected without unzipping:

```text
stockfish_sessions/
  active_graph.tsv                 # active version: editable numeric model data
  active_graph_expression.txt      # actual C++ / paceval compiled expression
  active_graph_terms.csv           # component descriptions and coefficients
  active_full_graph_catalog.csv    # all runtime graphs and evaluated point counts
  strength_summary.json            # historical match evidence by version + settings
  archives/game_000001.zip         # game, moves, engine logs and formula evidence
```

Within each retained game archive, inspect `joshua_ply_*/paceval_all_graphs.csv` or `joshua_ply_*/paceval_graph.txt`. Original V4 neural graph formula literals are also preserved under [`formulas/v4_graph_expressions.tsv`](formulas/v4_graph_expressions.tsv) in the full GitHub package.

A **graph registered** is not automatically a **graph executed**. The new `evaluated_points` column is zero for a registered but unused graph and counts actual engine evaluation points otherwise. The full catalog is generated from the real `Engine::create/eval/multi/single` paths, not reconstructed from console descriptions.

## 4. Nonlinear tactical formula versioning

V9 could only update eight fixed linear weights. V10 adds eight approved nonlinear tactical templates: `king_alarm`, `king_tactics`, `hanging_pressure`, `queen_exposure`, `rook_exposure`, `check_pressure`, `pawn_race`, and `active_captures`.

A representative white-oriented scoring formula is:

```math
S = S_{\mathrm{base}} + \min\left(160,\max\left(-160,\sum_i a_i f_i + \sum_j b_j g_j\right)\right).
```

For example, the real `king_tactics` component is

```math
g_{\mathrm{king}} = D_b(1+Q_b+R_b) - D_w(1+Q_w+R_w).
```

where $D$ is the count of king-neighbor squares attacked, and $Q,R$ encode queen/rook threats. These are limited chess-position heuristics, not proofs of forced tactics. The `hanging_pressure` term squares the already extracted hanging-piece counts. The host extracts these board features in C++; the entire weighted model, including the nonlinear terms, is evaluated by the original paceval engine.

A coefficient in the active TSV can be written as:

```text
version	1
mobility	0.0000
...
feature.king_tactics	-0.5000
```

The `...` above is explanatory only; real TSV files must contain all eight original base weights exactly once. The parser validates a known template name and a finite decimal coefficient. **It never executes user-supplied mathematical formula strings.** At most six additional nonlinear terms may be active; this limits graph complexity and prevents arbitrary formula injection. Each successful version is frozen for an entire opening/color pair.

## 5. Automated learning and independent controls

After matched White/Black games, JOSHUA analyzes poor decisions using Stockfish at a fixed node count, with its search hash reset on every reference query. Terminal mates are identified separately. Other mistakes use a **bounded heuristic loss**, not a naive average of gigantic artificial mate centipawns:

```math
p(c)=\frac{1}{1+\exp(-c/180)},\qquad
L=100\max(0,p_{\mathrm{before}}+p_{\mathrm{after,opponent}}-1).
```

This is an **illustrative expected-score transform, not Stockfish's calibrated WDL model**. Checkmates are explicitly mapped to terminal values. The per-move `loss_pp` is in heuristic expected-score **percentage points**. Stockfish's original UCI `score cp` / `score mate` information is retained separately in JSON, and tactical errors go to `tactical_findings.csv`.

From the worst recorded positions the controller proposes up to four bounded candidate coefficient changes, including structural nonlinear terms. It runs **actual Joshua + paceval decisions** on training positions and separate reference FENs. No graph is promoted merely because its expression is longer. A candidate must change at least one decision, improve the training objective, not worsen the average held-out loss and stay within per-position regression limits. Failed candidate creation or evaluation is a rejected trial. Promotion is marked **provisional**, not a global strength improvement.

By default, a model remains active for at least **four complete alternating-color pairs** (`--minimum-pairs-per-version 4`) before another update is attempted. Lower the threshold only for controlled research. A saved active TSV is read on every new game, so an accepted version takes effect **without recompilation**. The previous TSV and full candidate-trial evidence are preserved in game ZIPs.

## 6. Estimating actual playing strength

The `strength_summary.json` file distinguishes a score against fixed Stockfish settings from an absolute Elo rating. It groups matches by Stockfish identity, node limit, skill, Joshua depth, quiescence and graph version. Version comparisons require **matching complete color pairs with the same opening**, and at least eight distinct common openings for an exploratory sign-test. The `NOT_ESTABLISHED` status is not evidence that two engines are equally strong. The result remains provisional due to opening correlations, deterministic repetition, small samples and reference configuration dependence. A genuine improvement should be confirmed in repeated independent test series with a frozen model and consistent opponent settings.

The engine's original chess search is intentionally retained. Larger graphs can enrich positional evaluation but cannot replace an adequate tactical search depth. See [V10 research details](docs/V10_TACTICAL_GRAPH_EVOLUTION.md) and [test evidence](V10_RELEASE_VALIDATION.md).

## 7. Ongoing logs and timing

`delta_s` measures time since the prior printed diagnostic. `elapsed_s` measures time since the beginning of the game. Each completed move has `move_s`, including process startup and engine evaluation. A periodic `HEARTBEAT` appears during a long search. Every completed game is ZIP-compressed. Older ZIP files are deleted on exceeding the **25,000,000 byte retained-archive limit**. Active current-game files and temporary ZIPs require additional transient disk space and are independently bounded where supported. Logs may be exported with `python3 export_stockfish_logs.py` (flat installation) or [`scripts/export_stockfish_logs.py`](scripts/export_stockfish_logs.py) (full package).

## 8. Build, audit, and limitations

The genuine x86-64 JOSHUA binary was compiled here and tested against the **original paceval shared object supplied in the user's existing installation archive**. The test created and evaluated new nonlinear graphs and reconciled registered/evaluated graph counts. The UCI matchcontroller was checked with actual Joshua+paceval but a **mock Stockfish protocol peer**. Real full Stockfish-vs-Joshua games were previously provided by the user for V9, but **no new real Stockfish V10 strength match was run here**. The mock promotion and statistical-control tests exercise software behavior only; they are not evidence of chess improvement. See [`V10_RELEASE_VALIDATION.md`](V10_RELEASE_VALIDATION.md).

Previous research documentation remains accessible in [`docs/V10_TACTICAL_GRAPH_EVOLUTION.md`](docs/V10_TACTICAL_GRAPH_EVOLUTION.md) and the original historical PDF [`JOSHUA_Chess_Research_Whitepaper_EN.pdf`](JOSHUA_Chess_Research_Whitepaper_EN.pdf). The original SDK files are in `src/`, while the proprietary runtime stays external. Stockfish upstream: <https://github.com/official-stockfish/Stockfish>.
