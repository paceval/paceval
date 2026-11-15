#!/usr/bin/env bash
# Process-local safety ceiling for very large formula creation on Linux CI.
# Prevents the host from exhausting physical RAM when compiling long graphs.
set -euo pipefail
ulimit -v 2450000
exec "$@"
