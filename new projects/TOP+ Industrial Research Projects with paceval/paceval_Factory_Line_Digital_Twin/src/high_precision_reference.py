#!/usr/bin/env python3
"""Numerically independent 80-digit audit of selected original paceval CSV outputs."""
from pathlib import Path
import csv,json
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parent.parent
rows=list(csv.DictReader((ROOT/'examples'/'paceval_operation_results.csv').open()))
samples=[rows[i] for i in range(0,len(rows),max(1,len(rows)//50))]
checks=0;max_scaled=mp.mpf(0)
for r in samples:
 b,w,T,l,phi=map(mp.mpf,[r['base_min'],r['wear'],r['temp_C'],r['load'],r['phase']])
 for k in range(20):
  bias=mp.mpf(k)-mp.mpf('9.5');bias*=mp.mpf('.010')
  osc=mp.mpf(k%4+1)*mp.mpf('.003');coup=mp.mpf((k%5)-2)*mp.mpf('.006')
  val=b*(1+bias+mp.mpf('.011')*w+mp.mpf('.0009')*(T-22)**2+mp.mpf('.014')*l+osc*mp.sin(phi+mp.mpf(k)*mp.mpf('.09'))+coup*w*l)
  given=mp.mpf(r[f'cycle_v{k+1:02d}']);error=abs(val-given)/(1+abs(val));max_scaled=max(max_scaled,error)
  assert error<mp.mpf('3e-12'),(k,str(error));checks+=1
 prob=mp.mpf('.006')+mp.mpf('.01')*w+mp.mpf('.00007')*(T-22)**2
 energy=mp.mpf('.018')*b*(1+mp.mpf('.2')*l)
 for val,field in [(prob,'reject_probability'),(energy,'energy_kWh')]:
  d=abs(val-mp.mpf(r[field]))/(1+abs(val));max_scaled=max(max_scaled,d);assert d<mp.mpf('3e-12');checks+=1
rec={'precision_decimal_digits':80,'independent_mpmath_checks':checks,'sampled_rows':len(samples),'largest_scaled_difference':str(max_scaled),'all_passed':True,'scope':'synthetic analytical expression results; not physical model validation'}
(ROOT/'results'/'high_precision_audit.json').write_text(json.dumps(rec,indent=2)+'\n')
print(rec)
