#!/usr/bin/env bash
# Safely update an existing flat JOSHUA install, preserving all historical ZIP logs.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:?Usage: ./scripts/install_flat_linux.sh /path/to/joshua_autoplay}"
[[ -d "$TARGET" ]] || { echo "Target directory does not exist: $TARGET" >&2; exit 2; }
if command -v pgrep >/dev/null 2>&1 && pgrep -u "$(id -u)" -x joshua_selfplay >/dev/null; then
  echo 'A joshua_selfplay process is running. Stop it with Ctrl+C before updating.' >&2
  exit 2
fi
for name in joshua joshua_selfplay joshua_long_graph; do
  [[ -x "$ROOT/bin/$name" ]] || { echo "Missing compiled binary: $ROOT/bin/$name" >&2; exit 2; }
done
for name in joshua joshua_selfplay joshua_long_graph; do
  install -m 755 "$ROOT/bin/$name" "$TARGET/$name"
done
if [[ ! -f "$TARGET/libpaceval_linux_sharedLIB.so" && ! -f "$TARGET/runtime/libpaceval_linux_sharedLIB.so" ]]; then
  echo 'Note: no original paceval runtime found in target. Set PACEVAL_RUNTIME when starting.' >&2
fi
printf 'Updated JOSHUA binaries in %s. Existing sessions/logs were not modified.\n' "$TARGET"
