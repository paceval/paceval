#!/usr/bin/env python3
"""Independent 90-decimal mpmath evaluation of full pointwise formulas and cubic stationary roots.
The reference evaluates x,y,z and radius directly, not the paceval formula strings.
"""
import csv,sys,json,math
from pathlib import Path
from collections import Counter
import mpmath as mp
from fractions import Fraction
mp.mp.dps=90
R=Path(__file__).resolve().parents[1];DEST=Path(sys.argv[1]) if len(sys.argv)>1 else R/'results';IN=Path(sys.argv[2]) if len(sys.argv)>2 else R/'input/cases.csv'
raw={x['case_id']:x for x in csv.DictReader(IN.open())}
results=list(csv.DictReader((DEST/'screening.csv').open()))
def coeff(c):
 return [[mp.mpf(c[s+str(j)]) for j in range(3)] for s in 'xyz']
def f(x,t,r):
 coords=[v[0]+v[1]*t+v[2]*t*t for v in x]
 d2=sum(v*v for v in coords)
 dr=2*sum((v[0]+v[1]*t+v[2]*t*t)*(v[1]+2*v[2]*t) for v in x)
 return d2-r*r,mp.sqrt(d2)-r,dr
def cubic(x):
 a=[mp.mpf('0')]*5
 for p in x:
  for i in range(3):
   for j in range(3):a[i+j]+=p[i]*p[j]
 return [a[i]*i for i in range(1,5)]
def polyval(a,t):
 y=mp.mpf(0)
 for z in reversed(a):y=y*t+z
 return y
def quadratic_roots(a,b,c):
 tol=mp.mpf('1e-65')
 if abs(a)<tol:
  return [-c/b] if abs(b)>tol else []
 d=b*b-4*a*c
 if d<0:return []
 sq=mp.sqrt(d)
 return [(-b-sq)/(2*a),(-b+sq)/(2*a)]
def stationary_times(x):
 d=cubic(x);qc=quadratic_roots(3*d[3],2*d[2],d[1]);parts=[mp.mpf(0),mp.mpf(1)]+[z for z in qc if 0<z<1];parts.sort()
 roots=[]
 for a in parts:
  if abs(polyval(d,a))<mp.mpf('1e-65'):roots.append(a)
 for i in range(len(parts)-1):
  lo=parts[i];hi=parts[i+1];fl=polyval(d,lo);fh=polyval(d,hi)
  if fl*fh<0:
   for k in range(280):
    mid=(lo+hi)/2;fm=polyval(d,mid)
    if fm*fl>0:lo=mid;fl=fm
    else:hi=mid
   roots.append((lo+hi)/2)
 out=[]
 for r in roots:
  if not any(abs(r-q)<mp.mpf('1e-50') for q in out):out.append(r)
 return sorted(out)
checks=0;models=Counter();cases=0;max_diff_margin=0;max_diff_time=0
for index,row in enumerate(results):
 if index>40 and index%17!=0:continue
 c=raw[row['case_id']];x=coeff(c);r=mp.mpf(c['r1'])+mp.mpf(c['r2'])+(mp.mpf(c['buffer']) if row['model']=='V2' else 0)
 t=mp.mpf(row['min_time_normalized']);value,clear,der=f(x,t,r)
 for name,expected,tol in [('min_squared_margin_m2',value,'1e-7'),('min_surface_clearance_m',clear,'1e-7'),('derivative_at_min',der,'1e-6')]:
  actual=mp.mpf(row[name]);diff=abs(actual-expected)
  if diff>mp.mpf(tol)*(1+abs(expected)):raise AssertionError((row['case_id'],row['model'],name,str(diff)))
  checks+=1
 times=[mp.mpf(0),mp.mpf(1)]+stationary_times(x)
 mn,tm=min((f(x,z,r)[0],z) for z in times)
 diff=abs(mp.mpf(row['min_squared_margin_m2'])-mn)
 if diff>mp.mpf('1e-7')*(1+abs(mn)):raise AssertionError(('global minimum mismatch',row['case_id'],row['model'],str(diff)))
 max_diff_margin=max(max_diff_margin,float(diff))
 checks+=1
 if abs(mn)>mp.mpf('1e-5') and 0<tm<1:
  if abs(t-tm)>mp.mpf('2e-7'):raise AssertionError(('minimum time mismatch',row['case_id'],str(tm),str(t)))
  max_diff_time=max(max_diff_time,float(abs(t-tm)))
 checks+=1;cases+=1;models[row['model']]+=1
out={'status':'PASS','decimal_precision':90,'checked_case_model_rows':cases,'independent_checks':checks,'model_coverage':dict(models),'largest_observed_margin_difference':max_diff_margin,'largest_observed_interior_time_difference':max_diff_time,'reference_method':'independently implemented physical center-distance equations, high-precision derivative cubic root isolation and global endpoint/stationary evaluation'}
(DEST/'high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print('HIGH PRECISION PASS',cases,checks,'at 90 decimal digits')
