#!/usr/bin/env python3
"""Independent 80-digit original-paceval output oracle, using exact binary64 inputs.
Hard-coded mathematical reference, NOT evaluating the CSV graph source strings.
This does not establish global interval accuracy or physical validity.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
Q=lambda s:mp.mpf(str(s))
F=lambda s:mp.mpf(float(s))

def oracle(row):
 j,T,p,age,Ta,dt,w,target,prevj,weight,Tset,auxScale=(F(row[k]) for k in ['j','T','p','age','Ta','dt','w','target','prevj','weight','Tset','auxScale'])
 er=Q('1.229')-Q('.00085')*(T-25)+Q('.0043')*mp.log(p)
 act=Q('.105')*mp.log(1+j/Q('.17'))*mp.exp(-Q('.004')*(T-60))
 ohm=Q('.14')*j*age*(1+Q('.012')*(60-T))
 conc=Q('.032')*j/(Q('2.8')-j)*(1+Q('.25')*(1-w))
 far=Q('.985')-Q('.018')*mp.exp(-j/Q('.4'))-Q('.006')*(p/22)**2-Q('.012')*(1-w)**2
 farD=Q('.018')/Q('.4')*mp.exp(-j/Q('.4'))
 aux=auxScale*(Q('.75')+Q('.0012')*(T-Ta)**2+Q('.45')*(j/2)**2+Q('.007')*p)
 h=70*300*j*far*Q('.00201588')/(2*Q('96485.33212'))
 hd=70*300*(far+j*farD)*Q('.00201588')/(2*Q('96485.33212'))
 h2_power=h*Q('120000000')/1000
 dact=Q('.105')*mp.exp(-Q('.004')*(T-60))/(j+Q('.17'))
 dohm=Q('.14')*age*(1+Q('.012')*(60-T))
 dconc=Q('.032')*Q('2.8')/(Q('2.8')-j)**2*(1+Q('.25')*(1-w))
 daT=-Q('.004')*act
 doT=-Q('.14')*j*age*Q('.012')
 r={'reversible_voltage':er,'activation_overpotential':act,'ohmic_overpotential':ohm,'transport_overpotential':conc,'faradaic_factor':far,'stack_current':300*j,'auxiliary_power':aux,'hydrogen_rate':h,'hydrogen_rate_h':3600*h,'oxygen_rate':h*Q('.031998')/Q('.00201588')/2,'water_consumption_rate':h*Q('.01801528')/Q('.00201588'),'d_hydrogen_rate_d_j':hd,'d_faradaic_factor_d_j':farD,'current_density_lower_margin':j-Q('.2'),'current_density_upper_margin':Q('2.5')-j,'temperature_lower_margin':T-30,'temperature_upper_margin':85-T,'pressure_lower_margin':p-2,'pressure_upper_margin':22-p,'water_lower_margin':w-Q('.85'),'j_change_rate_margin':Q('.05')-(j-prevj)**2/dt**2,'d_reversible_voltage_d_T':-Q('.00085'),'d_activation_overpotential_d_T':daT,'d_ohmic_overpotential_d_T':doT,'version2_minus_version1_voltage':conc,'version2_minus_version1_power':70*300*j*conc/1000}
 for ver in [1,2]:
  suf='_v'+str(ver);V=er+act+ohm+(conc if ver==2 else 0)
  dV=dact+dohm+(dconc if ver==2 else 0)
  dVT=-Q('.00085')+daT+doT
  ps=70*300*j*V/1000;pt=ps+aux;eff=h2_power/pt
  heat=70*300*j*(V-Q('1.48'))/1000
  nt=T+dt*(heat-Q('.22')*(T-Ta)-Q('.15')*(T-Tset))/1200
  dp=70*300/1000*(V+j*dV)+auxScale*Q('.45')*j/2
  deff=Q('120000000')/1000*(hd*pt-h*dp)/pt**2
  r.update({'cell_voltage'+suf:V,'stack_voltage'+suf:70*V,'stack_power'+suf:ps,'total_system_power'+suf:pt,'chemical_lhv_power'+suf:h2_power,'system_lhv_efficiency'+suf:eff,'specific_electricity'+suf:pt/(3600*h),'lhv_power_gap'+suf:pt-h2_power,'thermoneutral_heat_proxy'+suf:heat,'next_stack_temperature'+suf:nt,'d_voltage_d_j'+suf:dV,'d_voltage_d_T'+suf:dVT,'d_stack_power_d_j'+suf:70*300/1000*(V+j*dV),'d_system_power_d_j'+suf:dp,'d_system_efficiency_d_j'+suf:deff,'target_efficiency_residual'+suf:eff-target,'efficiency_lower_margin'+suf:eff-Q('.57'),'stack_voltage_upper_margin'+suf:150-70*V,'power_upper_margin'+suf:82-pt,'production_lower_margin'+suf:3600*h-Q('.3'),'power_identity_residual'+suf:pt-ps-aux,'lhv_specific_identity_residual'+suf:eff*pt-h2_power})
  for k in range(1,11):
   # published model coefficients have nine significant decimals
   A=Q('.36')+Q('.012')*k;B=Q('.012')+Q('.003')*k;C=Q('.013')+Q('.002')*k;D=Q('.007')+Q('.002')*k;E=Q('.010')+Q('.001')*k
   r[f'composite_cost{suf}_{k:02d}']=A*(eff-target)**2+B*(pt/82)**2+C*((T-Tset)/25)**2+D*(j-prevj)**2+E*(w-1)**2+weight*(1-eff)**2
 return r

def audit(root):
 n=0;errors=[];worst=0;worstName=None;missing=set();seen=set()
 with (root/'results/executed_graph_probes.csv').open() as stream:
  for line in csv.DictReader(stream):
   val=oracle(line);id=line['graph_id'];seen.add(id)
   if id not in val:missing.add(id);continue
   got=F(line['paceval_value']);ref=val[id]
   d=float(abs(got-ref)/(1+abs(ref)))
   if d>worst:worst=d;worstName=id
   if d>2e-10:errors.append((id,line['scenario_id'],line['step'],d))
   n+=1
 if missing or errors:raise AssertionError({'missing':sorted(missing),'errors':errors[:10]})
 with (root/'results/formula_registry.csv').open() as f:
  registry={x['graph_id'] for x in csv.DictReader(f)}
 if seen!=registry:raise AssertionError('not all registered graph IDs executed in original SDK: '+str(sorted(registry-seen)))
 result={'passed':True,'precision_dps':80,'comparisons':n,'independent_formula_implementation':True,'exact_binary64_inputs':True,'all_graph_ids_executed':True,'worst_graph_id':worstName,'max_scaled_error':worst,'tolerance':2e-10,'clinical_or_industrial_certification':False}
 (root/'results/high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print('ORIGINAL paceval 80-digit independent graph oracle PASS:',n,'checks, worst_scaled=',worst)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);audit(p.parse_args().root)
