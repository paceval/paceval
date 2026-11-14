#!/usr/bin/env python3
"""Independent high-precision checks of the *executed* paceval CSV results.
Numerical reference equations are handwritten, not interpreted from the SDK
formula manifest. Every binary64 input is imported as its exact float value.
"""
from __future__ import annotations
import csv,json,sys,math,random
from pathlib import Path
import mpmath as mp
mp.mp.dps=90

def M(value):return mp.mpf(float(value))
def reference(data,model):
 (Fin,Fgas,Kla,Vol,Cstar,Cbulk,S,lean,maximum,Tstrip,Tfeed,cp,hx,wt,dh,hvap,etaMin,qMax,tMax)=map(M,data)
 one=mp.mpf(1); mw=mp.mpf('0.06108'); mwco2=mp.mpf('0.04401')
 raw=Kla*Vol*(Cstar-Cbulk)
 capacity=S*(maximum-lean)
 effective=raw if model=='V1' else capacity*(-mp.expm1(-raw/capacity))
 captured=min(Fin,capacity,effective)
 eta=captured/Fin; rich=lean+captured/S
 he=hx if model=='V1' else min(mp.mpf('.98'),hx+mp.mpf('.04'))
 sens=S*mw/wt*cp*(Tstrip-Tfeed)*(one-he)
 des=captured*dh
 vapor=captured*hvap*(one if model=='V1' else one+mp.mpf('.003')*(Tstrip-390))
 total=sens+des+vapor
 q=total/(captured*mwco2*1000)
 mEta=eta-etaMin; mQ=qMax-q; mL=(capacity-captured)/S;mT=tMax-Tstrip
 guard=int(all(v>=0 for v in (mEta,mQ,mL,mT)))
 score=4*eta-q-3*max(0,-mEta)-2*max(0,-mQ)
 dcap=(Vol*(Cstar-Cbulk) if raw<Fin and raw<capacity else mp.mpf(0)) if model=='V1' else (mp.exp(-raw/capacity)*Vol*(Cstar-Cbulk) if effective<Fin else mp.mpf(0))
 dqdt=(S*mw/wt*cp*(one-he)+(0 if model=='V1' else captured*hvap*mp.mpf('.003')))/(captured*mwco2*1000)
 return {'capture_mol_s':captured,'recovery':eta,'rich_loading':rich,'offgas_CO2_fraction':(Fin-captured)/(Fgas-captured),'reboiler_kW':total,'specific_duty_GJ_tCO2':q,'capture_margin':mEta,'duty_margin':mQ,'loading_margin':mL,'temp_margin':mT,'composite_guard':guard,'process_score':score,'d_capture_d_kLa':dcap,'d_specific_duty_d_Tstrip':dqdt}

def verify(result_dir,input_file,write=True):
 result_dir=Path(result_dir); records={}
 with Path(input_file).open(newline='',encoding='utf8') as f:
  for row in csv.DictReader(f):records[row['case_id']]=[float(row[x]) for x in 'Fin Fgas Kla Vol Cstar Cbulk S lean maxload Tstrip Tfeed cp hx wt dh hvap etaMin qMax tMax'.split()]
 with (result_dir/'screening.csv').open(newline='',encoding='utf8') as f:outputs=list(csv.DictReader(f))
 assert len(outputs)==len(records)*2,(len(outputs),len(records))
 checked=0;max_rel=0.;worst=[]
 sample={0,len(records)-1}|set(range(0,len(records),11))
 for row in outputs:
  index=int(row['case_id'][2:]);
  if index not in sample:continue
  ref=reference(records[row['case_id']],row['model'])
  for field,want in ref.items():
   observed=float(row[field]); expected=float(want)
   if not math.isfinite(observed):raise AssertionError('Nonfinite published value '+field)
   err=abs(observed-expected)
   tolerance=3e-7+3e-8*max(abs(expected),abs(observed))
   if err>tolerance:raise AssertionError(f'High precision check failed: {row["case_id"]} {row["model"]} {field} got={observed} expected={expected}, error={err}')
   checked+=1;max_rel=max(max_rel,err/max(1,abs(expected)))
 with (result_dir/'model_comparison.csv').open(newline='',encoding='utf8') as f:comparison=list(csv.DictReader(f))
 assert len(comparison)==len(records)
 for row in comparison[::23]:
  a=reference(records[row['case_id']],'V1');b=reference(records[row['case_id']],'V2')
  for field,expect in [('delta_capture_mol_s',b['capture_mol_s']-a['capture_mol_s']),('delta_recovery',b['recovery']-a['recovery']),('delta_duty_GJ_t',b['specific_duty_GJ_tCO2']-a['specific_duty_GJ_tCO2']),('delta_rich_loading',b['rich_loading']-a['rich_loading']),('both_feasible',int(a['composite_guard'] and b['composite_guard'])),('delta_score',b['process_score']-a['process_score'])]:
   actual=float(row[field]);target=float(expect);assert abs(actual-target)<1e-6+3e-8*abs(target),(row['case_id'],field,actual,target)
   checked+=1
 report={'reference':'independent handwritten mpmath analytical CO2 balance and energy model','precision_decimal_digits':90,'input_semantics':'exact IEEE-754 binary64 values of parsed CSV numeric tokens','checks_passed':checked,'max_scaled_reference_difference':max_rel,'status':'PASS','notes':'Differences/tolerances are technical audit only; not a public engine comparison. Model accuracy versus plant observations not established.'}
 if write:(result_dir/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print('HIGH PRECISION PASS',checked,'checks with',mp.mp.dps,'decimal digits')
 return report
if __name__=='__main__':verify(sys.argv[1],sys.argv[2])
