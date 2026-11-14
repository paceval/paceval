#!/usr/bin/env python3
"""Synthetic, deterministic *not measured* fleet loading and transformer metadata."""
from pathlib import Path
import csv,math
root=Path(__file__).resolve().parents[1];root.joinpath('input').mkdir(exist_ok=True)
fields=['asset_id','rated_A','lossR','topRated_K','hotRated_K','n','m','tauOil_h','tauHot_h','coolFactor','initTop_K','initHot_K','limitHS_C','limitOil_C','limitFAA','limitLoad','refTemp_C']
with (root/'input/transformer_parameters.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(fields)
 for i in range(48):
  w.writerow([f'TR{i:03d}',600+7*i,4.1+(i%7)*.2,47+2*(i%5),21+(i%4)*2,.78+(i%3)*.035,.75+(i%4)*.04,2.3+(i%6)*.26,.24+(i%5)*.075, .94+(i%6)*.035,35+(i%3)*2,14+(i%4)*1.5,110+(i%6)*3,96+(i%4)*3,7+(i%5)*1.2,1.36+(i%3)*.05,110])
with (root/'input/transformer_profiles.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['scenario','asset_id','hour','ambient_C','current_A','rated_A','dt_h'])
 for scenario in ('baseline','heatwave','overload'):
  for hour in range(24*14):
   tod=hour%24;day=hour//24
   for i in range(48):
    rated=600+7*i
    ambient=23+5.5*math.sin(2*math.pi*(tod-9)/24)+1.5*math.sin(2*math.pi*day/13)+(10 if scenario=='heatwave' else 2.5 if scenario=='overload' else 0)+.14*(i%5)
    load=.84+.135*math.sin(2*math.pi*(tod-7)/24)+.065*math.sin(2*math.pi*(day+i%6)/14)+.023*(i%7)
    if scenario=='heatwave':load+=.06
    if scenario=='overload':load+=(0.34 if 17<=tod<=22 else .11)
    w.writerow([scenario,f'TR{i:03d}',hour,f'{ambient:.12f}',f'{rated*load:.12f}',rated,1])
print('Generated 48 synthetic transformers x 14 days x 3 scenarios = 48,384 hourly inputs')
