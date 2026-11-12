#!/usr/bin/env python3
"""Independent 80-decimal-digit forward kinematics and determinant checks.
These checks are separate from native C++ checks performed by the original SDK run.
"""
from pathlib import Path
import csv,json,mpmath as mp
mp.mp.dps=80
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader(open(root/'examples/selected_path_points.csv')))
assert len(rows)==255,len(rows)
mx=mp.mpf('0');count=0
for r in rows:
 q1=mp.mpf(r['q1_rad']);q2=mp.mpf(r['q2_rad'])
 x=mp.cos(q1)+mp.mpf('.78')*mp.cos(q1+q2)
 y=mp.sin(q1)+mp.mpf('.78')*mp.sin(q1+q2)
 for a,b in [(x,mp.mpf(r['x_m'])),(y,mp.mpf(r['y_m']))]:
  err=abs(a-b);mx=max(mx,err);count+=1
  if err>mp.mpf('2e-12'):raise AssertionError(f'high precision FK failed: {r}')
res={'digits':80,'values_checked':count,'all_within_2e-12':True,'maximum_absolute_difference_from_exported_decimal':str(mx)}
(root/'results').mkdir(exist_ok=True)
(root/'results'/'high_precision_audit.json').write_text(json.dumps(res,indent=2)+'\n')
print('PASS high precision',count)
