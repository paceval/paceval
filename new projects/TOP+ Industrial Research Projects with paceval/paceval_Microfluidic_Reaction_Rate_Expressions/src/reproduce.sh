#!/usr/bin/env bash
set -euo pipefail
: "${PACEVAL_RUNTIME:?export PACEVAL_RUNTIME=/absolute/path/to/the_original_libpaceval_linux_sharedLIB.so}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_RUNTIME"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
"$ROOT/build/microfluidic_reactor" --out "$ROOT" --cells 64 --steps 1440
python3 "$ROOT/src/verify_results.py" --root "$ROOT"
python3 "$ROOT/src/mesh_refinement.py" --root "$ROOT" --executable "$ROOT/build/microfluidic_reactor"
python3 "$ROOT/src/make_figures.py" --root "$ROOT"
python3 "$ROOT/src/make_whitepaper.py" --root "$ROOT"
python3 "$ROOT/src/check_readme_math.py"
