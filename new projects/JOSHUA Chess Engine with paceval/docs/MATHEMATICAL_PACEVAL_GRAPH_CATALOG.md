# JOSHUA mathematical paceval graph catalog

This is an English-language mathematical guide to the **exact kinds of paceval formulas actually executed** by JOSHUA. The full decimal-constant neural expressions are in [`../formulas/v4_graph_expressions.tsv`](../formulas/v4_graph_expressions.tsv); this document gives their unambiguous symbolic equivalents, provenance, and purpose. Formula text lengths are counted in [`../formulas/v4_graph_manifest.csv`](../formulas/v4_graph_manifest.csv). `paceval_main.h` and `paceval_main.cpp` provide the real SDK interface. The compiled engine uses the local paceval library only.

## Input extraction and units

C++ is responsible for implementing chess rules, generating legal candidate moves and extracting deterministic numerical inputs. White and Black count features use prefixes `w` and `b`. Positive evaluation means an advantage for White. Unit is a **heuristic centipawn**, not a calibrated probability. `tempo = +1` when White moves, `-1` when Black moves. The V3 model has 32 variables; V4 adds 16 tactical proxy inputs, resulting in 48 variables.

## Classical material and positional models

Material:

```math
M = 100(wp-bp)+320(wn-bn)+330(wb-bb)+500(wr-br)+900(wq-bq).
```

Here `wp` counts White pawns, `wn` White knights, `wb` White bishops, `wr` White rooks, `wq` White queens, and similarly for Black. This graph provides a transparent material baseline. Its stored paceval expression length is 61 characters.

Core positional differences:

```math
C=wc-bc,\quad D=wd-bd,\quad A=wa-ba,\quad K=wk-bk.
```

Why: center squares, developed minor pieces, pawn advancement and a rough king-zone proxy allow the engine to distinguish positions with the same material balance.

Versions:

```math
E_1=M,\qquad E_2=M+13C+17D+3A+18K.
```

V3 expands the handcrafted positional model:

```math
P=wpsq-bpsq,
```

```math
S=-16(wdoub-bdoub)-12(wisolated-bisolated)+22(wpassed-bpassed)+28(wbpair-bbpair),
```

```math
H=9(wshield-bshield),\qquad T=7\,tempo,
```

```math
E_3=M+13C+17D+3A+18K+P+S+H+T.
```

Purpose of each V3 graph: `MATERIAL` preserves interpretable piece values; `POSITIONAL_ACTIVITY` rewards relative piece-square placement; `PAWN_STRUCTURE` penalizes doubled and isolated pawns and rewards passed pawns and bishop pairs; `KING_SHELTER` measures friendly pawn presence around each king; `TEMPO` distinguishes the side to move. The separate `SENSITIVITY_ACTIVITY_WEIGHT` is the mathematical factor `P`, which is the derivative of a linear score with respect to its own activity coefficient when that coefficient is treated as a free model parameter. `POSITIONAL_COMPOSITE` is the sum `13C+17D+P`.

All baseline models also supply diagnostics:

```math
\operatorname{SCORE\_MARGIN}=2000-|E_i|,
```

```math
\operatorname{SCORE\_GUARD}=\mathbf{1}\{ |E_i|\leq2000\}\cdot\mathbf{1}\{wp\geq0\}\cdot\mathbf{1}\{bp\geq0\}.
```

The margin/guard detect modeled score-envelope conditions; they are **not** a formal proof that a position is balanced or safe. The available V1/V2 `COMPOSITE_PIECE_ACTIVITY` is `13C+17D`. All V1/V2/V3 persisted C++ formula strings are stored in [`../src/paceval_math.h`](../src/paceval_math.h).

## Neural support: trained V4

The training pipeline generates *legal chess positions* and target scores from a native depth-two V3 minimax search. It uses no Stockfish, Leela, real-world human master labels or an MCP server. The initial model has twelve sigmoid hidden neurons, one output neuron and a fixed cap on the correction. Training uses a deterministic grouped split by game identity.

Each board provides a 48-element feature vector `x`. Its first 32 components are the exact V3 features. The new 16 are pseudo-legal move counts and capture counts, check indicators, attacked or hanging pieces, threats to queens or rooks, and attacked adjacent king squares for both sides.

Normalization on training-only data:

```math
z_i=\frac{x_i-\mu_i}{\sigma_i},\quad i\in\{1,\ldots,48\}.
```

Each hidden neuron is one persistent paceval graph:

```math
h_j(x)=\frac{1}{1+\exp\left(-b_j-\sum_{i=1}^{48}W_{ji}z_i\right)},\quad j=1,\ldots,12.
```

The weights `W` and biases `b` are constants learned during training; `x` is the only changing input. This captures **nonlinear feature interactions** that cannot be represented by a fixed additive V3 score. It does *not* recover missing board information.

The separate fused paceval graph receives all twelve calculated hidden outputs and an input named `base`, the value of `E3` returned from the original paceval V3 SCORE graph:

```math
R(x)=100\left(c+\sum_{j=1}^{12}v_jh_j(x)\right),
```

```math
E_4(x)=E_3(x)+\operatorname{clip}_{[-150,150]}(R(x)).
```

The equivalent SDK expression for clipping, chosen to avoid a dependency on conditional parsing, is

```math
\operatorname{clip}_{[-150,150]}(R)=\frac{|R+150|-|R-150|}{2}.
```

The clipped residual limits the impact of a speculative model. It is an engineering integration choice, **not a guarantee of chess correctness**. The source code evaluates every neural graph and compares its output against an independently coded native feedforward model; a separate high-precision checker does not call paceval.

## Automatic minimax decision graphs

For a position with `m` completed child evaluations from White's perspective:

```math
V_{White}=\max\{E(s_1),\ldots,E(s_m)\},\qquad
V_{Black}=\min\{E(s_1),\ldots,E(s_m)\}.
```

JOSHUA synthesizes the actual text `(v0 max v1 max ... vm)` or `(v0 min v1 min ... vm)` as required and reuses the resulting paceval computation handles. In full-width mode, all internal reductions are passed to the batch API. In Alpha-Beta, the search bounds remain native C++ because they decide *which* child states must be visited; only the mathematical leaf evaluations and final root reduction are performed by paceval.

Neither the mathematical score nor the maximum search depth is a proof of forced win, draw or loss. For a proof, all relevant legal continuations must be exhaustively accounted for or bounded using sound search logic and exact terminal evaluation.

## Source files / independent validation

- Exported formulas: [`../formulas/v4_graph_expressions.tsv`](../formulas/v4_graph_expressions.tsv)
- Exact graph lengths: [`../formulas/v4_graph_manifest.csv`](../formulas/v4_graph_manifest.csv)
- Trained coefficients: [`../formulas/v4_trained_weights.json`](../formulas/v4_trained_weights.json)
- Neural execution: [`../src/v4_paceval.h`](../src/v4_paceval.h)
- Independent training: [`../scripts/train_v4.py`](../scripts/train_v4.py)
- Chess feature extraction: [`../src/joshua_v4_features.h`](../src/joshua_v4_features.h)
- High precision reference: [`../scripts/check_v4_high_precision.py`](../scripts/check_v4_high_precision.py)

The exported V4 graph set consists of **13 formulas totaling 43,311 characters**. Their text lengths describe the literal input expressions, not the number of optimized internal paceval operation nodes. The early trained model is only a demonstrator: its held-out improvement is for imitation of its **own weak classical teacher**, not evidence of competitive chess strength.
