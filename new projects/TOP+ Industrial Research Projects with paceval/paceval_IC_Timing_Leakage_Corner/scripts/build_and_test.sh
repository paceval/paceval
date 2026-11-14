#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then echo 'Usage: bash scripts/build_and_test.sh /absolute/path/libpaceval_linux_sharedLIB.so' >&2; exit 2; fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$1"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
