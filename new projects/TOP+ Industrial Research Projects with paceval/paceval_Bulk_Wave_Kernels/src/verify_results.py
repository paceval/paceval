#!/usr/bin/env python3
"""Deterministic output & convergence integrity checks for WP_044."""
from pathlib import Path
import csv,json,math
R=Path(__file__).resolve().parents[1]
run=json.loads((R/'results'/'execution_summary.json').read_text())
assert run['paceval_persistent_graphs']==28
assert run['mode_count']==4
assert run['max_oracle_scaled_difference']<1e-10
con=list(csv.DictReader((R/'examples'/'grid_convergence.csv').open()))
assert len(con)==12
modes=sorted(set(r['mode'] for r in con));assert len(modes)==4
for m in modes:
    r=sorted((x for x in con if x['mode']==m),key=lambda x:int(x['n']))
    assert [int(x['n']) for x in r]==run['grid_sizes']
    for a,b in zip(r,r[1:]):
        assert float(b['l2_error'])<float(a['l2_error'])/3.5
        assert 1.9<float(b['observed_order'])<2.1
    assert float(r[-1]['l2_error'])<4e-5
nrows=0
with (R/'examples'/'energy_and_error_diagnostics.csv').open() as f:
    for r in csv.DictReader(f):
        nrows+=1
        for key in ('weighted_energy','l2_error','linf_error','flux_left_proxy','flux_right_proxy','source_power'):
            assert math.isfinite(float(r[key])),(key,r)
assert nrows>=100
num=0
with (R/'examples'/'parameterized_kernel_surface.csv').open() as f:
    for r in csv.DictReader(f):
        num+=1
        assert abs(float(r['version_delta'])+float(r['exact_mms'])*.4)<1e-11
        assert abs(float(r['rhs_v2'])-float(r['rhs_v1'])-float(r['version_delta']))<1e-9
assert num==7623
registry=list(csv.DictReader((R/'examples'/'formula_registry.csv').open()))
assert len(registry)==28 and len(set(r['id'] for r in registry))==28
inv=list(csv.DictReader((R/'results'/'math_execution_inventory.csv').open()))
assert sum(r['execution_owner']=='paceval' for r in inv)==28
print('PASS 4 modes, 12 converged runs, 28 live graphs, 7,623 versioned parameter points, energy diagnostics and inventories')
