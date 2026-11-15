#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DJOSHUA_RUNTIME_DELAY_LOAD=ON
cmake --build "$ROOT/build" --target joshua joshua_long_graph joshua_selfplay -j "${JOBS:-2}"
mkdir -p "$ROOT/bin"
cp "$ROOT/build/joshua" "$ROOT/build/joshua_long_graph" "$ROOT/build/joshua_selfplay" "$ROOT/bin/"
"$ROOT/bin/joshua_selfplay" --selftest
python3 "$ROOT/scripts/test_v6_supervisor.py" "$ROOT/bin/joshua_selfplay" "$ROOT/results/v3_ab_depth4_q1_10ply"
python3 "$ROOT/scripts/test_v7_zip_retention.py" "$ROOT/bin/joshua_selfplay" "$ROOT/results/v3_ab_depth4_q1_10ply"
python3 "$ROOT/scripts/test_v6_longgraph_supervisor.py" "$ROOT/bin/joshua_selfplay" "$ROOT/results/v5_graph_rebuilt_selfplay_8ply"
python3 "$ROOT/scripts/check_markdown.py" "$ROOT"
python3 "$ROOT/scripts/check_markdown.py" --selftest
printf '\nBinaries are in %s/bin. Full chess execution requires the original paceval shared library.\n' "$ROOT"
