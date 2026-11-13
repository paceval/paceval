#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${PACEVAL_RUNTIME:?Set PACEVAL_RUNTIME=/absolute/path/to/original.so}"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_RUNTIME"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
"$ROOT/build/battery_twin" --out "$ROOT" --steps 720
python3 "$ROOT/src/verify_results.py" --root "$ROOT"
python3 "$ROOT/src/high_precision_reference.py" --root "$ROOT"
python3 "$ROOT/src/make_figures.py" --root "$ROOT"
python3 "$ROOT/src/check_readme_math.py"
