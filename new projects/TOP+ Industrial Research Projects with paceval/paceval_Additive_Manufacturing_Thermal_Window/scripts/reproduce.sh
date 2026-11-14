#!/usr/bin/env bash
# Reproduce validation/plots without pretending a missing SDK runtime can execute.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 src/generate_formulas.py .
python3 validation/high_precision_reference.py .
python3 validation/check_project.py .
python3 src/make_figures.py .
python3 src/make_whitepaper.py .
if [[ -n "${PACEVAL_RUNTIME:-}" ]] && [[ -f "${PACEVAL_RUNTIME}" ]]; then
  cmake -S src -B build -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$PACEVAL_RUNTIME"
  cmake --build build -j
  ctest --test-dir build --output-on-failure
else
  echo "Original local SDK runtime missing: no local C++ linking or CTest run claimed."
fi
