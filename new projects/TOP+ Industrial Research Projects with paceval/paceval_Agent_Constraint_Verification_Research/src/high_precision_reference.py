#!/usr/bin/env python3
"""Independent 80-digit mathematical reference for a deterministic cross-section.
Read only the exported numerical datasets. No paceval calls or shared C++ helpers.
A finite sample checks point values; it does not certify an interval or global guard.
"""
import csv,json
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parents[1]
G={int(r['guard_id']):r for r in csv.DictReader((ROOT/'examples/guard_registry.csv').open()) if r['version']=='1'}
T=mp.mpf('1e-8')
def calc(g,x,y,z):
 a,b,c,k=[mp.mpf(g[key]) for key in ('a','b','c','k')]
 f=int(g['family'])
 if f==0:return c-x
 if f==1:return c-(x/a)**2-(y/b)**2
 if f==2:return c-x*x-k*y*y-mp.mpf('0.1')*z*z
 if f==3:return c+a*x-b*y+k*z
 return c-mp.exp(k*x)+a*mp.cos(y)-b*z*z
def verdict(v):return 'ACCEPT' if v>T else 'REJECT' if v< -T else 'REVIEW_BOUNDARY'
rows=list(csv.DictReader((ROOT/'examples/constraint_evaluations.csv').open()))
# Regular stride samples all five families and both interior and boundary cases.
chosen=rows[::169][:592]+[r for r in rows if int(r['sample_id']) in (0,2,4,6,8,10,12,14) and int(r['guard_id'])%167==0]
checked=0;max_difference=mp.mpf('0'); disagreement=0
for r in chosen:
 g=G[int(r['guard_id'])]
 x,y,z=[mp.mpf(r[k]) for k in ('x','y','z')]
 ref=calc(g,x,y,z)
 got=mp.mpf(r['paceval_margin'])
 diff=abs(ref-got);max_difference=max(max_difference,diff)
 if diff>mp.mpf('2e-12')*(1+abs(ref)):raise RuntimeError(f'High-precision mismatch: {r}')
 if verdict(ref)!=r['decision']:disagreement+=1
 checked+=1
if disagreement:raise RuntimeError(f'{disagreement} decisions disagree with 80-digit reference')
summary={'status':'PASS','precision_digits':80,'samples_checked':checked,'decision_mismatches':disagreement,'max_abs_difference':mp.nstr(max_difference,16), 'qualification':'Compares decimal representations of serialized floating-point inputs and outputs; does not provide global certification.'}
(ROOT/'results/high_precision_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
