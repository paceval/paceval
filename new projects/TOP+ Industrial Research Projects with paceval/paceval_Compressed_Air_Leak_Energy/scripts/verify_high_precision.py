#!/usr/bin/env python3
"""Independent 85-digit reference: independently written mass, thermodynamics,
energy and guard equations, not paceval formula strings or outputs used as references.
Input comes from the original CSV decimal parameters, not rounded graph CSV values.
"""
from pathlib import Path
import csv,json,sys,hashlib
import mpmath as m
m.mp.dps=85
root=Path(__file__).resolve().parents[1]
results=Path(sys.argv[1]) if len(sys.argv)>1 else root/'results'
source=Path(sys.argv[2]) if len(sys.argv)>2 else root/'input'/'cases.csv'
mp=lambda s:m.mpf(str(s))
ref={}
with source.open(newline='',encoding='utf8') as f:
 for r in csv.DictReader(f):ref[r['case_id']]=r
checks=0;max_error=0.;failures=[];low_cases=0
with (results/'screening.csv').open(newline='',encoding='utf8') as f:
 for z in csv.DictReader(f):
  a=ref[z['case_id']];P=mp(a['Pabs']);pa=mp(a['Pamb']);T=mp(a['Tin']);area=mp(a['area']);Cd=mp(a['Cd']);gamma=mp(a['gamma']);R=mp(a['Rgas']);mref=mp(a['mref']);Pref=mp(a['Pref']);exponent=mp(a['exponent']);demand=mp(a['demand']);cap=mp(a['supplyCap']);pmin=mp(a['Pmin']);kdrop=mp(a['kdrop']);eff=mp(a['eta']);cp=mp(a['cp']);hours=mp(a['hours']);price=mp(a['price']);fmax=mp(a['maxFraction']);pmax=mp(a['Pmax'])
  ratio=pa/P;crit=(2/(gamma+1))**(gamma/(gamma-1))
  if z['model']=='V1':leak=mref*((P-pa)/(Pref-pa))**exponent
  else:
   if ratio<=crit: leak=Cd*area*mp('0.000001')*P*m.sqrt(gamma/(R*T))*(2/(gamma+1))**((gamma+1)/(2*(gamma-1)))
   else:
    leak=Cd*area*mp('0.000001')*P*m.sqrt(2*gamma/(R*T*(gamma-1))*(ratio**(2/gamma)-ratio**((gamma+1)/gamma)))
    low_cases+=1
  total=demand+leak;frac=leak/total;work=cp*T*((P/pa)**((gamma-1)/gamma)-1)/eff;power=total*work/1000;lpower=leak*work/1000
  p_use=P-kdrop*total**2;mpres=p_use-pmin;mcap=cap-total;mf=fmax-frac;mph=pmax-P
  guard=int((mpres>=0) and (mcap>=0) and (mf>=0) and (mph>=0))
  c=leak*work/1000*hours*price
  values={'leak_kg_s':leak,'required_kg_s':total,'leak_fraction':frac,'work_J_kg':work,'power_kW':power,'leak_power_kW':lpower,'leak_energy_kWh':lpower*hours,'leak_cost_USD':c,'pressure_use_Pa':p_use,'margin_capacity_kg_s':mcap,'margin_leak_fraction':mf,'composite_guard':m.mpf(guard)}
  for field,want in values.items():
   got=mp(z[field]);err=abs(got-want);lim=mp('3e-10')*max(1,abs(want))+mp('3e-7')
   checks+=1;max_error=max(max_error,float(err))
   if err>lim and len(failures)<15:failures.append({'case_id':z['case_id'],'model':z['model'],'field':field,'error':str(err),'tolerance':str(lim)})
assert not failures,failures
assert low_cases>0,'Subcritical orifice branch did not receive actual production input data'
assert checks>50000,checks
meta={'status':'PASS','precision_decimal_digits':85,'independent_value_checks':checks,'subcritical_v2_rows':low_cases,'maximum_absolute_difference_in_reference_units':max_error,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reference':'Independent Python mpmath implementation; original CSV decimal values'}
(results/'high_precision_audit.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
print('HIGH PRECISION PASS',checks,'checks; subcritical V2 rows',low_cases)
