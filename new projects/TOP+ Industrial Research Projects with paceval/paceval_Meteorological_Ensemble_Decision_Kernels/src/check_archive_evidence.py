#!/usr/bin/env python3
import json,csv,pathlib
root=pathlib.Path(__file__).resolve().parent.parent;R=root/'results'
e=json.loads((R/'execution_evidence.json').read_text());v=json.loads((R/'validation_evidence.json').read_text())
assert e['unique_graphs_created']==60 and e['unique_graphs_executed']==60
assert e['graph_point_evaluations']==7460172
assert e['model_point_rows']==240000
assert e['surface_rows']==10086
assert e['compound_pairs_evaluated']==240000
assert v['high_precision_individual_values_verified']==20790
assert v['mathematical_check']=='passed'
with (R/'math_execution_inventory.csv').open() as f:
    rows=list(csv.DictReader(f));assert len([r for r in rows if r['execution_owner']=='paceval'])==60
with (R/'reliability_bins.csv').open() as f:
    r=list(csv.DictReader(f))
    assert r and sum(int(x['cases']) for x in r)==240000
print('ARCHIVE EVIDENCE PASSED: executed graphs, 240000 cases, surface, reliability and independent reference')
