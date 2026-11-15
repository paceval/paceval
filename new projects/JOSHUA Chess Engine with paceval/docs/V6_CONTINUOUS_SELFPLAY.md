# JOSHUA V6: Continuous paceval Self-Play and Learning-Evidence Log

## What this release does

JOSHUA continuously plays chess against itself without an external chess engine. A Linux x86-64 supervisor starts a fresh original-JOSHUA child for every game, then validates and stores the new game data, writes a structured list of experimental follow-ups, and proceeds to the next game. `--max-games 0` means **unbounded game count** until stopped by a signal, storage exhaustion, or a detected engine error. Every completed game is saved before the next is started.

The supervisor **never evaluates chess score formulas itself**. Chess feature evaluations and mathematical decisions are made by the original local paceval code in `src/joshua.cpp` or `src/joshua_long_graph.cpp`, depending on the configured mode. The subprocess boundary is essential: it releases paceval handles and other allocations at the end of each game. It also limits the damage from a failed or memory-intensive graph compilation to the current game.

## Two mathematical execution paths

**`--mode alphabeta` or `--mode research`:** Starts `bin/joshua` for a complete game. The Alpha-Beta host manages pruning and the transposition table while paceval evaluates the V3 or trained V4 position-score graphs. In research mode, paceval also evaluates minimax reductions in batched persistent graphs. Model 4 evaluates a bounded residual of a small previously trained neural model in paceval graphs. The V4 weights are NOT updated by this release.

**`--mode longgraph`:** Starts `bin/joshua_long_graph` for **every selected move**. This explicitly constructs a new legal finite-horizon minimax expression with infix `min` and `max`, evaluates it in the **original paceval runtime**, verifies it against a separate C++ minimax reference, and discards its process resources before the next move. This is an experimental alternative to standard search and is limited by graph size, available memory, and fixed finite search depth. It is NOT an unlimited chess-lookahead solver. A known legal first move can be forced in either mode to vary games reproducibly; forced moves are not engine-selected.

For each graph-mode ply, the supervisor checks the original C++ program's selected UCI move against the legal chess rule generator, verifies FEN transitions, checks both mathematical audit flags and reconciles every sorted root candidate. Exact V5 expressions and per-ply evidence remain in each `ply_XXX` folder.

## Recommended startup

Copy an authorized original compatible `libpaceval_linux_sharedLIB.so` into `runtime/`, then run from the extracted repository:

```bash
./scripts/run_continuous.sh --mode alphabeta --model 4 --depth 2 \
  --quiescence 2 --plies 160 --max-games 0 --opening cycle
```

For repeated full decision graphs instead:

```bash
./scripts/run_continuous.sh --mode longgraph --model 4 --depth 2 \
  --quiescence 0 --max-nodes 250000 --max-chars 5000000 \
  --plies 160 --max-games 0 --opening cycle
```

Stop with Ctrl+C, preferably between games. An interrupted game is **not** reported as completed and may contain partial files. The manager stops on any engine error instead of repeatedly restarting a broken process. Reusing the same output directory resumes at the next free `game_NNNNNN` number.

For a bounded verification run, replace `--max-games 0` with `--max-games 2` and keep the full `sessions/` folder.

## Persisted files

Every finished game gets its own `sessions/game_NNNNNN/` directory. It contains `selfplay_timeline.csv`, `root_move_rankings.csv`, `game_uci.txt`, `run_evidence.json`, `end_state.json`, `learning_report.md`, `analysis_queue.csv`, and the console trace when applicable. Alpha-Beta/research mode also generates a standard SAN `game.pgn`. V5 longgraph mode stores one exact graph trace in each `ply_NNN/` subdirectory and a UCI move file; it does not pretend that this UCI-only file is SAN PGN.

The session directory also contains:

| Output | Use |
| --- | --- |
| `learning_log.md` | Human-readable game-by-game findings appended after each completed game |
| `learning_events.jsonl` | One machine-readable JSON object per completed game; suited for future tools or ChatGPT analysis |
| `games_index.csv` | Persistent outcomes, plies and diagnostic aggregate counters |
| `analysis_queue.csv` | Review candidates with **original FEN, UCI move and proposed follow-up** |
| `manager_errors.log` | Failure information; the manager stops rather than spins on repeated engine errors |

**Suggested files to bring back to the next chat:** `learning_log.md`, `learning_events.jsonl`, `games_index.csv`, `analysis_queue.csv`, and selected `game_NNNNNN/` directories containing full mathematical output. For V5 graph investigations, include the corresponding `ply_NNN/` directory, as it contains the complete expression and the independent minimax check.

## Diagnostic triggers and their meaning

- **EVALUATION_REVERSAL:** The white-perspective score of successive root searches changed by at least 250 centipawns. This may indicate a horizon effect or tactical instability, but the alternating side and finite depth can also explain the shift. **This does not prove a blunder.** The queue suggests rerunning the exact FEN at greater depth and changed quiescence, then inspecting the resulting line independently.
- **CLOSE_ROOT_CHOICES:** The leading alternatives differ by at most 12 centipawns. This marks a potentially sensitive root choice. It is NOT evidence of an incorrect choice.
- **REPEATED_POSITION:** A prior board state recurred under the conservative FEN four-field key. This is a signal to test history-aware evaluation and draw avoidance. The classical self-play program uses its own more exact en-passant repetition handling; these concepts are deliberately not conflated.
- **DRAW_MECHANISM:** A chess rule ended the game as a draw. Threefold and fifty-move outcomes use the program's documented auto-claim policy.
- **MOVE_LIMIT:** The configured maximum halfmove count stopped the search. The result is `*`, **not a fabricated draw**.
- **DECISIVE_GAME:** The chess host reported a genuine legal checkmate. This is not proof that either side played optimally.

Thresholds are heuristics chosen to produce a focused research queue. They are not calibrated model-strength metrics. Recommendations are hypotheses, not online training. This version does not secretly change neural weights, search algorithms, or paceval graph formulas after a game. To measure improvements, compare fixed-FEN holdout suites under identical rules and model versions, with independent move-legality and tactical checks.

## Reproducibility and boundaries

- The position evaluator's graph construction is unchanged unless explicitly noted. In the V5 full-graph mode a **new** decision graph is compiled for each **engine-selected halfmove**.
- Distinct games are obtained through a deterministic rotation of 14 legal initial moves. This is controlled opening diversity, **not random self-play or reinforcement learning**. It repeats after 14 games. `--opening fixed --first-move e2e4` fixes the opener; omit `--first-move` to let the engine choose it.
- The game result is explicit: `1-0`, `0-1`, `1/2-1/2` or `*`. The terminating event is saved separately from the score.
- Full paceval graph-point counters are available in the classic `joshua` evidence. The V5 full-graph driver does not export this counter and the supervisor records that fact instead of inventing it.
- Unlimited numbers of games create **unbounded disk usage**. Archive or rotate entire completed game folders deliberately; never delete one while it is active. The system is not designed as a fault-tolerant distributed scheduler.
- The supplied Linux ELF binaries were built on a current x86-64 Linux system. Rebuild locally if the target distribution's glibc or libstdc++ is incompatible.
- The original paceval library is a required **external** dependency. The included optional `paceval_runtime_loader.cpp` forwards to its genuine FFI symbols via `dlopen`/`dlsym`. It does not implement any arithmetic or simulate the SDK. The correct runtime ABI and actual gameplay require verification on the machine where the official library is installed.

## Empirical verification status of this release

The supervisor, JOSHUA and JOSHUA V5 full-graph source programs compile to Linux x86-64 ELF files using the provided original `paceval_main.cpp`/`.h`. With no local compatible runtime `.so` available in the build environment, **no new live paceval chess game was executed**. Manager-process regression tests ran on clearly labelled fake runners that copy historical result fixtures and demonstrated repeated games, resumed indexing, failure stop and correct JSONL/CSV files. A separate recorded eight-ply V5 fixture was replayed with the source-level legal chess transition checks. None of this is presented as a fresh paceval execution. See [`../V6_RELEASE_VALIDATION.md`](../V6_RELEASE_VALIDATION.md).
