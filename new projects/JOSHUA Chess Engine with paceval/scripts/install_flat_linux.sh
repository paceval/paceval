#!/usr/bin/env bash
# Update a previous flat joshua_autoplay installation without deleting old ZIP sessions.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:?Usage: ./scripts/install_flat_linux.sh /path/to/joshua_autoplay}"
[[ -d "$TARGET" ]] || { echo "Target directory does not exist: $TARGET" >&2; exit 2; }
if command -v pgrep >/dev/null 2>&1 && pgrep -u "$(id -u)" -x joshua_selfplay >/dev/null; then
 echo 'Stop the running selfplay process with Ctrl+C before updating.' >&2; exit 2
fi
for name in joshua joshua_selfplay joshua_long_graph joshua_referee; do
 [[ -x "$ROOT/bin/$name" ]] || { echo "Missing compiled binary: $ROOT/bin/$name" >&2; exit 2; }
 install -m 755 "$ROOT/bin/$name" "$TARGET/$name"
done
install -m 644 "$ROOT/scripts/stockfish_match.py" "$TARGET/stockfish_match.py"
install -m 644 "$ROOT/scripts/export_stockfish_logs.py" "$TARGET/export_stockfish_logs.py"
mkdir -p "$TARGET/config"
if [[ ! -f "$TARGET/config/active_graph.tsv" ]]; then
 install -m 644 "$ROOT/config/active_graph.tsv" "$TARGET/config/active_graph.tsv"
fi
cat > "$TARGET/run_stockfish_matches.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${PACEVAL_RUNTIME:-}" ]]; then
 export PACEVAL_RUNTIME="$ROOT/libpaceval_linux_sharedLIB.so"
fi
exec python3 "$ROOT/stockfish_match.py" --joshua "$ROOT/joshua" \
 --referee "$ROOT/joshua_referee" --output "$ROOT/stockfish_sessions" "$@"
EOF
chmod 755 "$TARGET/run_stockfish_matches.sh"
if [[ ! -f "$TARGET/libpaceval_linux_sharedLIB.so" && ! -f "$TARGET/runtime/libpaceval_linux_sharedLIB.so" ]]; then
 echo 'Original paceval runtime is missing. Set PACEVAL_RUNTIME or copy your authorized library.' >&2
fi
printf 'Installed V9 matches and four ELF programs in %s. Old logs and paceval runtime preserved.\n' "$TARGET"
