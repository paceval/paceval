#!/usr/bin/env python3
"""Reconcile released paceval CSV rows with execution summary and routing totals."""
from pathlib import Path
import csv,sys
R=Path(__file__).resolve().parents[1]
s=dict(line.strip().split('=',1) for line in (R/'examples/execution_summary.txt').read_text().splitlines() if '=' in line)
with (R/'examples/constraint_evaluations.csv').open() as f:
 rows=list(csv.DictReader(f))
with (R/'examples/ellipse_surface.csv').open() as f:
 surface=list(csv.DictReader(f))
with (R/'examples/guard_registry.csv').open() as f:
 guards=list(csv.DictReader(f))
assert len(rows)==100000 and len(surface)==3721 and len(guards)==1001
for key,label in [('accept','ACCEPT'),('reject','REJECT'),('review_boundary','REVIEW_BOUNDARY')]:
 assert int(s[key])==sum(r['decision']==label for r in rows)
assert all(r['decision']==r['reference_decision'] for r in rows)
assert s['sdk_status']=='PASS'
print('PASS: 100000 decisions, 3721 surface values, 1001 guard registry rows; released decision totals verified')
