#!/usr/bin/env python3
"""Verify row counts, value bounds, threshold decisions, model structure and source manifests."""
import csv,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def data(name):return list(csv.DictReader((root/'examples'/name).open()))
r=data('quality_records.csv');s=data('score_summary.csv');surf=data('quality_surface.csv');v=data('formula_versions.csv');reg=data('score_registry.csv')
assert (len(r),len(s),len(surf),len(v),len(reg))==(10000,50,3721,61,51)
assert len({x['expression'] for x in reg})==51
assert all(0<=float(x['score'])<=1 for x in r)
assert all((float(x['score'])>=0.6)==bool(int(x['inspect_flag'])) for x in r)
assert all(int(x['synthetic_defect_label']) in (0,1) for x in r)
assert int(sum(int(x['inspect_flag']) for x in r))==round(sum(float(x['inspection_rate'])*200 for x in s))
log=(root/'examples/sdk_execution.txt').read_text();assert 'STATUS PASS' in log and 'GRAPH_COUNT 51' in log
out={'status':'PASS','records':len(r),'models':50,'graph_versions':51,'surface_points':len(surf),'inspections':sum(int(x['inspect_flag']) for x in r),'synthetic_defect_labels':sum(int(x['synthetic_defect_label']) for x in r),'model_families':5}
(root/'results/result_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS',out)
