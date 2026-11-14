#!/usr/bin/env python3
"""Deterministic synthetic parameters. These are NOT supplier measurements."""
import csv,itertools,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
cols=['case_id','H3_m','W_m','C3_invK','beta','T_K']
with (root/'input/scenarios.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(cols)
 for i,(h,width,cte,beta,t) in enumerate(itertools.product(
  [250e-6,400e-6,550e-6,700e-6],
  [12e-3,16e-3,20e-3,24e-3,28e-3],
  [10e-6,15e-6,20e-6,25e-6],
  [0.0006,0.0012,0.0018,0.0024],
  [298,328,358,388]),1):
  w.writerow([f'P{i:05d}',format(h,'.17g'),format(width,'.17g'),format(cte,'.17g'),format(beta,'.17g'),format(t,'.17g')])
print('Synthetic scenarios:',i)
