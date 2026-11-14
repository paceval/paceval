#!/usr/bin/env python3
"""Cross-check actual collected evidence and model/curve artifacts against public report claims."""
from pathlib import Path
import json,csv
R=Path(__file__).resolve().parent.parent;d=R/'results'
e=json.loads((d/'execution_evidence.json').read_text())
assert e['model_versions']==2 and e['input_pairs']>=250000
assert e['model_point_cases']==e['input_pairs']*2
assert e['unique_graphs_created']==e['unique_graphs_executed']
assert e['graph_point_evaluations']>5000000
assert e['native_reference_checks']>=e['model_point_cases']*10
with open(d/'formula_registry.csv') as f:
 rows=list(csv.DictReader(f))
assert len(rows)<=e['unique_graphs_created'] and len(rows)>=50
versions={r['version'] for r in rows};assert versions=={'V1','V2'}
with open(d/'column_configurations.csv') as f:
 cols=list(csv.DictReader(f))
assert len(cols)==e['stagewise_configurations']
assert set(r['feasible'] for r in cols).issubset({'0','1'})
for r in cols:
 assert abs(float(r['component_balance_residual']))<1e-8
assert json.loads((d/'independent_validation.json').read_text())['status']=='PASS'
print('EVIDENCE PASS',e['unique_graphs_executed'],'graphs,',e['graph_point_evaluations'],'outputs,',len(cols),'columns')
