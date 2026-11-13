#!/usr/bin/env python3
"""Independent 80-decimal high-precision oracle for the *actual paceval probe rows*.
Uses mpmath on exact IEEE-754 binary64 inputs. Explicit formulas are separate
from the engine's formula registry; no compilation of paceval strings here.
"""
import csv, json, argparse
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
F=lambda x:mp.mpf(float(x))

def calculate(row):
 z,p1,p2,I,T,Ta,dt,Q,age,h,Cth,target,scale=[F(row[k]) for k in ('z','p1','p2','I','T','Ta','dt','Q','age','h','Cth','target','scale')]
 o=mp.mpf('3.2')+mp.mpf('.93')*z+mp.mpf('.10')*(2/(1+mp.exp(-13*(z-mp.mpf('.5'))))-1)+mp.mpf('.00035')*(T-25)
 r0=mp.mpf('.021')*(1+mp.mpf('.7')*(1-z)**2)*mp.exp(mp.mpf('.017')*(25-T))*age
 r1=mp.mpf('.012')*(1+mp.mpf('.35')*(1-z))*mp.exp(mp.mpf('.013')*(25-T))*age
 r2=mp.mpf('.019')*(1+mp.mpf('.20')*(1-z))*mp.exp(mp.mpf('.009')*(25-T))*age
 tau1=32*(1+mp.mpf('.30')*(1-z))*mp.exp(mp.mpf('.008')*(25-T))
 tau2=175*(1+mp.mpf('.25')*(1-z))*mp.exp(mp.mpf('.006')*(25-T))
 fast=p1*mp.exp(-dt/tau1)+I*r1*(1-mp.exp(-dt/tau1))
 slow=p2*mp.exp(-dt/tau2)+I*r2*(1-mp.exp(-dt/tau2))
 dsoc=z-I*dt*age/(3600*Q)
 ans={'ocv':o,'ohmic_resistance':r0,'fast_resistance':r1,'slow_resistance':r2,'fast_tau':tau1,'slow_tau':tau2,'next_soc':dsoc,'next_fast_polarization':fast,'effective_capacity':Q/age,'d_soc_next_d_current':-dt*age/(3600*Q),
 'soc_lower_margin':z-mp.mpf('.08'),'soc_upper_margin':mp.mpf('.97')-z,'thermal_upper_margin':43-T,
 'd_ocv_d_soc':mp.mpf('.93')+2*mp.mpf('.10')*13*mp.exp(-13*(z-mp.mpf('.5')))/(1+mp.exp(-13*(z-mp.mpf('.5'))))**2,
 'd_r0_d_soc':-2*mp.mpf('.7')*mp.mpf('.021')*(1-z)*mp.exp(mp.mpf('.017')*(25-T))*age,
 'd_r0_d_temp':-mp.mpf('.017')*r0,'soc_delta':-I*dt*age/(3600*Q),
 'nominal_time_constant_ratio':tau2/tau1,'version2_minus_version1_voltage':-p2}
 for v in (1,2):
  suff=f'_v{v}';pol=p1+(p2 if v==2 else 0);slowNext=slow if v==2 else 0
  voltage=o-I*r0-pol
  heat=I**2*r0+p1**2/r1+(p2**2/r2 if v==2 else 0)
  power=I*voltage
  ans.update({
   'next_slow_polarization'+suff:slowNext,'terminal_voltage'+suff:voltage,'resistive_heat_proxy'+suff:heat,
   'next_cell_temperature'+suff:T+dt*(heat-h*(T-Ta))/Cth,
   'terminal_power'+suff:power,'open_circuit_power'+suff:I*o,'ohmic_power'+suff:I**2*r0,
   'polarization_power'+suff:I*pol,'power_identity_residual'+suff:I*o-power-I**2*r0-I*pol,
   'voltage_lower_margin'+suff:voltage-mp.mpf('2.8'),'voltage_upper_margin'+suff:mp.mpf('4.25')-voltage,
   'voltage_target_residual'+suff:voltage-target,'voltage_target_squared'+suff:(voltage-target)**2,
   'd_voltage_d_current'+suff:-r0,
   'd_voltage_d_soc'+suff:ans['d_ocv_d_soc']-I*ans['d_r0_d_soc'],
   'loss_voltage_fraction'+suff:(o-voltage)/o,'next_fast_residual'+suff:fast-p1,'next_slow_residual'+suff:slowNext-p2,
  })
  for j in range(1,11):
   # Model's documented decimal coefficients are exact mathematical constants.
   a=mp.mpf(str(round(.30+.02*j,9)));b=mp.mpf(str(round(.025+.008*j,9)));c=mp.mpf(str(round(.010+.004*j,9)));d=mp.mpf(str(round(.012+.002*j,9)));e=mp.mpf(str(round(.006+.002*j,9)))
   ans[f'composite_cost{suff}_{j:02d}']=a*(voltage-target)**2+b*(I/mp.mpf('3.2'))**2+c*((T-25)/15)**2+d*(r0/mp.mpf('.025'))**2+e*((z-mp.mpf('.65'))/mp.mpf('.35'))**2
 return ans

def check(root:Path):
 p=root/'results/executed_graph_probes.csv';n=0;missing=set();maxscale=0.;bad=[];worst=None
 with p.open() as f:
  for row in csv.DictReader(f):
   ans=calculate(row);key=row['graph_id'];
   if key not in ans:missing.add(key);continue
   # Float result compared to 80-digit oracle. Result in file is exact binary64.
   val=F(row['paceval_value']);oracle=ans[key]
   scaled=float(abs(val-oracle)/(1+abs(oracle)))
   if scaled>maxscale:maxscale=scaled;worst=key
   if scaled>2e-10:bad.append((key,row['scenario_id'],row['step'],scaled))
   n+=1
 if bad or missing:raise AssertionError(f'High precision audit bad {bad[:8]} missing {sorted(missing)}')
 out={'reference':'mpmath 80 decimal places (input floats reconstructed exactly)','comparisons':n,'max_scaled_error':maxscale,'largest_error_graph':worst,'all_registered_graphs_checked':not missing,'passed':True,'tolerance':2e-10}
 (root/'results/high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
 print('80-digit high-precision ORIGINAL paceval audit PASS:',n,'values; maximum scaled error',maxscale)
 return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);b=a.parse_args();check(b.root)
