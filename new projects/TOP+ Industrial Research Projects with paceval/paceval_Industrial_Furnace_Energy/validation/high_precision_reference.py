#!/usr/bin/env python3
"""Independent 90-digit reference for synthetic WP30 experiment.
This is NOT paceval and does not claim independent experimental calibration.
"""
import csv,json,sys
from pathlib import Path
import mpmath as mp
ROOT=Path(__file__).resolve().parents[1];mp.mp.dps=90
vars=json.loads((ROOT/'src/formula_manifest.json').read_text())['variables']
inputs=list(csv.DictReader((ROOT/'examples/synthetic_operating_points.csv').open()))
obs={r['case_id']:r for r in csv.DictReader((ROOT/'results/mcp_observed_grid_transcription.csv').open())}
snap={r['case_id']:r for r in csv.DictReader((ROOT/'results/mcp_observed_snapshots.csv').open())}
tinc=list(csv.DictReader((ROOT/'results/mcp_tinc_observed.csv').open()))

# Equations are deliberately independently reimplemented with mpmath,
# not copied from the paceval expression parser or the reference graph registry.
def reference(row):
 d={k:mp.mpf(float(row[k])) for k in vars}
 f=d['mf']*d['LHV']*d['eta']
 delta=d['Tout']-d['Tin']
 q1=d['mp']*d['cp']*delta
 q2=q1+d['mp']*d['cp']*d['beta']*delta**2/2
 wall=d['U']*d['A']*(d['Tw']-d['Tamb'])
 radiation=d['eps']*d['sigma']*d['A']*(d['Tw']**4-d['Tamb']**4)
 exhaust=d['mex']*d['cpe']*(d['Tex']-d['Tamb'])
 rec=d['rec']*exhaust
 baseline=f-(q1+wall+radiation+exhaust)
 modified=f-(q2+wall+radiation+exhaust-rec)
 co2=d['mf']*d['efco2']
 nox=d['cNOx']*d['qflue']/mp.mpf(1000000)
 cap1=d['capco2']-co2;cap2=d['capnox']-nox;cap3=d['fuelcap']-d['mf'];cap4=d['Tmax']-d['Tout']
 guard1=int(all(a>=0 for a in (baseline,cap1,cap2,cap3,cap4)))
 guard2=int(all(a>=0 for a in (modified,cap1,cap2,cap3,cap4)))
 score=min(modified/f,cap1/d['capco2'],cap2/d['capnox'],cap3/d['fuelcap'],cap4/d['Tmax'])
 return dict(baseline=baseline,modified=modified,radiation=radiation,recovered=rec,guard1=guard1,guard2=guard2,score=score,fuel_req=(q2+wall+radiation+exhaust-rec)/(d['LHV']*d['eta']))

success=0;fail=[];max_err=mp.mpf(0)
def compare(case,name,got,reference,atol=mp.mpf('1e-6'),rtol=mp.mpf('1e-11')):
 global success,max_err
 x=mp.mpf(str(got));ref=mp.mpf(reference);delta=abs(x-ref)
 if delta>max_err:max_err=delta
 if delta<=atol+rtol*abs(ref):success+=1
 else:fail.append({'case':case,'field':name,'difference':str(delta),'reference':str(ref),'observed':str(x)})
for row in inputs:
 case=row['case_id'];p=reference(row)
 if case.startswith('F'):
  x=obs[case]
  for field,ref in [('Qrad_W','radiation'),('margin_v1_W','baseline'),('margin_v2_W','modified'),('guard_v1','guard1'),('guard_v2','guard2')]:
   compare(case,field,x[field],p[ref],atol=mp.mpf(0) if field.startswith('guard_') else mp.mpf('1e-6'),rtol=mp.mpf(0) if field.startswith('guard_') else mp.mpf('1e-11'))
 else:
  x=snap[case]
  for field,ref in [('Qrecovered_W','recovered'),('margin_v1_W','baseline'),('margin_v2_W','modified'),('fuel_required_v2_kg_s','fuel_req'),('score_v2','score'),('guard_v1','guard1'),('guard_v2','guard2')]:
   compare(case,field,x[field],p[ref],atol=mp.mpf(0) if field.startswith('guard_') else mp.mpf('1e-6'),rtol=mp.mpf(0) if field.startswith('guard_') else mp.mpf('1e-11'))
point_tests=0
for x in tinc:
 p=reference(next(r for r in inputs if r['case_id'].startswith('F') and float(r['mf'])==float(x['mf']) and float(r['Tw'])==float(x['Tw'])))
 for name,low,high,val in [('balance_v2','balance_v2_lower_W','balance_v2_upper_W','modified'),('radiation','radiation_lower_W','radiation_upper_W','radiation')]:
  point_tests+=1
  if not (mp.mpf(x[low])<=p[val]<=mp.mpf(x[high])):
   fail.append({'case':x['case_id'],'field':name,'error':'TINC point inclusion failed'})
assert success==329,(success,fail[:4]);assert point_tests==12
assert sum(reference(r)['guard1'] for r in inputs[:49])==14
assert sum(reference(r)['guard2'] for r in inputs[:49])==21
print('PASS: 329 independent numerical/Boolean checks; 12 TINC point inclusions; no failures. Max abs difference:',mp.nstr(max_err,12)) if not fail else print('FAIL',fail[:5])
sys.exit(int(bool(fail)))
