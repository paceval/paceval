#!/usr/bin/env python3
"""Independent high-precision physics reference for the original-SDK WP24 experiment.

This script does not evaluate the paceval formulas. It independently formulates the
ideal-gas polytropic relations in mpmath with 80 decimal digits and validates the
full study's stored CSV status counts and rigid-vessel ideal-gas identity.
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path
import sys
import mpmath as mp
mp.mp.dps=80
folder=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'results'
write='--write' in sys.argv
M=mp.mpf

def records(path):
    with open(path,newline='',encoding='utf-8') as f:
        yield from csv.DictReader(f)

def compare(got,ref,name,scale='4e-10'):
    if abs(M(got)-ref)>M(scale)*max(M(1),abs(ref)):
        raise AssertionError(f'{name}: {got} != high precision {mp.nstr(ref,25)}')
    return float(abs(M(got)-ref))

src={int(r['id']):r for r in records(folder/'synthetic_compressor_scenarios.csv')}
assert len(src)>=100
checks=0
maximum=0.
for r in records(folder/'stage_trace_samples.csv'):
    orig=src[int(r['id'])]
    ver=int(r['version']);pin=M(r['pin_bar']);pout=M(r['pout_bar']);tin=M(r['tin_K']);eta=M(orig['eta_poly']);gamma=M(orig['gamma']);cp=M(orig['cp_JkgK']);mdot=M(orig['mdot_kgs']);cool=M(orig['cooltemp_K']);eff=M(orig['intercooler_effectiveness'])
    ratio=pout/pin
    ee=eta if ver==1 else eta-M('0.027')*(ratio-M('2.5'))**2/(1+(ratio-M('2.5'))**2)-M('0.00016')*(tin-M(300))
    aa=(gamma-1)/(gamma*ee)
    tout=tin*mp.power(ratio,aa)
    nextcool=cool+(1-eff)*(tout-cool)
    power=mdot*cp*(tout-tin)/1000
    cooling=mdot*cp*(tout-nextcool)/1000
    de=M(0) if ver==1 else -M('.027')*2*(ratio-M('2.5'))/(pin*(1+(ratio-M('2.5'))**2)**2)
    dp=tout*(aa/pout-mp.log(ratio)*(gamma-1)/(gamma*ee**2)*de)
    deta=-tout*mp.log(ratio)*(gamma-1)/(gamma*ee**2)
    for key,ref in [('eta_effective',ee),('tout_K',tout),('intercooled_K',nextcool),('power_kW',power),('cooling_kW',cooling),('dT_dpout_Kbar',dp),('dT_detaeff_K',deta)]:
        maximum=max(maximum,compare(r[key],ref,key));checks+=1
status=Counter()
for r in records(folder/'compression_scenarios.csv'):
    status[(r['version'],r['status'])]+=1
    if r['status'] not in ('ACCEPT','REVIEW','REJECT'):raise AssertionError('Unrecognized status')
    if r['status']=='ACCEPT' and (M(r['minimum_stage_temperature_margin_K'])<18 or M(r['minimum_cooler_margin_kW'])<9):raise AssertionError('Accept too close to threshold')
    if r['status']=='REVIEW' and (M(r['minimum_stage_temperature_margin_K'])<0 or M(r['minimum_cooler_margin_kW'])<0):raise AssertionError('Invalid review state')
assert sum(status.values())==len(src)*2
manifest=json.loads((folder/'execution_evidence.json').read_text())
for v in ('1','2'):
    for s in ('ACCEPT','REVIEW','REJECT'):
        assert status[(v,s)]==manifest[f'v{v}_status'][s]
identities=0
for r in records(folder/'storage_profiles.csv'):
    mass=M(r['mass_kg']);temperature=M(r['tank_T_K']);pressure=M(r['pressure_bar'])
    predicted=mass*M(4124)*temperature/(M('7.5')*M(100000))
    maximum=max(maximum,compare(pressure,predicted,'ideal gas vessel',scale='4e-10'));identities+=1
assert identities==manifest['storage_step_evaluations']
out={'high_precision_decimal_digits':80,'independent_high_precision_checks':checks,'storage_ideal_gas_identity_checks':identities,'full_csv_status_rows':sum(status.values()),'maximum_absolute_difference_in_tested_fields':maximum,'status':'PASS'}
if write:
    (folder/'independent_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS independent 80-digit checks=',checks,'storage identities=',identities,'scenario status rows=',sum(status.values()))
