# JOSHUA V11 | Chess Research with Verified paceval Graph Evolution

![JOSHUA chess research](figures/JOSHUA_Chess_Research_Cover_2400x1200.png)

**Research release:** 17 November 2026  
**Platforms:** Linux Intel/AMD x86-64, C++17 engine, Python 3 UCI match controller  
**Status:** Real mathematical graph execution and challenger gate verified; **no verified increase in chess playing strength**.

JOSHUA is a research chess engine with a C++ chess-rule/search host and the **original paceval Mathematical Engine** for classical, neural and versioned tactical scoring graphs. It plays Stockfish through a separate UCI interface. The new V11 controller rejects an experimental score graph unless it passes independent tactical-position checks **and** a color-paired chess match against a frozen copy of the previous graph. Formula selection and match orchestration remain in the host; all enabled tactical score formulas are evaluated by genuine paceval graphs.

The [current English research whitepaper](JOSHUA_Chess_Research_Whitepaper_EN.pdf) covers V11 and preserves the independently audited V10 Stockfish baseline as historical evidence.

## 1. Scientific use case and current state of the art

Chess is a strict test of numerical model changes: an alternative formula can improve one static position score but select worse moves in a game tree. Engines such as [Stockfish](https://github.com/official-stockfish/Stockfish) combine powerful search with neural evaluation. JOSHUA instead investigates reusable, inspectable mathematical scoring graphs and whether controlled changes improve decisions without rewriting C++ every game. No comparison of computational speed or general strength is claimed. [Stockfish UCI documentation](https://official-stockfish.github.io/docs/stockfish-wiki/Developers.html) and [paceval API](https://paceval.com/api/) describe the external interfaces.

Each experiment takes a legal FEN, a whitelisted versioned score model, a fixed search depth and independent opponent settings. JOSHUA's C++ referee checks legality and game endings. Stockfish grades decisions but **does not referee** the matches. A candidate model must survive a separately logged champion-versus-challenger gate before the active model changes.

## 2. What is actually new in V11?

| Change | Actual implementation | Evidence / limitation |
|---|---|---|
| Frozen champion | Original active TSV copied with SHA-256 before candidate testing | Champion is not changed during comparisons |
| Real color-paired challenger games | The V11 controller starts both versions of the authentic Joshua + paceval engine | 2 truncated test games, 38 actual selected engine moves; gate correctly rejected |
| Enforced promotion gate | Only completed decisive/drawn games count; a score threshold and win margin are required | Deterministic positive/negative test cases passed; **not a strength proof** |
| More tactical candidates | Two new nonlinear whitelisted feature-combination formulas | Both were registered and evaluated with the original paceval runtime |
| Search improvement | Bounded non-capture checking moves at the first quiescence horizon | Source compiled and sample FEN search executed; global advantage unproven |
| Immutable version snapshots | Saved in `stockfish_sessions/model_versions/`, at most 16 versions retained | Manual rollback is supported, no source recompilation |
| Live diagnostic timing | `delta_s`, `elapsed_s`, `move_s` on champion tests and Stockfish matches | Per-move timing is diagnostic, not a benchmark |

V11 does not create arbitrary free-form mathematics. The formula grammar remains whitelisted and tested. Its new templates are `king_check_combo` and `hanging_capture_combo`. The active model still permits at most six nonlinear terms at a time, with bounded coefficients.

## 3. Stockfish research results: historical V10 baseline

The **previous V10 upload** contained **250 completed Stockfish 16 games**: **0 JOSHUA wins, 8 draws, 242 losses**, with Joshua depth 2 and quiescence 2 versus Stockfish Skill 20 / 1,000 nodes per played move. Historical versions 0–7 were observed. No reliably improving series was demonstrated. These are V10 observations, **not V11 games**. See [the preserved numerical audit](results/REAL_STOCKFISH_AUDIT_2026-11-17.json) and [method details](docs/V10_REAL_MATCH_METHOD_AND_REFEREE_2026-11-17.md).

**V11 verified locally:** The original user-supplied paceval shared library ran the changed tactical graph. Separately, two authentic challenger/champion games with opposite colors reached the prescribed 20-ply test limit, and **no candidate was promoted**. All moves came from the actual engine. This is a functional test, not a genuine completed tournament or Elo result. Stockfish was not installed here for new V11 matches.

## 4. Install V11 directly over your working Linux folder

Use the separate `JOSHUA_V11_Flat_Linux_x64.zip` for your private `~/Dropbox/joshua_autoplay` folder. **Stop the running Joshua match controller first.** Unzip directly into that folder, then:

```bash
cd "$HOME/Dropbox/joshua_autoplay"
chmod 755 joshua joshua_referee joshua_selfplay joshua_long_graph run_stockfish_matches.sh
export PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so"
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 2 --progress-seconds 5
```

If these two tests pass, change `--max-games 2` to `--max-games 0`. **Do not use `sudo`.** This package preserves existing `stockfish_sessions` and `selfplay_sessions`. Stockfish must be installed separately. The official paceval library belongs only in your authorized local installation. It is **not included in the public GitHub ZIP**.

The full checkout uses `./scripts/run_stockfish_matches.sh`, requiring `bin/` and the external paceval runtime. To rebuild:

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --target joshua joshua_referee joshua_selfplay joshua_long_graph -j 2
ctest --test-dir build -R 'joshua_v10_tactical_graph_policy|joshua_v11_champion_gate_offline' --output-on-failure
```

For a research experiment with an explicit color-paired gate:

```bash
./run_stockfish_matches.sh --stockfish /usr/games/stockfish \\
  --max-games 0 --minimum-pairs-per-version 4 \\
  --champion-pairs 4 --champion-max-plies 100 \\
  --champion-min-score 0.625 --progress-seconds 5
```

`--champion-pairs 4` means four distinct test openings, each played twice with reversed colors (eight challenger/champion games). Longer completed matches are necessary for promotion. Truncated matches and draws without a sufficient win margin fail closed. The gate is a **conservative experimental filter**, not statistical certification of strength. More pairs provide a stronger sample but also require additional chess calculations.

## 5. Mathematical graph and why it changes

The inherited trained V4 support network accepts 48 features, uses 12 paceval sigmoid graphs and a fused output score. The adaptive correction is also a persistent paceval graph:

```math
S_{11}(s)=S_{4}(s)+\min\left(160,\max\left(-160,\sum_i a_i f_i(s)+\sum_j b_j g_j(s)\right)\right).
```

Only the bounded correction is clipped. C++ extracts board features and executes legal-tree search, while **paceval actually calculates this composite mathematical score**.

The two additional permitted terms are:

```math
g_{check}=I_b(1+D_b+Q_b)-I_w(1+D_w+Q_w)
```

```math
g_{capture}=H_b C_w-H_w C_b
```

Here $I$ is the in-check indicator, $D$ king-neighbor danger, $Q$ queen threat, $H$ hanging-piece count and $C$ pseudo-legal capture count. These are approximate tactical signals, **not proven forced tactics**. New model coefficients can lengthen or shorten the expression without recompilation. New arbitrary feature extraction or grammar does require new C++ code.

## 6. How a mathematical candidate is tested

1. A finished Stockfish-versus-Joshua color pair produces legal positions and Stockfish decision diagnostics. Mate findings are recorded separately from the bounded heuristic percentage-point loss.
2. The controller proposes at most four bounded coefficient/template changes. The **current active TSV is not changed**.
3. The actual Joshua binary evaluates candidate and old champion against selected error FENs and independent fixed FENs. A candidate must change at least one move, improve the training measure, respect every holdout loss bound and not introduce a new holdout mate alert.
4. Only a locally passing candidate enters the new **V11 challenger gate**: fixed withheld opening moves (`b2b4`, `c2c3`, `f2f3`, `g2g4`, `b1a3`, `g1h3`), each tested in both colors against an immutable copy of the incumbent.
5. Each move is generated by a separate real Joshua + paceval execution and checked by the C++ referee. Any incomplete game, missing graph, failed engine, invalid move or insufficient result rejects the candidate.
6. Only after the gate accepts are the candidate TSV and its actually generated paceval expression published as the active version. Both model snapshots and all accept/reject reasons are retained for analysis. A provisional local acceptance still does **not** prove stronger Stockfish tournament performance.

The manual rollback tool never edits the C++ binary. Check a historical saved model with:

```bash
python3 v11_restore_graph.py --sessions stockfish_sessions --version 7
```

Only after stopping the live matches, apply explicitly with `--apply`. The original model is backed up first. This is a research control, not automatic source rewriting.

## 7. What does the referee do?

`joshua_referee` implements independent rule enforcement, checks the complete FEN, enumerates legal moves, rejects illegal UCI choices and applies valid moves. It returns the next FEN, SAN notation, normalized repetition key, count of legal moves and terminal state (mate, stalemate or selected draw-claim conditions). The match controller tracks repetitions across the sequence. **The referee does not judge whether a legal move is strategically or tactically good**. Stockfish does that separately, with a bounded search and its own limitations. This is a demonstrator, not certified implementation of every tournament edge case.

## 8. Where is the *actual* paceval graph readable?

| File | Meaning |
|---|---|
| `stockfish_sessions/active_graph.tsv` | The currently active numerical coefficients and model version |
| `stockfish_sessions/active_graph_expression.txt` | The **actual full adaptive formula** exported by an executing Joshua process |
| `stockfish_sessions/active_graph_terms.csv` | All active component expressions and numeric coefficients |
| `stockfish_sessions/active_full_graph_catalog.csv` | All runtime-registered graph expressions including long V4 neural formulas; `evaluated_points` distinguishes used from unused |
| `stockfish_sessions/model_versions/version_0000007.tsv` | Frozen version snapshot, if preserved by a later V11 promotion |
| `stockfish_sessions/archives/game_XXXXXX.zip` | Game moves, referee/Stockfish grades, graph trials and full duel details after completion |
| [`formulas/observed_active_graph_v7.txt`](formulas/observed_active_graph_v7.txt) | Observed V7 mathematical expression archived from the previous match evidence |

For example, run `cat stockfish_sessions/active_graph_expression.txt`, then inspect `active_full_graph_catalog.csv` in a spreadsheet. An SDK computation graph itself is not a portable text object: these files record the *exact formula input and evaluated point counts* so it can be regenerated using the same SDK.

## 9. Reproducibility, limitations, and research documentation

The original Linux-x64 mathematical runtime from the previous upload was used to check new V11 graph expressions and a complete (but intentionally truncated) color-swapped duel. Regression policy tests check positive and negative outcomes, incomplete games and color mismatch. **No new real Stockfish tournament or statistically conclusive playing-strength gain was produced here.** The historical V10 result is still the benchmark against which a frozen V11 test must be conducted.

More detail: [V11 algorithms and release audit](docs/V11_CHAMPION_GATE.md), [V11 validation record](V11_RELEASE_VALIDATION.md), and [current whitepaper](JOSHUA_Chess_Research_Whitepaper_EN.pdf). Historical release notes remain labeled V5–V10. No performance speedups are claimed.
