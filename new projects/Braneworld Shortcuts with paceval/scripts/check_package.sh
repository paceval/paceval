#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/check_links.py
python3 - <<'PYTEST'
from pathlib import Path
from collections import Counter
import csv
p=Path('results/paceval_scan_v13.csv')
rows=list(csv.DictReader(p.open()))
assert len(rows)==50
assert sum(float(r['w'])==-1 for r in rows)==7
assert sum(float(r['w'])>-1 and float(r['advance'])>0 for r in rows)==43
print('PASS: archived model scan counts')
PYTEST
