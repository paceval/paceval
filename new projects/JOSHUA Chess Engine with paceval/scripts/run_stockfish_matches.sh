#!/usr/bin/env bash
# Start a real UCI Stockfish vs local genuine paceval Joshua match series.
# Can run from a full GitHub checkout or from the flat Linux installation.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -x "$ROOT/bin/joshua" || ! -x "$ROOT/bin/joshua_referee" ]]; then
  echo 'Expected compiled Joshua and referee in bin/. Build or install the package.' >&2
  exit 2
fi
if [[ -z "${PACEVAL_RUNTIME:-}" ]]; then
  export PACEVAL_RUNTIME="$ROOT/runtime/libpaceval_linux_sharedLIB.so"
fi
if [[ ! -f "$PACEVAL_RUNTIME" ]]; then
  echo "Original paceval shared library missing: $PACEVAL_RUNTIME" >&2
  exit 2
fi
exec python3 "$ROOT/scripts/stockfish_match.py" --joshua "$ROOT/bin/joshua" \
  --referee "$ROOT/bin/joshua_referee" --output "$ROOT/stockfish_sessions" "$@"
