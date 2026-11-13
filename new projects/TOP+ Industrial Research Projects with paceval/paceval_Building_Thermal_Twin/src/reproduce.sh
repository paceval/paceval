#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: bash src/reproduce.sh /absolute/path/to/libpaceval_linux_sharedLIB.so" >&2
  exit 2
fi
RUNTIME="$(realpath "$1")"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$RUNTIME"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
"$ROOT/build/building_thermal_twin" --out "$ROOT" --steps 384 --grid 7
python3 "$ROOT/src/verify_results.py" --root "$ROOT"
python3 "$ROOT/src/make_figures.py" --root "$ROOT" --figures "$ROOT/figures"
python3 "$ROOT/src/make_whitepaper.py" --root "$ROOT"
python3 "$ROOT/src/check_readme_math.py"
