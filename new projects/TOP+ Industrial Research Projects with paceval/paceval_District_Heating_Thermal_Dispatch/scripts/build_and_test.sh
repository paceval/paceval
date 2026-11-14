#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# -ne 1 ]] || [[ ! -f "$1" ]];then echo 'Usage: scripts/build_and_test.sh /absolute/path/to/original_libpaceval_linux_sharedLIB.so' >&2;exit 2;fi
cmake -S "$ROOT/src" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DPACEVAL_RUNTIME="$1"
cmake --build "$ROOT/build" -j
ctest --test-dir "$ROOT/build" --output-on-failure
