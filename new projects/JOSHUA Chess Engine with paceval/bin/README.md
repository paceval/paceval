# Compiled Linux x86-64 programs

- `joshua`: paceval mathematical chess evaluation, including the V9 reloadable adaptive graph via `--graph-file`.
- `joshua_referee`: validates legal moves and returns FEN, SAN, checkmate/stalemate or automatic draw candidates; no paceval runtime required for rules.
- `joshua_selfplay`: V8/V7 historical autonomous JOSHUA-vs-JOSHUA executable with ZIP log rotation.
- `joshua_long_graph`: V5 full finite-horizon mathematical decision-graph experiment.

The original authorized `libpaceval_linux_sharedLIB.so` is needed separately to execute the math in `joshua` and `joshua_long_graph`. V9 Stockfish match orchestration is in `scripts/stockfish_match.py` (Python standard library only); Stockfish itself must be installed separately.

The four binaries are actual compiled ELF x86-64 programs. The GNU C++ runtime is linked statically, but compatible Linux glibc remains required. No proprietary paceval runtime or Stockfish implementation is distributed.
