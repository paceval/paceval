#!/usr/bin/env python3
"""Check completeness and semantic invariants of the released, executed WP036 CSVs."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda x:list(csv.DictReader((ROOT/'examples'/x).open()))
reg=read('formula_registry.csv');r=read('wearable_feature_windows.csv');s=read('signal_quality_surface.csv');v=read('formula_version_trace.csv')
assert len(reg)==51 and len({(x['family'],x['version'],x['expression']) for x in reg})==51
assert len(r)==10000 and len(s)==3721 and len(v)==101
assert len([x for x in reg if int(x['version'])==2])==1
assert all(0<=float(x['score'])<=1 for x in r)
assert sum(int(x['screen_flag']) for x in r)==sum(float(x['score'])>=.65 for x in r)
assert all(0<=float(x['score'])<=1 for x in s)
assert all(0<=float(x['score_v1'])<=1 and 0<=float(x['score_v2'])<=1 for x in v)
assert all(len(read(f'synthetic_trace_{j}.csv'))==200 for j in range(1,5))
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'examples').glob('*.csv')}
(ROOT/'results'/'result_manifest.json').write_text(json.dumps({'status':'PASS','windows':len(r),'graphs':len(reg),'surface_points':len(s),'trace_samples_total_recorded':800,'sha256':manifest},indent=2)+'\n')
print('PASS: 51 registered graphs, 10,000 windows, 3,721 surface points and complete reproducibility manifest')
