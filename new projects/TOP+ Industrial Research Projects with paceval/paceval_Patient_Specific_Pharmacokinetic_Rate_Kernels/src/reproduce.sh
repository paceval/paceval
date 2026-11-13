#!/usr/bin/env bash
# End-to-end reproducible Linux x86-64 build and verification. Original external library required.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${PACEVAL_RUNTIME:?Set PACEVAL_RUNTIME=/absolute/path/to/original/libpaceval_linux_sharedLIB.so}"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_RUNTIME"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
"$ROOT/build/pharmacokinetic_kernels" --out "$ROOT" --steps 384 --patients 42
python3 "$ROOT/src/verify_results.py" --root "$ROOT"
python3 "$ROOT/src/make_figures.py" --root "$ROOT"
python3 "$ROOT/src/make_whitepaper.py" --root "$ROOT"
python3 "$ROOT/src/check_readme_math.py"
