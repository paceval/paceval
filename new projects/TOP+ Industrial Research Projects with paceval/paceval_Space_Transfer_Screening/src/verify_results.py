#!/usr/bin/env python3
"""Release preflight: executed data, mathematical invariants, images and references."""
from pathlib import Path
from PIL import Image
import csv,json,math,sys
ROOT=Path(__file__).resolve().parent.parent
rdir=ROOT/'results'; edir=ROOT/'examples'
props=dict(x.split('=',1) for x in (rdir/'execution_summary.txt').read_text().splitlines() if '=' in x)
assert props['status']=='PASS'
cases=list(csv.DictReader((edir/'transfer_candidates.csv').open()))
assert len(cases)==int(props['candidates'])==8000
assert len(list(csv.DictReader((edir/'formula_registry.csv').open())))==int(props['reusable_graphs'])==17
assert len(list(csv.DictReader((edir/'cost_surface.csv').open())))==3721
assert len(list(csv.DictReader((edir/'bielliptic_trade.csv').open())))==121
assert len(list(csv.DictReader((edir/'policy_versions.csv').open())))==101
assert sum(int(r['screen_pass']) for r in cases)==int(props['passed_screen'])==1244
assert sum(int(r['bielliptic_better_coplanar']) for r in cases)==int(props['bielliptic_lower_dv_coplanar_candidates'])==4538
for row in cases:
 d1=float(row['departure_kms']);d2=float(row['arrival_coplanar_kms']);a=float(row['arrival_with_plane_kms']);t=float(row['total_with_plane_kms']);days=float(row['time_days'])
 assert math.isfinite(t) and t>=d1+d2-1e-10 and abs(t-(d1+a))<=1e-9 and days>0
 assert 0<float(row['propellant_fraction'])<1
 assert abs(float(row['propellant_kg'])-float(row['mass_kg'])*float(row['propellant_fraction']))<1e-8
assert json.loads((rdir/'high_precision_audit.json').read_text())['pass']
assert Image.open(ROOT/'figures'/'00_space_transfer_hero.png').size==(2400,1200)
for idx in range(1,10):
 stem=next((ROOT/'figures').glob(f'{idx:02d}_*.png'))
 assert stem.with_suffix('.pdf').is_file()
 assert Image.open(stem).width>=600
assert (ROOT/'paceval_Space_Transfer_Screening_Whitepaper_EN.pdf').stat().st_size>100000
assert not (ROOT/'LICENSE_NOTICE.md').exists()
assert not any(p.suffix=='.so' for p in ROOT.rglob('*'))
print('PASS: 8000 candidates, 17 original paceval graphs, physical invariants, 9 figures, hero dimensions, PDF presence')
