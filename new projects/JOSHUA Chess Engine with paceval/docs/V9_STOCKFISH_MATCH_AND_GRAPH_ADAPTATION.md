# JOSHUA V9: Stockfish matches, debugging times, and validated paceval graph evolution

## Purpose and architecture

JOSHUA V9 adds an external UCI opponent without changing the legal chess rules or moving the mathematics out of the original paceval runtime. It is a research loop, not proof of self-improving playing strength.

The Linux program `bin/joshua` remains the C++ chess engine. For every JOSHUA move the Python coordinator launches this real binary with `--model 4 --fen ... --plies 1 --graph-file ...`, reads the single move from its actual `selfplay_timeline.csv`, and verifies the associated `run_evidence.json` reported successful adaptive paceval graph evaluations. Its separate chess referee, `bin/joshua_referee`, uses JOSHUA's own legal move generator. Stockfish is launched via the standard UCI protocol as an external process. No Stockfish mathematics is presented as paceval mathematics.

The public Stockfish repository is <https://github.com/official-stockfish/Stockfish>. Stockfish is GPL-3.0 licensed. It is not bundled with this ZIP. A locally installed Stockfish executable is required. JOSHUA's original proprietary paceval runtime is also required separately and is not redistributed.

## Usage

Stop existing games with Ctrl+C. Never run `sudo ./joshua_selfplay` or the match script. Preserve your existing `selfplay_sessions` folder by using the installer.

```bash
# Debian or Ubuntu, where available:
sudo apt-get update
sudo apt-get install stockfish

# Unpack this GitHub ZIP, then update the existing installation:
./scripts/install_flat_linux.sh "$HOME/Dropbox/joshua_autoplay"
cd "$HOME/Dropbox/joshua_autoplay"

# For your existing installation the paceval .so is already here:
export PACEVAL_RUNTIME="$PWD/libpaceval_linux_sharedLIB.so"

# Prove the first two-color cycle before continuous operation:
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 2

# After the first experiment, continue indefinitely:
./run_stockfish_matches.sh --stockfish /usr/games/stockfish --max-games 0
```

The default Stockfish binary may instead be in the shell `PATH`. For a fresh source checkout, run `./scripts/run_stockfish_matches.sh` and place the original paceval `.so` in `runtime/`.

Relevant switches include `--depth 2`, `--quiescence 2`, `--stockfish-nodes 1000`, `--teacher-nodes 2500`, `--stockfish-skill 20`, `--progress-seconds 5`, `--opening cycle|none`, `--adapt` and `--no-adapt`. Node budgets are reproducible search limits, not equal search difficulty across engines. `--stockfish-skill` changes the match opponent but not the independent full-skill teacher. The maximum retained archive footprint defaults to 25,000,000 bytes. `--max-plies 400` is a safety cutoff; a capped game is marked unfinished, not a draw.

## Debug logging and time interpretation

Each console line uses an ISO timestamp and monotonic, seconds-based fields:

- `delta_s`: seconds since the previous emitted debug line, regardless of the event type.
- `elapsed_s`: seconds since the current game's debug logger was initialized.
- `move_s`: wall-clock seconds from the start of the current move calculation to the received move. For JOSHUA it **includes** process initialization, SDK graph creation, search, and CSV output. It does not represent the search stage alone.
- `search_s`: heartbeat time currently spent waiting for the move. Heartbeats appear even when JOSHUA or Stockfish produces no completed move.
- `grading_s`: additional elapsed seconds taken by independent Stockfish quality evaluation. This is **not** part of `move_s`.

Example line shape (illustration, **not a measured game**):

```text
2026-11-15T14:01:23+00:00 MOVE delta_s=4.217 elapsed_s=21.104 ply=12 actor="JOSHUA" uci="g8f6" san="Nf6" move_s=4.217 score=null
```

The full debug timeline is inside each game ZIP under `debug_timeline.log`. Each game ZIP also includes `moves.json`, `game.pgn`, per-ply JOSHUA search and formula evidence, `joshua_stockfish_grades.json`, `model_used.tsv`, `adaptation.json`, and `summary.json`. The state files `strength_summary.json`, `active_graph.tsv`, `next_game_id.txt` and `latest_game.txt` remain in the session root. The main match index keeps a bounded recent window. The oldest ZIPs are deleted when the retained log limit is exceeded, so export snapshots regularly when long-term study matters.

## Fairness and reproducibility

A match begins with Stockfish as White and JOSHUA as Black. The next match reverses colors. By default, the opening book chooses one of fourteen **forced** legal first moves. The same first move is imposed for the pair of opposite-color matches, and the logs explicitly label it as an opening book move rather than a move selected by either engine. This gives controlled position diversity and partial color pairing. Disable it with `--opening none` for unrestricted engine-selected openings. A repeated opening or later position can still produce the same moves.

A version cannot change in the middle of an opening/color pair. After the first game its training proposal is deferred, and after the second game its graph version can be revised for the next pair. Match conclusions must control opponent version, node limit, opening, colors, and model version.

Result accounting distinguishes `1-0`, `0-1`, `1/2-1/2`, and `*` unfinished or interrupted. W/D/L, average match points, and the Stockfish evaluation of JOSHUA's moves are reported separately. An optional relative Elo score transformation describes the match score against **this configured opponent only**. It is not a FIDE or absolute engine rating and may be unavailable when all observations are wins or losses. Small and non-paired samples do not establish changes in engine strength.

## Mathematically defined adaptive paceval graph

The C++ neural V4 evaluator computes its normal base position score `B(x)` from the original paceval graphs. A new persistent paceval graph computes the full modified evaluation:

```math
S_v(x)=B(x)+\min\!\left(160,\max\!\left(-160,\sum_{i=1}^{8}w_{v,i}\,d_i(x)\right)\right).
```

The eight explicit feature-difference terms are `mobility`, `captures`, `hanging`, `attacked`, `passed`, `kingdanger`, `queenthreat`, and `rookthreat`. Their exact V4 input-name mapping is in [`src/adaptive_score_graph.h`](../src/adaptive_score_graph.h). The bounded weights are loaded from `active_graph.tsv`. Only strict decimal literals, a numeric version and these eight predefined terms are accepted. Arbitrary formula text from an external log or CSV is rejected. The expression remains bounded and can grow as additional terms acquire nonzero weights, without recompiling the C++ program.

The C++ search runs the actual compiled graph on each evaluated V4 feature row. The batch evaluation path uses the existing paceval API when the model uses batches. C++ still controls legal move generation, alpha-beta, and game decisions. The graph file is reloaded **between games**. Existing original paceval SDK APIs, features, and errors are not substituted or simulated during genuine match mode.

After a completed paired game, the coordinator selects up to two earlier JOSHUA decisions with substantial Stockfish-observed loss. It proposes a bounded positive and a bounded negative coefficient change for a rotating feature term. Each proposal is evaluated using **the actual JOSHUA executable and paceval graph** on the same training FEN positions and on separate fixed holdout opening positions. A proposal is promoted only when it changes an actual selected move, improves the mean reference loss on training positions by the specified minimum, and does not worsen the mean holdout loss or violate a per-holdout regression limit. Otherwise the current coefficients are retained and the rejected proposal is logged. Promotion is atomic, versioned and reflected in the next match pair.

This is **limited, heuristic, validation-gated online coefficient search**, not arbitrary source-code generation, general symbolic discovery, mathematical proof of optimality or guaranteed stronger chess play. The default holdout is small. Promotions are provisional. A larger fixed holdout, independent longer matches, and confidence intervals are required before calling a version objectively stronger.

## Test scope and limitations

The release build contains four x86-64 ELF programs and the Python match coordinator. The SDK-independent offline mock regression covers two opposite-color games, a real C++ legal-move referee, log timing fields, ZIP CRC tests, archive rotation, coefficient-injection rejection and simulated promotion/rejection logic. The mock is explicitly not Stockfish and does not execute paceval. These tests do not establish successful real Stockfish matches or real adaptive paceval graph compilation in this environment because the original runtime and Stockfish binary were not supplied here.

Run the first two real games on your Linux machine with the actual `.so` and genuine Stockfish installed. Use the saved logs to verify FEN consistency, actual paceval graph use, candidate acceptance and time behavior before running indefinitely.

## Export for human analysis

From the full GitHub checkout:

```bash
python3 scripts/export_stockfish_logs.py --session stockfish_sessions --output JOSHUA_Stockfish_Study.zip
```

For a flat installation, run `python3 export_stockfish_logs.py --session stockfish_sessions --output JOSHUA_Stockfish_Study.zip`. The export contains only retained game archives and the latest model/summary. Games already pruned by the 25 MB retention mechanism cannot be recovered from the export.
