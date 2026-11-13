#!/usr/bin/env bash
# Rebuild an original-SDK synthetic WP050 research computation using external paceval .so.
set -euo pipefail
if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo 'Usage: bash src/reproduce.sh /absolute/path/to/libpaceval_linux_sharedLIB.so' >&2
  exit 2
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIB="$(realpath "$1")"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$LIB"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
"$ROOT/build/production_planning" --out "$ROOT"
python3 "$ROOT/src/verify_results.py" --root "$ROOT"
python3 "$ROOT/src/high_precision_reference.py" --root "$ROOT"
python3 "$ROOT/src/make_figures.py" --root "$ROOT"
python3 "$ROOT/src/make_whitepaper.py" --root "$ROOT"
python3 "$ROOT/src/check_readme_math.py"
echo 'PASS all documented reproduction steps'
