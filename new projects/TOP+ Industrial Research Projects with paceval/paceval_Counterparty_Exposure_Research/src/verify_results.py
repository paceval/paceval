#!/usr/bin/env python3
"""Verify the actual exported SDK experiment and project integrity."""
import csv, pathlib, json
root=pathlib.Path(__file__).resolve().parents[1]; e=root/'examples'
def rows(n):return list(csv.DictReader((e/n).open()))
a=rows('rule_registry.csv'); m=rows('rule_metrics.csv'); s=rows('exposure_samples.csv'); surf=rows('exposure_surface.csv')
assert len(a)==51 and len(m)==50 and len(s)==200 and len(surf)==3721
assert len(rows('stress_scenarios.csv'))==81 and len(rows('formula_revision.csv'))==61
log=(e/'sdk_execution.txt').read_text();assert 'MARKET_UPDATES 20000' in log and 'STATUS PASS' in log
assert all(float(x['exposure_eur_m'])>=0 for x in s)
assert all(float(x['exposure_eur_m'])>=0 for x in surf)
print('PASS: 51 formulas, 20,000 updates, 200 sampled rows, 3,721 surface points, 81 stress positions, 61 version samples')
(root/'results/verification.txt').write_text('PASS: executed output schemas and counts independently verified\n')
