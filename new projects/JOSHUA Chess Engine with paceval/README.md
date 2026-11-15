# JOSHUA V4: A Chess Research Engine with Trained Neural Support in paceval

![JOSHUA cover](figures/JOSHUA_Chess_Research_Cover_2400x1200.png)

**JOSHUA** is an English-language, Linux/C++ chess research program that plays both sides automatically. It uses the **original local paceval SDK** to evaluate reusable mathematical expressions. The MCP server, Stockfish, and Leela Chess Zero are not needed and are not invoked during a JOSHUA self-play game. JOSHUA's name is a tribute to the computer in *WarGames*, not a claim of association with the film.

The new optional **model 4** combines the transparent classical JOSHUA V3 score with a **genuinely trained** shallow neural network. The neural weights were learned from reproducibly generated legal chess positions labelled by JOSHUA's own **two-ply V3 minimax teacher**. They are not weights from Stockfish, Leela, or human grandmaster games. **Training-fit improvement is not proof of stronger chess play.** Models 1, 2, and 3 remain supported and unchanged.

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
E_4(s)=E_3(s)+\operatorname{clip}_{[-150,150]}\left(100\left[c+\sum_{j=1}^{12}v_j h_j(s)\right]\right).
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
