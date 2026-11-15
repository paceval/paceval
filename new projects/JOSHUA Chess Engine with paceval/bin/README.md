# Compiled Linux Intel/AMD x86-64 programs

- `joshua`: original chess engine with model 1-4, optional Alpha-Beta or paceval research search, SAN PGN and unambiguous termination results.
- `joshua_long_graph`: V5 complete legal finite-horizon mathematical decision-graph compiler, using genuine original paceval and independent C++ minimax checks.
- `joshua_selfplay`: continuous games and rigorous game-by-game review queue in a separate process for each game, including the V5 longgraph mode. Each game is compressed into an individual ZIP archive, with oldest-first deletion under a default 25 MB retained-log budget. The archive writer uses statically linked zlib.

All three are actual compiled x86-64 ELF programs. The authentic paceval runtime remains necessary to execute chess math. Place it in `../runtime/libpaceval_linux_sharedLIB.so` or set `PACEVAL_RUNTIME`. The optional `src/paceval_runtime_loader.cpp` is a transparent forwarding adapter that contains no paceval computation implementation.

The GNU C++ runtime was linked statically. System libraries `libc` and `libm` are supplied by the target Linux distribution. Native executables require a compatible Linux glibc ABI. Rebuild with `../scripts/build_linux.sh` if the target system is older.
