#!/usr/bin/env python3
import csv,sys,json
from pathlib import Path
p=Path(sys.argv[1]);reg=list(csv.DictReader((p/'results/graph_registry.csv').open()));inv=list(csv.DictReader((p/'results/math_execution_inventory.csv').open()))
assert len(reg)==35, f'Expected 35 real registered and executed graphs, got {len(reg)}'
ids={g['graph_id'] for g in reg};assert len(ids)==len(reg)
assert all(r['executed']=='yes' for r in reg)
assert {r['paceval_graph_id'] for r in inv if r['execution_owner']=='paceval'}==ids
assert any(g['version']=='v1' for g in reg) and any(g['version']=='v2' for g in reg)
rows=list(csv.DictReader((p/'results/decision_results.csv').open()))
assert len(rows)==3384
assert {r['status'] for r in rows}=={'ACCEPT','REVIEW','REJECT'}
assert all(abs(float(r['path_coverage'])-1)<1e-12 for r in rows)
assert all(abs(float(r['base_score'])-float(r['nested_score']))<1e-11 for r in rows)
print(f'PASS: {len(reg)} graph registry entries, {len(rows)} scenario outputs, complete inventory')
