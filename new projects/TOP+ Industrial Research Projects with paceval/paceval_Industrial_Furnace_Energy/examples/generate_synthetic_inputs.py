#!/usr/bin/env python3
"""Generate all 61 deterministic WP30 synthetic input cases. No randomness is used.
This input generator never writes paceval results or simulated paceval outputs.
"""
from pathlib import Path
import csv
R=Path(__file__).resolve().parents[1]
V=['mf','LHV','eta','mp','cp','Tin','Tout','beta','U','A','Tw','Tamb','eps','sigma','mex','cpe','Tex','rec','efco2','cNOx','qflue','capco2','capnox','fuelcap','Tmax']
rows=[]
for j,Tw in enumerate([350,360,370,380,390,400,410]):
 for i,mf in enumerate([.025,.03,.035,.04,.045,.05,.055]):
  rows.append([f'F{j*7+i+1:03d}',mf,45000000,.87,2,620,300,970,.00012,9,62,Tw,295,.78,5.670374419e-8,1.05,1120,770,.35,2.75,[90,100,110,120,130,140,150][j],2.25,.13,.00034,.052,990])
for j,rec in enumerate([0,.35,.65]):
 for i,mf in enumerate([.03,.035,.04,.045]):
  rows.append([f'S{j*4+i+1:03d}',mf,45000000,.87,2,620,300,970,.00012,9,62,380,295,.78,5.670374419e-8,1.05,1120,770,rec,2.75,[95,120,145][j],2.25,.13,.00034,.052,990])
out=R/'examples/synthetic_operating_points.csv'
with out.open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['case_id']+V);w.writerows(rows)
print(f'Generated {len(rows)} deterministic synthetic cases: {out}')
