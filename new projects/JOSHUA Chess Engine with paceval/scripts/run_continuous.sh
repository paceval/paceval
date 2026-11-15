#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${PACEVAL_RUNTIME:-}" ]]; then
  export PACEVAL_RUNTIME="$ROOT/runtime/libpaceval_linux_sharedLIB.so"
fi
if [[ ! -f "$PACEVAL_RUNTIME" ]]; then
  printf 'Cannot start JOSHUA: original paceval runtime missing at %s\n' "$PACEVAL_RUNTIME" >&2
  printf 'Copy the authorized SDK Linux x64 .so to runtime/ or set PACEVAL_RUNTIME.\n' >&2
  exit 2
fi
if [[ ! -x "$ROOT/bin/joshua_selfplay" ]]; then
  printf 'Compiled supervisor missing. Run ./scripts/build_linux.sh\n' >&2
  exit 2
fi
exec "$ROOT/bin/joshua_selfplay" --output "$ROOT/sessions" "$@"
