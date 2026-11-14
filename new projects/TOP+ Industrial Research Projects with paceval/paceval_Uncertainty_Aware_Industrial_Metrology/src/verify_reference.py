#!/usr/bin/env python3
"""Independent 80-digit metrology audit, CSV schema checks and decision checks.
This does not call paceval, re-evaluate its expression strings, or borrow a native C++ result.
"""
import csv, json, math, sys
from collections import Counter
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
out=Path(sys.argv[1]); small='--small' in sys.argv
with (out/'execution_evidence.json').open() as f: evidence=json.load(f)
expected=evidence['calibration_revisions']*evidence['covariance_cases']*evidence['samples_per_scenario']*2
assert evidence['model_point_rows']==expected
assert evidence['unique_measurement_inputs']*2==expected
assert evidence['unique_graphs_executed']==42
assert evidence['native_cpp_reference_checks']==21*expected
with (out/'scenario_summary.csv').open() as f:summaries=list(csv.DictReader(f))
assert len(summaries)==evidence['calibration_revisions']*evidence['covariance_cases']*2
counts=Counter()
for a in summaries:
 n=int(a['samples']); ac=int(a['accepted']);review=int(a['review']);reject=int(a['rejected'])
 assert n==evidence['samples_per_scenario'] and ac+review+reject==n
 counts['ACCEPT']+=ac;counts['REVIEW']+=review;counts['REJECT']+=reject
assert all(counts[x]>0 for x in ['ACCEPT','REVIEW','REJECT']), counts
with (out/'audit_samples.csv').open() as f:audits=list(csv.DictReader(f))
assert len(audits)>=len(summaries)
if not small: assert len(audits)>=2000
checks=0
for d in audits:
 m=lambda name:mp.mpf(d[name]); v=int(d['model_version'])
 x,temp,ux,ut,rho=m('x'),m('temp_C'),m('ux'),m('ut_C'),m('rho')
 a0,a1,a2,b=m('a0'),m('a1'),m('a2'),m('b')
 ucal,ures,target,tol,k=m('ucal'),m('ures'),m('target_mm'),m('tol_mm'),m('k')
 sx=a1+2*a2*x
 base=a0+a1*x+a2*x*x+b*(temp-20)
 var0=(sx*ux)**2+(b*ut)**2+2*sx*b*rho*ux*ut+ucal**2+ures**2
 bias= a2*ux**2 if v==2 else mp.mpf('0')
 var=var0+2*a2**2*ux**4 if v==2 else var0
 y=base+bias
 assert var>0
 u=mp.sqrt(var);U=k*u
 am=tol-abs(y-target)-U; rm=abs(y-target)-tol-U
 ac=1 if am>=0 else 0; rj=1 if rm>=0 else 0
 quality=mp.mpf('.55')*((y-target)/tol)**2+mp.mpf('.30')*(U/tol)**2+mp.mpf('.15')*abs(rho)
 dudx=(4*a2*sx*ux**2+4*a2*b*rho*ux*ut)/(2*u)
 expected_fields={'y_mm':y,'sensitivity_x':sx,'variance_mm2':var,'u_mm':u,'U_mm':U,
   'acceptance_margin_mm':am,'rejection_margin_mm':rm,'accept_indicator':ac,
   'reject_indicator':rj,'decision_code':ac-rj,'quality_score':quality,'uncertainty_sensitivity_x':dudx}
 for name,value in expected_fields.items():
  got=m(name)
  assert abs(got-value) <= mp.mpf('2e-10')+mp.mpf('2e-10')*abs(value), (d['revision'], d['covariance_case'],name,str(got),str(value))
  checks+=1
assert all(float(a['mean_u_mm'])>0 for a in summaries)
report={'checks':checks,'precision_digits':80,'audit_rows':len(audits),'model_rows':expected,
        'independent_cpp_reference_checks':evidence['native_cpp_reference_checks'],
        'decision_counts':dict(counts),'validation':'passed','dataset':'synthetic'}
(out/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT_METROLOGY_REFERENCE_PASS',json.dumps(report))
