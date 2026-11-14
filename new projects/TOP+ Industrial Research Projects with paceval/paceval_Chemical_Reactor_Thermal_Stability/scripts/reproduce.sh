#!/usr/bin/env bash
# The proprietary/external compatible runtime must be supplied separately.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${PACEVAL_RUNTIME:?Set PACEVAL_RUNTIME to a licensed compatible Linux .so file}"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_RUNTIME"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure | tee "$ROOT/results/ctest_report.txt"
"$ROOT/build/reactor_screening" --run "$ROOT/input/scenarios.csv" "$ROOT/results"
python3 "$ROOT/scripts/verify_high_precision.py"
python3 "$ROOT/scripts/make_figures.py"
python3 "$ROOT/scripts/make_whitepaper.py"
python3 "$ROOT/src/check_readme_math.py" "$ROOT/README.md"
python3 "$ROOT/src/check_readme_math.py" --selftest
python3 "$ROOT/scripts/finalize_evidence.py"
python3 "$ROOT/scripts/verify_release.py"
