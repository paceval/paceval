#!/usr/bin/env python3
"""Independent 80 decimal digit re-evaluation of selected actual paceval exports.
No outputs are substituted: assertions compare persisted SDK CSV against mpmath.
"""
import csv, json, math
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parents[1]
def rows(path):return list(csv.DictReader((ROOT/path).open()))
def mpf(x):return mp.mpf(str(x))
def value_check(found,calc,label):
    global count, maximum
    found=mpf(found);z=abs(calc-found)/(1+abs(calc))
    maximum=max(maximum,float(z));count+=1
    if z>mp.mpf('3e-11'):raise ValueError(f'{label}: scaled diff {z}')
def independent(q,n,hs,price):
    q=mpf(q);n=mpf(n);hs=mpf(hs);pr=mpf(price)
    a=mpf('1250');ha=mpf('58');ka=mpf('2800');kb=mpf('3700')
    ke=1/(1/mp.sqrt(ka)+1/mp.sqrt(kb))**2
    pump=ha*n*n-a*q*q;sys=hs+ke*q*q
    qstar=mp.sqrt((ha*n*n-hs)/(a+ke))
    qa=q/(mp.sqrt(ka)*(1/mp.sqrt(ka)+1/mp.sqrt(kb)))
    qb=q-qa
    eta=mpf('0.78')-mpf('0.2')*((q/n-mpf('.145'))/mpf('.12'))**2
    hydro=mpf('998.2')*mpf('9.81')*q*pump/1000
    p=hydro/(eta*mpf('.94'))
    cA=mp.exp(-mpf('.012')*mpf('3.5')/qa)
    cB=mp.exp(-mpf('.012')*mpf('5.0')/qb)
    mix=(qa*cA+qb*cB)/q
    def ver(j):return p/(1+mpf('.0006')*mpf(j-10)*mp.sin(12*q/n))
    return locals()
count=0;maximum=0.0
s=rows('examples/paceval_operating_sweep.csv')
for k in range(0,len(s),29):
 r=s[k];d=independent(r['q_m3s'],r['speed_ratio'],15,r['tariff'])
 for col,v in {'head_pump_m':d['pump'],'head_system_m':d['sys'],'residual_m':d['pump']-d['sys'],'flow_operating_m3s':d['qstar'],'efficiency_base':d['eta'],'hydraulic_power_kW':d['hydro'],'electric_power_base_kW':d['p'],'branch_a_m3s':d['qa'],'branch_b_m3s':d['qb'],'quality_mix_mgL':d['mix'],'electric_power_v1_kW':d['ver'](0),'electric_power_v20_kW':d['ver'](19),'energy_kWh_per_m3':d['p']/(3600*d['q'])}.items():value_check(r[col],v,f'sweep[{k}] {col}')
surf=rows('examples/paceval_operating_surface.csv')
for k in range(0,len(surf),37):
 r=surf[k];d=independent(r['q_operating_m3s'],r['speed_ratio'],r['static_head_m'],mpf('.2'))
 for col,v in {'pump_head_m':d['pump'],'system_head_m':d['sys'],'hydraulic_residual_m':d['pump']-d['sys'],'eta_base':d['eta'],'electric_kW':d['p'],'branch_a_m3s':d['qa'],'branch_b_m3s':d['qb'],'c_out_mgL':d['mix']}.items():value_check(r[col],v,f'surface[{k}] {col}')
version=rows('examples/paceval_formula_version_profile.csv')
for r in version:
 d=independent(r['q_operating_m3s'],r['speed_ratio'],15,mpf('.21'));j=int(r['version'])-1
 for col,v in {'efficiency':d['eta']*(1+mpf('.0006')*mpf(j-10)*mp.sin(12*d['q']/d['n'])),'power_kW':d['ver'](j),'cost_per_hour':mpf('.21')*d['ver'](j)}.items():value_check(r[col],v,f'version[{j}] {col}')
report={'status':'passed','precision_decimal_digits':80,'checked_values':count,'max_scaled_difference':maximum,'tested':'selected persisted real paceval outputs from sweep, operating surface and all versioned formulas','observational_data':False}
(ROOT/'results/high_precision_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
