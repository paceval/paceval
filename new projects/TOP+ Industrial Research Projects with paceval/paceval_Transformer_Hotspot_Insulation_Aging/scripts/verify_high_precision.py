#!/usr/bin/env python3
"""Independent, high precision two-state thermal reference, not expression-string replay.
Inputs are the precise binary64 numbers presented to the original SDK.
The intentionally approximate *physical model* is distinct from arithmetic validation.
"""
import csv, json, sys
from pathlib import Path
from collections import defaultdict
import mpmath as mp
mp.mp.dps=85
M=lambda v:mp.mpf(float(v))

def load(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))

def verify(resdir,inpdir):
 resdir=Path(resdir);inpdir=Path(inpdir)
 par={p['asset_id']:{k:M(v) for k,v in p.items() if k!='asset_id'} for p in load(inpdir/'transformer_parameters.csv')}
 recorded=load(resdir/'hotspot_timeseries.csv');summaries={(v['scenario'],v['asset_id'],v['model']):v for v in load(resdir/'asset_summary.csv')}
 cases=load(inpdir/'transformer_profiles.csv')
 selected={'TR000','TR007','TR023','TR041'}
 cases={(x['scenario'],x['asset_id'],int(x['hour'])):x for x in cases if x['asset_id'] in selected}
 # independent state per scenario, asset and model; check all 336 hours of selected chains.
 state={};assertions=0;failures=[];max_error=defaultdict(float)
 def check(label,expected,actual,absolute=mp.mpf('8e-6'),relative=mp.mpf('7e-8')):
  nonlocal assertions
  assertions+=1
  d=abs(expected-actual);max_error[label]=max(max_error[label],float(d))
  if d>absolute+relative*max(abs(expected),abs(actual)):
   if len(failures)<20:failures.append({'quantity':label,'independent_ref':str(expected),'actual_output':str(actual),'abs_difference':str(d)})
 for z in recorded:
  sc,asset,ver,h=z['scenario'],z['asset_id'],z['model'],int(z['hour'])
  if asset not in selected:continue
  p=par[asset];orig=cases[(sc,asset,h)];k=(sc,asset,ver)
  if k not in state:
   state[k]=(p['initTop_K'],p['initHot_K'],mp.mpf('0'),mp.mpf('-200'),mp.mpf('1e6'),True)
  oldTo,oldHot,oldAge,oldPeak,oldMin,allgood=state[k]
  ambient=M(orig['ambient_C']);ratio=M(orig['current_A'])/M(orig['rated_A']);dt=M(orig['dt_h']);q=(ratio**2*p['lossR']+1)/(p['lossR']+1)
  steadyOil=p['topRated_K']*p['coolFactor']*q**p['n']
  steadyHot=p['hotRated_K']*ratio**(2*p['m'])
  oilMem=mp.exp(-dt/(p['tauOil_h']*p['coolFactor']))
  hotMem=mp.mpf('0') if ver=='V1' else mp.exp(-dt/p['tauHot_h'])
  oilRise=steadyOil*(1-oilMem)+oldTo*oilMem
  hotRise=steadyHot*(1-hotMem)+oldHot*hotMem
  oilTemp=ambient+oilRise;hs=oilTemp+hotRise
  fa=mp.exp(mp.mpf(15000)/(p['refTemp_C']+M(273.15))-mp.mpf(15000)/(hs+M(273.15)))
  age=oldAge+dt*fa;peak=max(oldPeak,hs)
  margin=p['limitHS_C']-hs;oilmargin=p['limitOil_C']-oilTemp;faamargin=p['limitFAA']-fa;loadmargin=p['limitLoad']-ratio
  guard=margin>=0 and oilmargin>=0 and faamargin>=0 and loadmargin>=0
  dSteadyOil=p['topRated_K']*p['coolFactor']*p['n']*q**(p['n']-1)*2*p['lossR']*ratio/(p['lossR']+1)
  dSteadyHot=p['hotRated_K']*2*p['m']*ratio**(2*p['m']-1)
  dHsDK=(1-oilMem)*dSteadyOil+(1-hotMem)*dSteadyHot
  dFaaDhs=fa*15000/(hs+M(273.15))**2
  expected=[('load_ratio',ratio,'load_ratio'),('top_rise',oilRise,'top_rise_K'),('hot_rise',hotRise,'winding_rise_K'),('hotspot',hs,'hotspot_C'),('top_oil',oilTemp,'top_oil_C'),('aging',fa,'aging_factor'),('aging_increment',dt*fa,'aging_increment_h'),('cumulative_aging',age,'cumulative_aging_h'),('peak',peak,'peak_hotspot_C'),('hotspot_margin',margin,'hotspot_margin_K'),('oil_margin',oilmargin,'oil_margin_K'),('aging_margin',faamargin,'aging_margin'),('load_margin',loadmargin,'load_margin'),('dHs_dK',dHsDK,'dHs_dK_K'),('dFAA_dHs',dFaaDhs,'dFAA_dHs_perK'),('dFAA_dK',dFaaDhs*dHsDK,'dFAA_dK'),('compound_guard',mp.mpf(1 if guard else 0),'compound_guard')]
  for label,val,column in expected:check(label,val,M(z[column]))
  state[k]=(oilRise,hotRise,age,peak,min(oldMin,margin),allgood and guard)
 for key,val in state.items():
  row=summaries[key];a,b,age,peak,mini,allgood=val
  check('total_equiv_aging',age,M(row['equivalent_aging_h']))
  check('series_peak_hotspot',peak,M(row['peak_hotspot_C']))
  check('series_min_margin',mini,M(row['min_hotspot_margin_K']))
  check('series_feasibility',mp.mpf(int(allgood)),M(row['all_intervals_within_illustrative_limits']))
 result={'method':'independent mpmath reference at 85-decimal-digit precision using binary64 input interpretations','selected_asset_count':len(selected),'selected_complete_series':len(state),'selected_model_hour_records':sum(1 for z in recorded if z['asset_id'] in selected),'reference_assertions':assertions,'all_passed':not bool(failures),'failures':failures,'max_absolute_differences_internal':dict(max_error),'tolerances':{'absolute':8e-6,'relative':7e-8},'caution':'The verification establishes agreement with the declared simplified thermal model only; it does not validate transformer design constants, aging lifetime, IEEE C57.91-2025 implementation, calibration or safety.'}
 with (resdir/'high_precision_audit.json').open('w') as f:json.dump(result,f,indent=2,sort_keys=True)
 if failures:raise RuntimeError(f'High precision failed {len(failures)} first errors: {failures[:3]}')
 print(f'HIGH-PRECISION PASS: {assertions} checks for {len(state)} complete asset-scenario-model thermal histories')
 return result
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('Usage: verify_high_precision.py results/ input/')
 verify(sys.argv[1],sys.argv[2])
