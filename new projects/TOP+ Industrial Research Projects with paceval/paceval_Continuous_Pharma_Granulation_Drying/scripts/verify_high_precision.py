#!/usr/bin/env python3
"""Independent multiprecision verification of ORIGINAL CSV inputs against saved paceval values.
Does not read or interpret the paceval mathematical formula manifest.
All differences and tolerances belong to technical audit files, not public README/PDF.
"""
from pathlib import Path
import csv,sys,json,hashlib
import mpmath as mp
mp.mp.dps=85
project=Path(__file__).resolve().parents[1]
result=Path(sys.argv[1]) if len(sys.argv)>1 else project/'results'
source=Path(sys.argv[2]) if len(sys.argv)>2 else project/'input/cases.csv'
with source.open(newline='',encoding='utf8') as f: ins={r['case_id']:r for r in csv.DictReader(f)}
D=lambda s:mp.mpf(str(s))
nchecks=0;nfail=0;maxerr=mp.mpf(0);issues=[];near_lim=0
for row in csv.DictReader((result/'screening.csv').open(newline='',encoding='utf8')):
 a=ins[row['case_id']];v=int(row['model'][-1]);p={k:D(z) for k,z in a.items() if k not in ('case_id','scenario')}
 s=p['solid'];wl=p['water'];T=p['Tair'];Ti=p['Tin'];Tr=p['Tref'];tm=p['time'];RH=p['RH'];q=wl/s
 moisture_start=p['baseMoist']+q
 humidity_equilibrium=p['eqBase']+p['eqRH']*RH*mp.exp(-p['eqTC']*(T-Tr))
 kinetic_rate=p['kref']*mp.exp(-p['Ea']/mp.mpf('8.31446261815324')*(1/T-1/Tr))
 if v==1:
  survival=mp.exp(-kinetic_rate*tm)
  speed_weight=survival
 else:
  alpha=p['fastFraction'];spread=p['spread']
  fast_survive=mp.exp(-kinetic_rate*(1+spread)*tm)
  slow_survive=mp.exp(-kinetic_rate*(1-spread)*tm)
  survival=alpha*fast_survive+(1-alpha)*slow_survive
  speed_weight=alpha*(1+spread)*fast_survive+(1-alpha)*(1-spread)*slow_survive
 solid_moisture=humidity_equilibrium+(moisture_start-humidity_equilibrium)*survival
 wetmoisture=solid_moisture/(1+solid_moisture)
 def moisture_at(t):
  if v==1:remain=mp.exp(-kinetic_rate*t)
  else:remain=p['fastFraction']*mp.exp(-kinetic_rate*(1+p['spread'])*t)+(1-p['fastFraction'])*mp.exp(-kinetic_rate*(1-p['spread'])*t)
  m=humidity_equilibrium+(moisture_start-humidity_equilibrium)*remain
  return m/(1+m)
 short=moisture_at(tm*(1-p['rtdWidth']))
 long=moisture_at(tm*(1+p['rtdWidth']))
 product_temperature=Ti+(T-Ti)*(1-mp.exp(-p['hcoef']*tm))-p['latentCool']*(moisture_start-solid_moisture)
 removed_flow=s*(moisture_start-solid_moisture)
 heat_indicator=removed_flow*mp.mpf('2257')/mp.mpf('3600')
 moisture_rate=-(moisture_start-humidity_equilibrium)*kinetic_rate*speed_weight
 margin_overdry=long-p['Mmin'];margin_underdry=p['Mmax']-short
 temp_margin=p['Tmax']-product_temperature
 wetting_margin=min(q-mp.mpf('.08'),mp.mpf('.28')-q)
 pat_residual=p['sensor']-wetmoisture
 pat_margin=p['sensorTol']-abs(pat_residual)
 decision=int(all(z>=0 for z in (margin_overdry,margin_underdry,temp_margin,wetting_margin,pat_margin)))
 score=100*abs(wetmoisture-p['target'])+200*max(mp.mpf(0),-margin_overdry)+200*max(mp.mpf(0),-margin_underdry)+max(mp.mpf(0),-temp_margin)/20+10*max(mp.mpf(0),-pat_margin)
 dkdT=kinetic_rate*p['Ea']/(mp.mpf('8.31446261815324')*T*T)
 dEqdT=-p['eqTC']*(humidity_equilibrium-p['eqBase'])
 temperature_derivative=dEqdT*(1-survival)-(moisture_start-humidity_equilibrium)*tm*dkdT*speed_weight
 ref={
 'moisture_in_dry':moisture_start,'moisture_eq_dry':humidity_equilibrium,'k_s':kinetic_rate,
 'exit_dry':solid_moisture,'exit_wet':wetmoisture,'early_wet':short,'late_wet':long,
 'granule_temp_K':product_temperature,'evaporation_kg_h':removed_flow,'latent_duty_kW':heat_indicator,
 'drying_rate_dry_s':moisture_rate,'margin_too_wet':margin_overdry,'margin_too_dry':margin_underdry,
 'margin_temp_K':temp_margin,'margin_wetting':wetting_margin,'margin_sensor':pat_margin,
 'sensor_residual':pat_residual,'quality_guard':mp.mpf(decision),'deviation_target':abs(wetmoisture-p['target']),
 'process_score':score,'sensitivity_time':moisture_rate,'sensitivity_air_temp':temperature_derivative,
 'exit_wet_flow_kg_h':s*(1+solid_moisture),'mass_balance_residual':mp.mpf(0)
 }
 for key,target in ref.items():
  nchecks+=1
  err=abs(D(row[key])-target)
  maxerr=max(maxerr,err)
  tolerance=mp.mpf('2e-7')+mp.mpf('1e-8')*abs(target)
  if key=='quality_guard':tolerance=mp.mpf('1e-10')
  if err>tolerance:
   nfail+=1
   if len(issues)<25:issues.append({'case':row['case_id'],'version':v,'quantity':key,'abs_diff':mp.nstr(err,12),'threshold':mp.nstr(tolerance,12)})
  if min(abs(margin_overdry),abs(margin_underdry),abs(pat_margin))<mp.mpf('1e-5'):near_lim+=1
summary={'status':'PASS' if nfail==0 else 'FAIL','decimal_precision':85,'checks':nchecks,'failed_checks':nfail,'illustrative_boundary_near_cases':near_lim,'largest_abs_numeric_difference_in_mixed_units':float(maxerr),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'failures':issues,'reference':'Independent mpmath derivation from original numeric input rows; simplified physical models only'}
(result/'high_precision_audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print('HIGH PRECISION',summary['status'],nchecks,'independent checks')
if nfail:raise SystemExit(1)
