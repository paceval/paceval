#!/usr/bin/env python3
"""Independent Python state integration and end-to-end mass/energy audit.
Uses independently written native Python equations; does not call paceval or
parse/evaluate the graph-registry expressions.
"""
from __future__ import annotations
import argparse,csv,math,json
from pathlib import Path
from high_precision_reference import audit as high_precision

def jprofile(profile,k):
 x=k%60
 if profile==0:return (1.25 if x<20 else 1.80 if x<36 else .60 if x<46 else 1.05)
 if profile==1:return (.45 if x<10 else .95 if x<22 else 1.55 if x<37 else 2.25 if x<49 else .73)
 return (.35 if x<12 else 1.95 if x<26 else 2.35 if x<38 else .50 if x<50 else 1.35)

def expected(profile,pressure,version,steps):
 temp=55.;prev=.85;kg=0;oxygen=0;water=0;energy=0;chemical=0;score=0;min_eta=1;maxT=-1;maxP=0;minV=10;maxV=0;low=0;series={}
 age=1.1 if profile==2 else 1.
 for k in range(steps):
  j=jprofile(profile,k);p=float(pressure);T=temp
  rev=1.229-.00085*(T-25)+.0043*math.log(p)
  act=.105*math.log(1+j/.17)*math.exp(-.004*(T-60))
  ohm=.14*j*age*(1+.012*(60-T))
  transp=.032*j/(2.8-j)*(1+.25*(1-.98))
  v=rev+act+ohm+(transp if version==2 else 0.)
  efff=.985-.018*math.exp(-j/.4)-.006*(p/22)**2-.012*(1-.98)**2
  h=70*300*j*efff*.00201588/(2*96485.33212)
  ps=70*300*j*v/1000
  aux=.75+.0012*(T-25)**2+.45*(j/2)**2+.007*p
  pw=ps+aux;eta=h*120000000/(1000*pw)
  heat=70*300*j*(v-1.48)/1000
  nextT=T+60*(heat-.22*(T-25)-.15*(T-65))/1200
  kg+=h*60;oxygen+=h*.031998/.00201588/2*60;water+=h*.01801528/.00201588*60
  energy+=pw/60;chemical+=h*120000000/1000/60
  sc=(.36+.012)*(eta-.71)**2+(.012+.003)*(pw/82)**2+(.013+.002)*((T-65)/25)**2+(.007+.002)*(j-prev)**2+(.010+.001)*(.98-1)**2+.025*(1-eta)**2
  score+=sc*60
  min_eta=min(min_eta,eta);maxT=max(maxT,nextT);maxP=max(maxP,pw);minV=min(minV,v);maxV=max(maxV,v)
  low+=eta<.57
  series[k]=(T,v,pw,h,eta,aux,ps,heat,kg)
  temp=nextT;prev=j
 return {'final_temperature_C':temp,'max_temperature_C':maxT,'total_H2_kg':kg,'total_O2_kg':oxygen,'minimum_water_kg':water,'system_electricity_kWh':energy,'hydrogen_LHV_energy_kWh':chemical,'integrated_system_efficiency_LHV':chemical/energy,'specific_electricity_kWh_kg':energy/kg,'min_instant_efficiency_LHV':min_eta,'min_cell_voltage_V':minV,'max_cell_voltage_V':maxV,'max_system_power_kW':maxP,'integral_composite_score':score,'low_efficiency_count':low},series

def check(root):
 maxerr=0;count=0;scenarioCount=0
 with (root/'results/scenario_summary.csv').open() as f:
  rows=list(csv.DictReader(f))
 assert len(rows)==18,'must cover all 18 research scenarios'
 histories={}
 for row in rows:
  k=(int(row['profile']),int(row['pressure_bar']),int(row['version']))
  output,samples=expected(k[0],k[1],k[2],int(row['steps']))
  histories[int(row['scenario_id'])]=samples
  for col,ref in output.items():
   got=float(row[col]);e=abs(got-ref)/(1+abs(ref));maxerr=max(maxerr,e);count+=1
   if e>1e-9:raise AssertionError(f'full scenario {k} field {col} error={e} expected={ref} observed={got}')
  assert float(row['algebraic_identity_max_kW'])<1e-8
  scenarioCount+=1
 with (root/'examples/trace_samples.csv').open() as f:
  for row in csv.DictReader(f):
   sid=int(row['scenario_id']);step=int(row['step']);sample=histories[sid][step]
   for col,ref in zip(['temperature_C','cell_voltage_V','system_power_kW','hydrogen_kg_s','efficiency_LHV','auxiliary_power_kW','stack_power_kW','thermoneutral_heat_proxy_kW','cumulative_H2_kg'],sample):
    got=float(row[col]);e=abs(got-ref)/(1+abs(ref));maxerr=max(maxerr,e);count+=1
    if e>1e-9:raise AssertionError(f'trace {sid} {step} {col}: {e}')
 result={'passed':True,'scenario_count':scenarioCount,'full_path_numeric_checks':count,'reference':'independent native Python equations; complete state and all aggregate values','max_scaled_error':maxerr,'tolerance':1e-9,'synthetic_only':True}
 (root/'results/independent_trajectory_audit.json').write_text(json.dumps(result,indent=2)+'\n');print('Full synthetic electrolysis trajectory audit PASS:',count,'checks across',scenarioCount,'scenarios')
 high_precision(root)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);check(p.parse_args().root)
