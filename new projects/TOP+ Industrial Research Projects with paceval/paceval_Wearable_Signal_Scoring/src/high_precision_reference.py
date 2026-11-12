#!/usr/bin/env python3
"""Independent 80-digit mathematical oracle and signal-extraction checks for WP_036."""
import csv, json
from pathlib import Path
from mpmath import mp
mp.dps=80
ROOT=Path(__file__).resolve().parents[1]
def score(f,A,B,a,c,h,m,p,q):
 if f==0:z=A*a+B*c+mp.mpf('.14')*h-mp.mpf('.37')
 elif f==1:z=A*q-B*m+mp.mpf('.27')*p-mp.mpf('.30')
 elif f==2:z=A*a*c+B*p*q-mp.mpf('.28')*m-mp.mpf('.37')
 elif f==3:z=A*mp.sin(a)+B*mp.cos(h)+mp.mpf('.32')*q-mp.mpf('.42')*m-mp.mpf('.43')
 elif f==4:z=A*mp.log(1+a*a)+B*mp.exp(-m*m)+mp.mpf('.19')*p*q-mp.mpf('.66')
 else:raise ValueError(f)
 return 1/(1+mp.exp(-z))
registry={int(r['id']):r for r in csv.DictReader((ROOT/'examples'/'formula_registry.csv').open())}
records=list(csv.DictReader((ROOT/'examples'/'wearable_feature_windows.csv').open()))
indices=sorted(set(round(i*(len(records)-1)/499) for i in range(500)))
max_abs=mp.mpf(0)
for j in indices:
 r=records[j]; rr=registry[int(r['formula_id'])]
 x=[mp.mpf(r[k]) for k in ('a','c','h','m','p','q')]
 actual=mp.mpf(r['score'])
 expected=score(int(rr['family'])-1,mp.mpf(rr['alpha']),mp.mpf(rr['beta']),*x)
 delta=abs(actual-expected);max_abs=max(delta,max_abs)
 assert delta<mp.mpf('5e-13'),(j,delta)
# Independently recompute PPG/IMU window features from the four saved raw synthetic traces.
raw_checks=[]
for j in range(4):
 xs=list(csv.DictReader((ROOT/'examples'/f'synthetic_trace_{j+1}.csv').open()))
 assert len(xs)==200
 acc=[(float(r['acc_x_g']),float(r['acc_y_g']),float(r['acc_z_g'])) for r in xs]
 ppg=[float(r['ppg_normalized']) for r in xs]
 import math
 rms=math.sqrt(sum(x*x+y*y+(z-1)**2 for x,y,z in acc)/200)
 cross=sum(acc[i-1][0]<0<=acc[i][0] for i in range(1,200))
 cadence=60.*cross/8.
 mean=sum(ppg)/200;periodic=[x-mean for x in ppg]
 var=sum(v*v for v in periodic)/200
 mods=math.sqrt(var)/mean
 scores=[]
 for lag in range(12,39):
  left=periodic[lag:];right=periodic[:-lag]
  norm=math.sqrt(sum(a*a for a in left)*sum(b*b for b in right))
  scores.append((sum(a*b for a,b in zip(left,right))/max(1e-12,norm),lag))
 best,lag=max(scores,key=lambda t:t[0]);best=max(0.,min(1.,best))
 expected=[rms,cadence,1500./lag,rms*(1-best),mods,best]
 record=records[j]
 actual=[float(record[k]) for k in ('acc_rms_g','cadence_proxy_per_min','pulse_proxy_bpm','motion_artifact_proxy','ppg_modulation','ppg_periodicity')]
 for a,b in zip(actual,expected):assert abs(a-b)<1e-12,(j,a,b)
 raw_checks.append(dict(trace_id=j+1,samples=200,feature_checks=6,status='PASS'))
report=dict(project='WP036',reference_precision_decimal_digits=80,score_values_verified=len(indices),max_absolute_difference_internal_only=str(max_abs),synthetic_trace_recomputations=raw_checks,status='PASS',clinical_validation='NOT PERFORMED')
(ROOT/'results'/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: {len(indices)} 80-digit score calculations and 24 independently reconstructed trace features')
