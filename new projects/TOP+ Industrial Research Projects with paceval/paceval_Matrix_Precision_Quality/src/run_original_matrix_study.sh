#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIB="${1:?Usage: bash scripts/run_generic_spd.sh /absolute/path/libpaceval.so [size=512] [batch=4096]}"
N="${2:-512}"
BATCH="${3:-4096}"
RUN_OUT="$ROOT/results/reproduced"
mkdir -p "$RUN_OUT"
g++ -O3 -std=c++17 -Wall -Wextra -pedantic "$ROOT/src/dense_spd_paceval.cpp" -o "$ROOT/dense_spd_paceval" -ldl
"$ROOT/dense_spd_paceval" "$LIB" "$RUN_OUT" "$N" "$BATCH" 1
OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-2}" python3 "$ROOT/validation/verify_dense_numpy.py" "$RUN_OUT" "$N"
