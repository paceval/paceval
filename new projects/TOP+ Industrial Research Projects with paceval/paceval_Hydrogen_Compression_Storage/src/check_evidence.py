from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1]/'results'
e=json.loads((R/'execution_evidence.json').read_text());v=json.loads((R/'independent_validation.json').read_text())
assert e['created_unique_graphs']==e['executed_unique_graphs']==49
assert e['compressor_scenarios_per_version']==100000 and e['compressor_model_cases']==200000
assert e['compressor_stage_visits']==500000 and e['graph_point_evaluations']>9_000_000
assert e['storage_step_evaluations']==5760
assert e['independent_native_checks']>6_000_000
assert v['independent_high_precision_checks']>4000 and v['status']=='PASS'
with (R/'formula_registry.csv').open(newline='') as f:rows=list(csv.DictReader(f))
assert len(rows)==49
assert len({(x['version'],x['graph_id']) for x in rows})==49
with (R/'math_execution_inventory.csv').open(newline='') as f:inv=list(csv.DictReader(f))
assert len(inv)==51 and sum(x['execution_owner']=='paceval' for x in inv)==49
assert not list((R.parent).rglob('*.so')) and not list((R.parent).rglob('*.dll'))
for ver in ['1','2']:
    assert sum(e[f'v{ver}_status'].values())==100000
print('PASS 49 actual graph inventory rows, reference checks, output counts and runtime-exclusion rule')
