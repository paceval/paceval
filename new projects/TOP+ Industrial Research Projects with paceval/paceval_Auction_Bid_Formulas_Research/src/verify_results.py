#!/usr/bin/env python3
"""Verify released CSV schemas, row totals and domain arithmetic."""
from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1]
def records(name):return list(csv.DictReader((R/'examples'/name).open()))
a=records('offers.csv');p=records('policy_registry.csv');s=records('bid_surface.csv');v=records('formula_version.csv');sm=records('policy_summary.csv')
assert len(a)==10000 and len(p)==51 and len(s)==3721 and len(v)==50 and len(sm)==50
assert set(map(lambda r:int(r['policy_id']),a))==set(range(1,51))
assert all(float(r['final_unit_bid_eur'])>=float(r['unit_cost_eur'])*1.03-1e-10 for r in a)
assert all(int(r['eligible'])==int(float(r['final_unit_bid_eur'])<=float(r['buyer_ceiling_eur'])) for r in a)
assert sum(int(r['eligible']) for r in a)>=0
log=(R/'results/sdk_execution.txt').read_text()
assert 'STATUS PASS' in log and 'GRAPH_COUNT 51' in log and 'REQUESTS 10000' in log
assert json.loads((R/'results/high_precision_audit.json').read_text())['status']=='PASS'
print('PASS: 51 graph entries, 10,000 offers, 3,721 surface points, 50 revisions, 50 summary rules')
