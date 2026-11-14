#!/usr/bin/env bash
# Full independent reproduction with supplied ORIGINAL paceval Linux runtime.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -ne 1 || ! -f "$1" ]]; then
 echo 'Usage: scripts/reproduce.sh /absolute/path/to/original/libpaceval_linux_sharedLIB.so' >&2; exit 2
fi
RUNTIME="$(realpath "$1")"
python3 "$ROOT/scripts/create_scenarios.py"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$RUNTIME"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure | tee "$ROOT/results/ctest_report.txt"
"$ROOT/build/chip_warpage" --run "$ROOT/input/scenarios.csv" "$ROOT/results"
python3 "$ROOT/scripts/verify_high_precision.py" "$ROOT/results"
python3 "$ROOT/scripts/finalize_evidence.py"
python3 "$ROOT/scripts/make_figures.py"
python3 "$ROOT/scripts/make_whitepaper.py"
python3 "$ROOT/scripts/verify_release.py"
