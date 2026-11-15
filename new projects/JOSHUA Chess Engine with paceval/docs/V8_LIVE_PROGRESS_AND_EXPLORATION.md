# JOSHUA V8: Live progress and reproducible self-play diversity

## Why V7 appeared inactive

V7 redirected the chess engine's stdout and stderr into `game_console.log` and did not mirror it to the terminal during a game. A deep search could therefore display only `GAME_START` for a long interval even though the engine was running. V8 reads the child's real console file while it runs. The engine explicitly flushes its console messages even when stdout is redirected to a regular file.

## Live messages

The Linux x86-64 supervisor displays concise lines that do not require decoding the raw JSON or CSV traces:

| Message | Meaning |
|---|---|
| `GAME_START` | Partienumber, controlled first move, seed, exploration settings |
| `OPENING` | Applied first move, if forced |
| `SEARCH` | Engine started thinking about the next halfmove; legal move count |
| `HEARTBEAT` | Time since the current child was started, active halfmove, most recent completed move, current stage and consumed console-log bytes |
| `DIVERSITY` | Number of eligible alternatives, policy-best move, played move, evaluation loss and deterministic seed |
| `MOVE` | Completed search result, chosen UCI move, SAN notation and white-perspective score |
| `GRAPH_START` / `GRAPH_MOVE` | V5 full decision-graph rebuild starting or completing for the given halfmove |
| `GAME_END` | Chess result and actual termination reason; `max_halfmoves` is not a draw |
| `ARCHIVE_COMMITTED` | ZIP archive and retained disk usage after rotation |

`--progress-seconds 5` gives an independent heartbeat at five-second intervals while the engine is still computing. Set `--progress-seconds 1` for more frequent output, or `0` to disable heartbeats while retaining completed move lines. A heartbeat proves that the supervisor and process are still observable, not that the chess search is guaranteed to terminate. Raw engine stdout, position history and scientific evidence stay in each retained game ZIP. There is no second unbounded live-log file.

## Eröffnungsvielfalt (opening variation)

V7 already cycled through the following fourteen *legal first White moves* (in UCI notation):

`e2e4`, `d2d4`, `c2c4`, `g1f3`, `b1c3`, `e2e3`, `d2d3`, `g2g3`, `b2b3`, `f2f4`, `a2a3`, `h2h3`, `a2a4`, `h2h4`.

Consequently, adjacent games in one uninterrupted cycle have different first moves. The rotation repeats after fourteen games. Previously the engine's subsequent choices were deterministic for identical positions and search settings. Thus distinct first moves did **not** guarantee distinct complete games once a sequence repeated.

V8 keeps the reliable initial move cycle and adds *controlled near-best exploration* in the first fourteen halfmoves by default. Once the normal local paceval-backed search returns its sorted, per-root evaluations, the host considers only alternatives whose evaluated loss against the optimal root is no more than `--explore-cp 30` (using the project's white-perspective chess evaluation scores). The host selects an eligible move deterministically using the explicit game seed and position FEN. The same seed, position and search scores reproduce the same choice. Different game numbers shift the seed, so repeated positions with at least two eligible candidates can produce different continuation moves. If no alternative qualifies, the best-ranked move is played.

The host does **not** replace the mathematical evaluation with random chess scores; all root scores still come from original paceval graph results. This is an *experimental trajectory-sampling policy*, not a strength improvement, trained chess engine, learning-rate change, proof of opening theory, or guarantee of unique complete games. Short search depths may mis-rank candidate moves. Do not interpret the exploration choice as a search blunder without comparing the original best-ranked alternative.

### Selection and audit details

For sorted candidate scores $S_1,S_2,\ldots$ measured from White's perspective, the reported relative cost is

$$
L_i = \begin{cases}
S_1-S_i & \text{White to move},\\
S_i-S_1 & \text{Black to move}.
\end{cases}
$$

Eligible candidates satisfy $0\leq L_i\leq\Delta$, where $\Delta$ is the `--explore-cp` limit. The C++ host chooses a candidate index using a stable FNV-1a hash of the initial FEN for that search, the halfmove number and the per-game integer seed. The hash affects selection only. The evaluations themselves remain the existing paceval computations. The stable method permits deterministic replays; it is not cryptographic randomness.

`root_move_rankings.csv` retains the authentic best-first ranking. The new `selected` column marks the actual played move with `1` and all others with `0`. `selfplay_timeline.csv` records the selected score and actual FEN transition. The independent Python audit checks the selected row and admissible evaluation loss, rather than incorrectly assuming rank 1 must have been played. The per-game `learning_report.md` records controlled-exploration decisions separately from suspected evaluation errors. Full-graph mode preserves the independently verified exact minimax *best* in each `ply_NNN/run_evidence.json` and separately records the exploratory *played* move in the top-level game CSV.

### Run modes

```bash
# Recommended diversity, 14 rotating first moves and near-best exploration.
PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so" \
  ./joshua_selfplay --max-games 0 --opening cycle \
  --explore-cp 30 --explore-plies 14 --progress-seconds 5

# More conservative experiment with zero difference in selected move scores.
PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so" \
  ./joshua_selfplay --max-games 0 --opening cycle \
  --explore-cp 0 --progress-seconds 5

# No forced first move. From the initial position, JOSHUA itself selects one.
PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so" \
  ./joshua_selfplay --max-games 0 --opening engine \
  --explore-cp 30 --explore-plies 14

# Long-graph: V5 paceval decision graph rebuilt before every halfmove.
PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so" \
  ./joshua_selfplay --mode longgraph --model 4 --depth 2 --quiescence 0 \
  --opening cycle --max-games 0 --progress-seconds 5
```

The examples above assume the three compiled programs and original authorized runtime `.so` are in the current directory. A GitHub checkout instead uses `./scripts/run_continuous.sh`, which looks for the authorized `.so` under `runtime/` unless `PACEVAL_RUNTIME` is set.

## Retention, error handling and permissions

V8 preserves the V7 25,000,000-byte (decimal 25 MB) retained-log archive rotation and active-output guard. Each game is ZIP-compressed after it terminates; the oldest archive is deleted first, and only the latest top-level summary is retained. Disk space can temporarily exceed the retained-log limit during an active game or ZIP commit. The independent live heartbeat does not write an additional ever-growing logfile.

Run as a normal user, not `sudo`. If previous runs created root-owned session files:

```bash
sudo chown -R "$(id -un):$(id -gn)" ./selfplay_sessions
chmod -R u+rwX ./selfplay_sessions
```

For a running Joshua instance, press **Ctrl+C** before installing a new executable. Keep the original paceval shared library in place and never claim the redistributed program contains the actual proprietary runtime.

## Test scope

Standalone tests reproduce deterministic exploration for both White and Black with no paceval dependency. Mock-child process tests prove live search, move and heartbeat messages and ZIP retention. The historical eight-halfmove V5 graph trace is replayed with exploration disabled, while a separate four-game mock process test demonstrates distinct selected moves from identical prerecorded V5 root-score vectors. All mock tests are explicitly marked as replay/supervision tests, **not new original paceval chess executions**. An end-to-end live engine test with the authentic `libpaceval_linux_sharedLIB.so` remains necessary on the machine where that runtime is installed.
