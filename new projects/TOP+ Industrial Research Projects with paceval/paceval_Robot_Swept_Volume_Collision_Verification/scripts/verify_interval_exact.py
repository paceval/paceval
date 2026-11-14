#!/usr/bin/env python3
"""EXACT rational Bernstein subdivision for degree-4 sphere clearance.

A strictly positive Bernstein lower bound certifies separation on an interval.
An exactly negative rational witness certifies overlap at a particular time.
An exactly zero witness rules out strict separation but never alone certifies
that this witness is the global minimum. Inconclusive cases remain UNRESOLVED.
No certification of non-spherical robots, measured model errors or controller dynamics.
"""
import csv,json,sys,math
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from collections import Counter
from math import comb
ROOT=Path(__file__).resolve().parents[1]
DEST=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results'
IN=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'input/cases.csv'
@lru_cache(maxsize=5000)
def frac(s):return F(s)
def polynomial(c,version):
 x=[frac(c[f'{axis}{degree}']) for degree in range(3) for axis in []] if False else None
 poly=[F(0) for i in range(5)]
 for axis in 'xyz':
  a=[frac(c[axis+str(i)]) for i in range(3)]
  for i in range(3):
   for j in range(3):poly[i+j]+=a[i]*a[j]
 radius=frac(c['r1'])+frac(c['r2'])+(frac(c['buffer']) if version=='V2' else F(0))
 poly[0]-=radius*radius
 return poly
def bernstein(a):
 return tuple(sum((a[j]*F(comb(k,j),comb(4,j)) for j in range(k+1)),F(0)) for k in range(5))
def split(b):
 levels=[b]
 while len(levels[-1])>1:levels.append(tuple((levels[-1][j]+levels[-1][j+1])/2 for j in range(len(levels[-1])-1)))
 return tuple(level[0] for level in levels),tuple(level[-1] for level in levels[::-1])
def test_case(a,max_depth=22):
 b0=bernstein(a); todo=[(b0,F(0),F(1),0)]; touched=False;witness=None;status='SEPARATED';split_count=0;maxdepth=0
 while todo:
  b,lo,hi,depth=todo.pop();maxdepth=max(maxdepth,depth)
  if min(b)>0:continue
  mid=(lo+hi)/2
  # Exact coefficients ensure no floating-point decision is hidden here.
  if b[0]<0:status='OVERLAP';witness=lo;break
  if b[-1]<0:status='OVERLAP';witness=hi;break
  if b[0]==0:touched=True;witness=lo
  if b[-1]==0:touched=True;witness=hi
  left,right=split(b);val=left[-1]
  if val<0:status='OVERLAP';witness=mid;break
  if val==0:touched=True;witness=mid
  if depth>=max_depth:
   if min(b)<0:status='UNRESOLVED'
   continue
  split_count+=1
  todo.append((right,mid,hi,depth+1));todo.append((left,lo,mid,depth+1))
 if status=='SEPARATED' and touched:status='CONTACT_WITNESS_NO_OVERLAP_PROVEN'
 return status,witness,split_count,maxdepth
rows={x['case_id']:x for x in csv.DictReader(IN.open())}
results=list(csv.DictReader((DEST/'screening.csv').open()))
audit=[];counter=Counter();consistency=0;uncertain=[];weak=[]
for rec in results:
 case=rows[rec['case_id']];pol=polynomial(case,rec['model']);status,wit,split_count,depth=test_case(pol)
 counter[status]+=1
 numeric=float(rec['min_squared_margin_m2']);
 # A true exact SAFE certificate must agree with the numerical global-minimum candidate.
 if status=='SEPARATED' and numeric <= -2e-8:raise AssertionError(('false safe',rec['case_id'],rec['model'],numeric))
 if status=='OVERLAP' and numeric > 2e-8:raise AssertionError(('false collision',rec['case_id'],rec['model'],numeric))
 if status=='CONTACT_WITNESS_NO_OVERLAP_PROVEN' and numeric > 2e-7:raise AssertionError(('missed contact',rec['case_id'],rec['model'],numeric))
 consistency+=1
 if status=='UNRESOLVED':uncertain.append(rec['case_id']+':'+rec['model'])
 audit.append({'case_id':rec['case_id'],'model':rec['model'],'exact_interval_status':status,'witness_time':str(wit) if wit is not None else '', 'subdivision_nodes':split_count,'max_depth':depth,'native_global_min_margin_m2':rec['min_squared_margin_m2']})
DEST.mkdir(exist_ok=True,parents=True)
with (DEST/'exact_interval_certificates.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
summary={'method':'exact rational Bernstein degree-4 enclosure and exact rational witnesses on normalized [0,1]','input_representation':'all input coordinate/radius scalars are exact dyadic fractions of 1/256; no decimal rounding assumption','certificate_count':len(audit),'label_counts':dict(counter),'consistency_checks':consistency,'uncertified_cases':uncertain[:60],'uncertified_case_count':len(uncertain),'scope':'3D quadratic relative center trajectories of two conservatively bounded spheres; exact polynomial of the entered dyadic coefficients; no safety certification of articulated robotics','max_subdivision_depth':22,'known_narrow_case':{x['model']:x['exact_interval_status'] for x in audit if x['case_id']=='T00000'},'known_tangent_case':{x['model']:x['exact_interval_status'] for x in audit if x['case_id']=='T00001'}}
(DEST/'exact_interval_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
assert len(audit)==len(results)
assert summary['known_narrow_case']['V1']=='OVERLAP'
assert summary['known_tangent_case']['V1']=='CONTACT_WITNESS_NO_OVERLAP_PROVEN'
print('EXACT INTERVAL VERIFICATION PASS',json.dumps({k:summary[k] for k in ('certificate_count','label_counts','uncertified_case_count','known_narrow_case','known_tangent_case')}))
