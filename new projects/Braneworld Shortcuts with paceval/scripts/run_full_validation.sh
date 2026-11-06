#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
LIB="${1:-${PACEVAL_LIBRARY:-}}"
if [[ -z "$LIB" && -f sdk/libpaceval.so ]]; then LIB="$(pwd)/sdk/libpaceval.so"; fi
if [[ -z "$LIB" || ! -f "$LIB" ]]; then
  echo 'Usage: bash scripts/run_full_validation.sh /absolute/path/to/libpaceval.so' >&2
  exit 2
fi
LIB="$(realpath "$LIB")"
mkdir -p sdk
if [[ "$LIB" != "$(pwd)/sdk/libpaceval.so" ]]; then
  ln -sfn "$LIB" sdk/libpaceval.so
fi
# The existing research iteration scripts assume sdk/libpaceval.so.
bash validation/run_geometric_regression.sh
bash validation/run_iteration_suite.sh
python3 figures/generate_figures.py
python3 scripts/check_links.py
printf '
PASS full research iteration suite (not physical peer review).
'
