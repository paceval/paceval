# V5 Mathematical Decision Graphs: Definition and Purpose

The C++ host generates legal chess moves and has no reliance on paceval to decide whether
castling, promotion, en passant or checks are legal. paceval executes the mathematical
functions after receiving numerical leaf scores.

## 1. Classical position evaluation (V3)

In the following GitHub-compatible math fence, `w` and `b` indicate the same numeric
feature family for White and Black. Values are heuristic centipawns:

```math
E_3(s)=100(w_p-b_p)+320(w_n-b_n)+330(w_b-b_b)+500(w_r-b_r)
+900(w_q-b_q)+E_{\mathrm{position}}(s).
```

The purpose of V3 is to provide a deterministic and interpretable baseline. Other
positional components are included in the exact formula source at
[`../src/paceval_math.h`](../src/paceval_math.h).

## 2. Trained neural residual (V4)

The 48 input scalars are standardized with constants learned exclusively on the
training split. Twelve sigmoid graphs represent the hidden units; a final graph
combines them with the V3 score:

```math
z_i=\frac{x_i-\mu_i}{\sigma_i},\qquad
h_j(s)=\frac{1}{1+\exp\left[-\left(b_j+\sum_{i=1}^{48}W_{ji}z_i\right)\right]}.
```

```math
R(s)=100\left(c+\sum_{j=1}^{12}v_j h_j(s)\right),\qquad
E_4(s)=E_3(s)+\max\left(-150,\min\left(150,R(s)\right)\right).
```

The bound is a heuristic integration constraint, not a mathematical guarantee of
chess reliability. The exact trained weights are fixed literals in
[`../formulas/v4_graph_expressions.tsv`](../formulas/v4_graph_expressions.tsv).

## 3. Full-width bounded minimax decision graph (V5)

For a state `s`, legal moves `L(s)` and transition function `T`, the C++ host
recursively enumerates legal continuations to a **fixed requested depth**. At a
nonterminal leaf the score is `E3` or `E4`; at checkmate/stalemate the terminal
value is applied first. The mathematical minimax recursion is:

```math
V_d(s)=\begin{cases}
E(s), & d=0\text{ and }s\text{ nonterminal},\\
\max\limits_{a\in L(s)} V_{d-1}(T(s,a)), & \text{White to move},\\
\min\limits_{a\in L(s)} V_{d-1}(T(s,a)), & \text{Black to move}.
\end{cases}
```

Terminal positions take precedence over this expression. This is a finite-horizon
search evaluation, not a proof of the game-theoretic value of chess.

The generated graph uses variables `v0`, `v1`, etc. Each represents the
precomputed score of a distinct feature vector under the selected model. An
illustrative, structurally accurate **two-ply** expression is:

```text
((v0 min v1 min v2) max (v3 min v4 min v5))
```

This example assumes White is choosing between two moves and Black has three
replies to each move. The real expressions contain every legal move in their
bounded search tree, and are saved verbatim as
`results/v5_long_graph/<run>/paceval_minimax_expression.txt`.

When terminal scores are negative, the generator explicitly encodes them as
`(0-29996)` instead of an ambiguous prefix minus after `min` or `max`.

**What is and is not reused:** Changing the `v_i` numerical inputs allows the
same compiled graph to recalculate another evaluation of the *same legal tree*.
If a new move changes the legal tree, the host regenerates a new graph.
Feature aliasing (the same 48 values for two different boards) is not a chess
transposition and may miss tactical information. The current experiment does
not carry complete repetition histories into graph nodes.

## 4. Why large batches matter

The 48-dimensional feature vectors of numerous leaf positions are assembled by
C++, deduplicated by their numeric input vector, and passed in chunks to the
original local paceval multi-graph batch API. The V4 hidden layers are computed
with persistent graphs; a fused graph then calculates the final scores. The
large V5 `min`/`max` graph receives these scores as numerical variables and
produces the root minimax result.

An implementation-specific batch upper limit of 65,536 rows is available.
It is **not** a performance optimum or a guarantee that arbitrarily large
calls succeed on every system. Graph creation and evaluation are reported
separately for the concrete Linux experiments.

## 5. Independent checks

An independently coded C++ minimax traversal calculates the same root value
without using the compiled V5 expression; the same graph is then re-evaluated
with a different numeric vector. In an eight-halfmove experiment, legal moves
and FEN transitions are replayed from the recorded trace, and each saved
expression is checked against its JSON run evidence.

These tests validate mathematical equivalence and documented moves. They do
not establish higher chess strength, general graph scalability or advantage
over existing leading chess engines.
