#!/usr/bin/env python3
"""Generate deterministic synthetic scenario inputs, not physical plant observations."""
from pathlib import Path
import csv
out=Path(__file__).resolve().parents[1]/'input'/'scenarios.csv'
columns=['scenario_id','Tc','UA','Ea','kref','tau','Cin','Tin','V','rhoCp','H','Tref','alpha','Tlim']
with out.open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(columns)
    for i in range(9):
        for j in range(9):
            w.writerow([f'S{i:02d}_{j:02d}',str(287+2*i),str(11200+j*1200),80000,0.02,150,3000,300,2,4000000,100000,340,0.002,345])
print(out)
