#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then echo 'usage: bash src/reproduce.sh /absolute/path/to/libpaceval_linux_sharedLIB.so'; exit 2; fi
lib=$(realpath "$1")
cd "$(dirname "$0")/.."
cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$lib"
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/electrolyser_twin --out . --steps 240
python3 src/verify_results.py --root .
python3 src/make_figures.py --root .
python3 src/check_readme_math.py
python3 src/make_whitepaper.py --root .
