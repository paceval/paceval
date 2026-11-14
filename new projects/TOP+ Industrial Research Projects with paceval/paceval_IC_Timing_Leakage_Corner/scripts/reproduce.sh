#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 validation/validate_records.py
python3 scripts/build_evidence.py
python3 scripts/make_figures.py
python3 scripts/make_equations.py
python3 scripts/make_whitepaper.py
python3 src/check_readme_math.py
python3 validation/check_project.py
printf '\nThe local paceval SDK test requires an external ABI-compatible .so:\n  bash scripts/build_and_test.sh /absolute/path/libpaceval_linux_sharedLIB.so\n'
