#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
LIB="${1:-${PACEVAL_LIBRARY:-}}"
if [[ -z "$LIB" && -f sdk/libpaceval.so ]]; then LIB="$(pwd)/sdk/libpaceval.so"; fi
if [[ -z "$LIB" || ! -f "$LIB" ]]; then
  echo 'Usage: bash scripts/run_smoke.sh /absolute/path/to/libpaceval.so' >&2
  exit 2
fi
LIB="$(realpath "$LIB")"
mkdir -p build results
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
python3 reference_python/test_refine.py
./build/braneworld_v13 --backend both --paceval "$LIB" --steps 2000 --output results/smoke_geometry
./build/braneworld_v14 --lib "$LIB" --mode static --k 3 --ny 81 --dt 0.003 --tmax 1 --out results/smoke_static.csv
./build/braneworld_v14_planar --lib "$LIB" --mode constant --nx 31 --ny 31 --dt 0.004 --tmax 0.08 --out results/smoke_planar.csv
./build/braneworld_v15 --lib "$LIB" --n 100 --ellmin 0.1 --ellmax 0.535 --count 2 --out results/smoke_cosmology.csv
python3 validation/validate_results.py
python3 scripts/check_generated.py
python3 scripts/check_links.py
printf '
PASS: smoke tests completed (scientific scope remains limited).
'
