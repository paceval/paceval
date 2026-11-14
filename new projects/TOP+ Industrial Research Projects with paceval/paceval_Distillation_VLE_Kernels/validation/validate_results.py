#!/usr/bin/env python3
"""Independent reference: separate Python expressions and 80-digit mpmath arithmetic.

The program never parses the exported paceval formula strings as its oracle.
"""
import csv, json, math, sys
from pathlib import Path
import mpmath as mp
import numpy as np
from scipy.optimize import brentq
mp.mp.dps=80
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'results'
P=mp.mpf

def py_psat_a(t):return P(10)**(P('4.72583')-P('1660.652')/(t-P('1.461')))
def py_psat_b(t):return P(10)**(P('4.07827')-P('1343.943')/(t-P('53.773')))
def py_vle(v,x,t):
  if v==1:return P('2.6')*x/(1+P('1.6')*x)
  A=x*mp.exp(P('.18')*(1-x)**2)*py_psat_a(t)
  B=(1-x)*mp.exp(P('.18')*x*x)*py_psat_b(t)
  return A/(A+B)
def py_alpha(v,x,t):
  if v==1:return P('2.6')
  return mp.exp(P('.18')*(1-2*x))*py_psat_a(t)/py_psat_b(t)
def py_bubble(x,t):return x*mp.exp(P('.18')*(1-x)**2)*py_psat_a(t)+(1-x)*mp.exp(P('.18')*x*x)*py_psat_b(t)
def approx(got,ref,label,tol=2e-8):
  assert math.isfinite(float(got)),label+' nonfinite'
  assert abs(float(got)-float(ref)) <= tol*max(1,abs(float(ref))),f'{label} {got} != {ref}'

rows=list(csv.DictReader(open(R/'vle_samples.csv')))
assert len(rows)>=64
checks=0
for r in rows[::max(1,len(rows)//512)]:
  v=int(r['version']);x=P(r['x']);t=P(r['T_K']);y=py_vle(v,x,t);alpha=py_alpha(v,x,t)
  approx(r['y'],y,'80-digit vapor fraction');checks+=1
  approx(r['alpha_eff'],alpha,'80-digit effective alpha');checks+=1
  approx(r['bubble_pressure_bar'],py_bubble(x,t),'80-digit bubble pressure');checks+=1
  if v==1:dy=P('2.6')/(1+P('1.6')*x)**2
  else:dy=y*(1-y)*(1/(x*(1-x))-P('.36'))
  approx(r['dy_dx'],dy,'80-digit dY/dX');checks+=1
  if v==2:
    dtemp=y*(1-y)*mp.log(10)*(P('1660.652')/(t-P('1.461'))**2-P('1343.943')/(t-P('53.773'))**2)
    approx(r['dy_dT'],dtemp,'80-digit dY/dT');checks+=1
  assert int(round(float(r['vle_quality_indicator']))) in (0,1)

# Core column material conservation and process heat proxy on every archived configuration.
cc=list(csv.DictReader(open(R/'column_configurations.csv')))
assert len(cc)>=32
for c in cc:
  F=100.0;D=float(c['distillate_kmol_h']);B=float(c['bottoms_kmol_h']);V=float(c['vapor_kmol_h']);xd=float(c['xd']);xb=float(c['xb']);zf=float(c['zfeed'])
  assert abs(D+B-F)<1e-8
  assert abs(D*xd+B*xb-F*zf)<1e-8
  assert abs(V-D*(float(c['reflux'])+1))<1e-8
  assert abs(float(c['reboiler_kW'])-V*31/3.6)<1e-8

# Independent rigorous bubble-point root and temperature validity, x grid subset.
curve=list(csv.DictReader(open(R/'isobaric_equilibrium_curves.csv')))
assert len(curve)>100
for rr in curve[::max(1,len(curve)//60)]:
  x=float(rr['x']);t=float(rr['bubble_temperature_K']);press=float(rr['bubble_pressure_bar']);v=int(rr['version'])
  exact=brentq(lambda T:float(py_bubble(P(str(x)),P(str(T))))-0.6,333.4,373.5,xtol=3e-12)
  assert abs(exact-t)<5e-7
  approx(rr['vapor_y'],py_vle(v,P(str(x)),P(str(t))),'isobaric VLE',1e-8)
  assert abs(press-0.6)<5e-7

# Forward/backward saturation equilibrium x->y monotonicity in each model.
for v in (1,2):
  data=sorted((float(r['x']),float(r['vapor_y'])) for r in curve if int(r['version'])==v)
  assert all(a[0]<b[0] and a[1]<b[1] for a,b in zip(data,data[1:]))

report={'high_precision_decimal_digits':80,'independent_high_precision_values_checked':checks,
        'column_configurations_checked':len(cc),'isobaric_curve_points_checked':len(curve),
        'note':'These are separate independent Python reference formulas, not a substitute for validating real thermodynamic interaction parameters.',
        'status':'PASS'}
(R/'independent_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT VALIDATION PASS',json.dumps(report))
