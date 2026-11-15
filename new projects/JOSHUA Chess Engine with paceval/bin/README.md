# Linux x86-64 binaries

The four executables `joshua`, `joshua_referee`, `joshua_selfplay`, and `joshua_long_graph` are precompiled ELF programs. V10 modifies the main `joshua` engine; other executables retain their documented V9 behavior. `joshua` uses dynamically loaded **original** paceval at runtime. Stockfish is an external UCI process, and no Stockfish executable is distributed. See the root README for installation and verified tests.
