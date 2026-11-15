# JOSHUA V6: Continuous Chess Self-Play with paceval Decision-Graph Evidence

![JOSHUA cover](figures/JOSHUA_Chess_Research_Cover_2400x1200.png)

**New in V6:** This ZIP includes three **compiled Linux Intel/AMD x86-64 executables** in `bin/`: `joshua` (classical/research), `joshua_long_graph` (new full mathematical graph for every move), and `joshua_selfplay` (indefinite self-play supervisor). The supervisor starts a fresh child process for each game, records a correctly classified result and all legal moves, saves a machine-readable learning-evidence queue and appends `sessions/learning_log.md` **after every completed game**. Both the model-4 graph path and the V5 full-graph alternative remain supported. No automatic weight modification or reinforcement-learning claim is made.

**Important runtime requirement:** The authentic `libpaceval_linux_sharedLIB.so` was not supplied, so the binaries' actual chess calculations **cannot run until the original paceval runtime is installed**. The optional `src/paceval_runtime_loader.cpp` contains only `dlopen` forwarding to real SDK FFI symbols, not a replacement math engine. The repo includes original `src/paceval_main.h` and `src/paceval_main.cpp`. GNU C++ runtime dependencies were linked statically for the three distributed binaries; compatible Linux glibc is still required. Original SDK runtime licensing must be respected and verified before redistribution.

**Quick start after placing your authorized library in `runtime/`:**

```bash
./scripts/run_continuous.sh --mode alphabeta --model 4 --depth 2 \
  --quiescence 2 --plies 160 --opening cycle --max-games 0

# The full V5 mathematical decision-graph rebuild before each selected move:
./scripts/run_continuous.sh --mode longgraph --model 4 --depth 2 \
  --quiescence 0 --plies 160 --opening cycle --max-games 0
```

Use Ctrl+C to stop. Set `--max-games 2` for a bounded first run. Reusing the session directory continues at the next free game number rather than overwriting earlier games. See [V6 continuous self-play design and evidence](docs/V6_CONTINUOUS_SELFPLAY.md), [V6 exact release validation](V6_RELEASE_VALIDATION.md) and [runtime installation](runtime/README.md). **The included historical English PDF describes the V5 research baseline.** New V6 behavior is documented in the two files just linked; the V5 PDF is not misrepresented as a V6 verification report.

---

## Preserved V5 research archive

### JOSHUA V5: Long Mathematical Chess Decision Graphs and Neural Support with paceval

**JOSHUA** is an English-language, Linux/C++ chess research program that plays both sides automatically. It uses the **original local paceval SDK** to evaluate reusable mathematical expressions. The MCP server, Stockfish, and Leela Chess Zero are not needed and are not invoked during a JOSHUA self-play game. JOSHUA's name is a tribute to the computer in *WarGames*, not a claim of association with the film.

The new optional **model 4** combines the transparent classical JOSHUA V3 score with a **genuinely trained** shallow neural network. The neural weights were learned from reproducibly generated legal chess positions labelled by JOSHUA's own **two-ply V3 minimax teacher**. They are not weights from Stockfish, Leela, or human grandmaster games. **Training-fit improvement is not proof of stronger chess play.** Models 1, 2, and 3 remain supported and unchanged.


[Current V5 release validation and test scope](V5_RELEASE_VALIDATION.md).

## V5: What is new and what is independently verified

**JOSHUA V5** adds an experimental, **full-width legal-tree-to-formula compiler** in
[`src/joshua_long_graph.cpp`](src/joshua_long_graph.cpp). The normal self-play engine
(`src/joshua.cpp`) and its V3/V4 search modes remain available as reference implementations.
The compiler performs legal chess enumeration in C++, evaluates leaf features through
**persistent local paceval V3 or trained-V4 graphs**, then emits one explicit, nested
`min`/`max` expression representing the exact finite-horizon decision tree.
A second C++ minimax implementation verifies the returned paceval value.
The same compiled graph is also evaluated with an independently perturbed leaf-score
vector, without recompilation, to test mathematical graph reuse.

Measured and executed on the available Linux system:

| Position / model | Depth (plies) | Legal tree nodes | Distinct leaf-score variables | Exact expression length | paceval graph creation | Graph evaluation |
|---|---:|---:|---:|---:|---:|---:|
| Initial position / V3 | 3 | 9,323 | 399 | 75,551 characters | 0.0396 s | 0.0010 s |
| Initial position / V4 | 3 | 9,323 | 2,893 | 83,672 characters | 0.0764 s | 0.0011 s |
| Initial position / V3 | 4 | 206,604 | 3,436 | 1,857,759 characters | 1.5919 s | 0.0180 s |
| Initial position / V4 | 4 | 206,604 | 40,946 | **2,088,691 characters** | **16.4167 s** | **0.0189 s** |

The last row includes the complete 197,281 four-ply legal continuations. Numbers above are
recorded experiment-specific measurements, **not claims of outperforming any other chess engine**.
Source artifacts (including exact entire formula text, feature-score input values and JSON
measurements) are stored under [`results/v5_long_graph/`](results/v5_long_graph/depth4_v4/run_evidence.json).
Text length is not an internal SDK node count.

**Graph regenerated before every move:** An additional, actually executed V4 self-play
regenerates the full depth-3 mathematical expression **eight times**, once for each halfmove.
This produced **1,571,370 total expression characters** across eight different graphs and
finished in 15.38 seconds on the available Linux runtime. Every move was verified by
replaying legal chess state transitions, and every mathematical result and reuse experiment
matched independent C++ minimax. The full trace and all eight expressions are preserved in
[`results/v5_graph_rebuilt_selfplay_8ply/`](results/v5_graph_rebuilt_selfplay_8ply/summary.json).
This is a deliberately bounded eight-halfmove experiment, not a whole finished chess game.

**Observed tactical mistake regression:** The original 94-halfmove ChatGPT/JOSHUA game
contains a black knight loss after `15...Nxe5 16.dxe5`. Reusing the recorded FEN,
a V4 depth-2 search without tactical extension again selected `15...Nxe5`, while
adding two quiescence plies selected `15...Nb6`. A deeper alternative selected another move.
This is a measured change in decision, not proof of universally superior chess play.
See [`results/game_analysis/`](results/game_analysis/historical_audit.json) and the legal board figures.

For the new mathematical construction and exact tree-to-formula mapping, see
[`docs/V5_LONG_GRAPH_MATHEMATICS.md`](docs/V5_LONG_GRAPH_MATHEMATICS.md).
The package contains **one consolidated English scientific whitepaper**:
[`JOSHUA_Chess_Research_Whitepaper_EN.pdf`](JOSHUA_Chess_Research_Whitepaper_EN.pdf).
No MCP server or external competitive chess engine is used in the execution.

### Build and run the long-graph mode

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build --target joshua_long_graph joshua_v5_selfplay_audit joshua -j

# A complete depth-three decision graph from the initial position:
./build/joshua_long_graph --model 4 --depth 3 --max-nodes 40000 \
  --max-chars 500000 --output results/my_graph

# Recompile a fresh graph before each move, for eight halfmoves:
python3 scripts/run_long_graph_selfplay.py --binary ./build/joshua_long_graph \
  --depth 3 --model 4 --plies 8 --max-nodes 150000 --max-chars 5000000 \
  --output results/my_eight_ply_experiment

# Verify the recorded game, the formulas and all source checks:
ctest --test-dir build --output-on-failure -j 1 \
  -E 'joshua_v5_huge_v4_neural_graph|joshua_v5_huge_v4_graph_independent_evidence'
```

The depth-4 graph compilation requires substantially more memory; use the documented
[`scripts/run_graph_with_memory_limit.sh`](scripts/run_graph_with_memory_limit.sh)
on memory-constrained Linux hosts. Chess rules and board transitions are handled by C++;
long expressions do not allow unlimited legal topologies, undo moves, detect all historical
repetitions or replace a complete chess search engine. The feature-vector deduplication is
only valid for the particular mathematical evaluator and does not assert identical tactics.

## What is actually implemented

The original move generator implements legal chess moves, check detection, castling, en passant, promotion, and make/unmake. It passes established perft tests. In `--mode research`, all legal continuations to a fixed search depth are built, feature vectors are evaluated through the original paceval **multi-graph batch API**, and internal min/max functions are evaluated through persistent paceval graphs. In `--mode alphabeta`, the search uses iterative deepening, exact-width alpha-beta at the chosen depth, and a transposition table; the position evaluator (including the optional neural network) is executed through the local paceval SDK, while alpha-beta control flow stays in C++. Quiescence search is optional and can change fixed-horizon equivalence.

Model 4 uses **48 scalar inputs**. The first 32 are unchanged V3 features. The additional 16 are pseudo-legal mobility, pseudo-legal captures, check status, hanging/attacked pieces, queen/rook threats, and local king-square attack pressure. The learned network is **48 → 12 sigmoid neurons → 1 capped residual**. The V3 base evaluation and the 13 neural graphs are all compiled by paceval. **All 13 formula strings**, including exact coefficients, are in [`formulas/v4_graph_expressions.tsv`](formulas/v4_graph_expressions.tsv). Exact lengths and variable counts are in [`formulas/v4_graph_manifest.csv`](formulas/v4_graph_manifest.csv).

A source-level mathematical catalog is also available in [`docs/MATHEMATICAL_PACEVAL_GRAPH_CATALOG.md`](docs/MATHEMATICAL_PACEVAL_GRAPH_CATALOG.md). A single research report, [`JOSHUA_Chess_Research_Whitepaper_EN.pdf`](JOSHUA_Chess_Research_Whitepaper_EN.pdf), contains the complete mathematical model, use cases, FEN-consistent board drawings, validation, and limitations. No second whitepaper is distributed.

## Reproducible Linux build

The original `paceval_main.h` and `paceval_main.cpp` are in `src/`. Obtain the original compatible Linux paceval runtime separately according to its licensing terms. The shared library is intentionally not included here.

```bash
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release \
  -DPACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so
cmake --build build --target joshua joshua_v4_audit -j
ctest --test-dir build --output-on-failure
```

Try the **trained neural support**, with an English console trace and elapsed seconds since launch:

```bash
./build/joshua --mode alphabeta --model 4 --depth 2 --plies 10 --no-board --output results/my_v4_game
```

For a mathematically full-width comparison, use a moderate depth and larger batches:

```bash
./build/joshua --mode research --model 4 --depth 2 --plies 3 --batch-rows 8192 --no-board --output results/my_v4_research
```

To retain the original manual evaluation, change `--model 4` to `--model 3`. For detailed usage, run `./build/joshua --help`. A configured maximum of 65,536 batch rows is an upper software setting, not an experimentally established optimal row count.

## Mathematics: what and why

The V3 score is a weighted, **explainable hand-designed** position evaluation. In mathematical notation, where `w` and `b` denote White and Black feature counts, its first terms are

```math
E_3(s) = 100(w_p-b_p) + 320(w_n-b_n) + 330(w_b-b_b) + 500(w_r-b_r) + 900(w_q-b_q) + E_{\mathrm{position}}(s).
```

The neural network learns a **bounded residual** relative to a two-ply V3 search target. Features are standardized using the means and scales computed *only from training games*:

```math
z_i=(x_i-\mu_i)/\sigma_i,\qquad
h_j=\frac{1}{1+\exp[-(b_j+\sum_{i=1}^{48}W_{ji}z_i)]}.
```

The final graph combines the manually interpretable V3 score with the trained support:

```math
E_4(s)=E_3(s)+\max\left(-150,\min\left(150,100\left[c+\sum_{j=1}^{12}v_j h_j(s)\right]\right)\right).
```

The cap is an explicit safety-of-integration **heuristic**, not a proof of chess reliability. The actual fused paceval graph uses an equivalent absolute-value expression for clipping. C++ produces legal positions and feature vectors; paceval executes the mathematical expressions and reused reduction graphs. The full account of each formula and its reason for existence is in the sole PDF report.

## Training, independent validation and measured evidence

The model was fitted using a fixed maximum of 280 L-BFGS iterations; the candidate fits reached that iteration limit, so optimizer convergence is not claimed. The legacy constant `bias` input normalizes to zero and provides no extra information. The model was fitted on **1,788 deterministic chess positions from 150 generated games**, split by complete game identity into 1,289 training, 252 validation, and 247 untouched test rows. No test position was used to select the neural architecture. The target is a clipped two-ply V3 minimax score residual, **not** an independent measure of true chess strength.

The held-out **test MAE** against this synthetic teacher decreased from **123.04 centipawns** for the uncorrected V3 residual to **105.06 centipawns** for V4. The training MAE was lower, which signals a generalization gap. The example is deliberately an early technical prototype, not a competitive neural chess evaluator.

In an independent local SDK audit, **110 held-out positions** were evaluated with all 12 neural hidden paceval graphs and the final fused paceval graph. The same positions were checked with 85-digit `mpmath` arithmetic; the recorded maximum absolute error was below `5e-7` centipawns. Full-width V4 search and Alpha-Beta V4 search selected the same moves and returned identical root move scores at an exact shared horizon in the tested three-halfmove trial. Ten halfmoves of model-4 self-play are included in `results/v4_alphabeta_10ply/` and `docs/v4_alphabeta_10ply_console.txt`.

Verification programs:

- [`scripts/train_v4.py`](scripts/train_v4.py) - deterministic grouped training and exact text-formula exporter (Python / NumPy / scikit-learn)
- [`src/joshua_v4_teacher.cpp`](src/joshua_v4_teacher.cpp) - reproducible legal positions and native V3 two-ply labels
- [`src/joshua_v4_audit.cpp`](src/joshua_v4_audit.cpp) - real paceval batch audit of held-out positions
- [`scripts/check_v4_high_precision.py`](scripts/check_v4_high_precision.py) - 85-digit independent neural mathematics
- [`scripts/check_mode_equivalence.py`](scripts/check_mode_equivalence.py) - fixed-horizon root scores and moves
- [`scripts/check_autoplay.py`](scripts/check_autoplay.py) - independent FEN and move coherence

## How to retrain

The published model artifacts are committed; retraining is **optional**. With a Python environment providing NumPy, scikit-learn and mpmath:

```bash
./build/joshua_v4_teacher training/teacher_positions.csv 150
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/train_v4.py
cmake --build build --target joshua joshua_v4_audit -j
ctest --test-dir build --output-on-failure
```

Retraining changes the generated C++ weight header, expression header and model files, so recompilation is required. A production quality chess model would need substantially broader datasets, policy/value supervision, independent Elo testing, robust tactical search, quantization studies, and benchmarking against NNUE inference. None of these are claimed here.

## Architecture, scope, and licensing

Current release: **JOSHUA vs JOSHUA self-play only**. Stockfish and Leela are referenced for architecture context, not bundled or connected. Remote MCP is not used. The Linux paceval shared library is excluded; see [`LICENSE_NOTICES.md`](LICENSE_NOTICES.md). Prior V3 experiments remain in their historical `results/v3_...` folders and form a reproducible baseline, but there is exactly **one whitepaper**.

Research context: [Stockfish NNUE architecture](https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html), [Lichess CC0 computer evaluations](https://database.lichess.org/), [paceval developers](https://paceval.com/developers/). Lichess external evaluation data has **not** been used for V4 training.
