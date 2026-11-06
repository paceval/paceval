#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 2
python reference_python/test_refine.py
python validation/high_precision_check.py
./build/braneworld_v13 --backend both --paceval sdk/libpaceval.so --steps 2000 --output results/scan_v13
# The executable writes results/scan_v13.native.csv and .paceval.csv.
cp results/scan_v13.native.csv results/native_scan_v13.csv
cp results/scan_v13.paceval.csv results/paceval_scan_v13.csv
python validation/validate_results.py
python validation/convergence_run.py "$(pwd)/build/braneworld_v13"
python validation/plot_v13.py
printf '\nPASS all core Linux regressions (TINC intentionally disabled)\n'
