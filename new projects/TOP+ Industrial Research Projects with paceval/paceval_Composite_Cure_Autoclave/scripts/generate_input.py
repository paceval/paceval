#!/usr/bin/env python3
"""Deterministic synthetic ramp/dwell/part-thickness experiment, NOT a resin product sheet."""
from pathlib import Path
import csv
p=Path(__file__).resolve().parents[1]/'input'/'recipes.csv'
with p.open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f,lineterminator='\n')
 w.writerow(['recipe_id','thickness_m','ramp_C_min','hold_C','hold_min','convection_W_m2K','pressure_bar'])
 i=0
 for thickness in [0.010,0.014,0.018]:
  for ramp in [1.,2.,3.]:
   for temp in [145.,155.,165.,175.]:
    i+=1
    w.writerow([f'R{i:03}',f'{thickness:.3f}',f'{ramp:.1f}',f'{temp:.1f}',f'{80+(i%3)*15:.1f}',f'{55+(i%5)*9:.1f}',f'{4.0+(i%3)*0.65:.2f}'])
print('Created',p,'with',i,'synthetic recipes')
