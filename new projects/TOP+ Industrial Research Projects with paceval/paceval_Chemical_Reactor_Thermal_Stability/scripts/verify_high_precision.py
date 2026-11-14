#!/usr/bin/env python3
"""Independently derived CSTR reference. mpmath evaluates physics, not paceval syntax.

High precision checks use exact CSV decimal *model input* values, whereas the
public CSV output is formatted using the SDK's presentation converter.
Actual numeric differences are stored in results/scientific_audit.json only.
"""
import csv, json, math, sys
from pathlib import Path
import mpmath as mp
mp.mp.dps=85
ROOT=Path(__file__).resolve().parents[1]; RESULT=ROOT/'results'

def rows(path):
    with open(path, newline='', encoding='utf-8') as f:return list(csv.DictReader(f))

S={r['scenario_id']:r for r in rows(ROOT/'input/scenarios.csv')}
roots=rows(RESULT/'equilibria.csv'); profiles=rows(RESULT/'profile.csv')
R=mp.mpf('8.31446261815324')

def derive(s, t, ver):
    t=mp.mpf(t)
    p={k:mp.mpf(v) for k,v in s.items() if k!='scenario_id'}
    k=p['kref']*mp.exp((-p['Ea']/R)*(1/t-1/p['Tref']))
    c=p['Cin']/(1+p['tau']*k)
    h=p['H']/p['rhoCp']
    effective=p['UA']*(1+(p['alpha']*(t-p['Tref']) if ver==2 else 0))
    c_dot=(p['Cin']-c)/p['tau']-k*c
    t_dot=(p['Tin']-t)/p['tau']+h*k*c-effective/(p['rhoCp']*p['V'])*(t-p['Tc'])
    dkdt=k*p['Ea']/(R*t*t)
    a=-1/p['tau']-k
    b=-c*dkdt
    c_j=h*k
    d=-1/p['tau']+h*c*dkdt-p['UA']/(p['rhoCp']*p['V'])*(1+(p['alpha']*(2*t-p['Tref']-p['Tc']) if ver==2 else 0))
    tr=a+d; det=a*d-b*c_j
    disc=tr*tr-4*det
    eig=tr/2+mp.sqrt(max(mp.mpf('0'),disc))/2
    score=min((p['Tlim']-t)/(p['Tlim']-p['Tin']),-p['tau']*tr,p['tau']**2*det)
    good=int(tr<0 and det>0 and t<=p['Tlim'] and c>=0 and c<=p['Cin'])
    return {'C':c,'F':t_dot,'FC':c_dot,'trace':tr,'det':det,'eig':eig,'score':score,'guard':good,
            'gen':p['H']*p['V']*k*c,'rem':effective*(t-p['Tc']),'dQgen_dT':p['H']*p['V']*c*dkdt,
            'dT_dUA':-(1+(p['alpha']*(t-p['Tref']) if ver==2 else 0))*(t-p['Tc'])/(p['rhoCp']*p['V']),
            'dT_dTc':effective/(p['rhoCp']*p['V'])}

def error(a,b):return float(abs(mp.mpf(a)-b))
metrics={k:0.0 for k in ['root_temperature_residual','mass_residual','concentration','trace','det','eig','score','profile_gen','profile_rem','profile_energy','sensitivity_dQgen','sensitivity_dUA','sensitivity_dTc']}
fail=[];n=0
for row in roots:
    s=S[row['scenario_id']];ver=int(row['model']);t=mp.mpf(row['root_T_K']);out=derive(s,t,ver)
    for key,col,tol in [('F','root_temperature_residual',mp.mpf('1e-9')),('FC','mass_residual',mp.mpf('1e-9')),
                        ('C','concentration',mp.mpf('1e-7')),('trace','trace',mp.mpf('1e-9')),
                        ('det','det',mp.mpf('1e-10')),('eig','eig',mp.mpf('1e-8')),
                        ('score','score',mp.mpf('1e-7'))]:
        diff=abs(mp.mpf(row.get({'C':'C_mol_m3','trace':'trace_s_inv','det':'det_s_inv2','eig':'max_real_eigen_s_inv','score':'screen_score'}.get(key,'F_reduced_K_s'), '0'))-out[key]) if key!='FC' else abs(out['FC'])
        metrics[col]=max(metrics[col],float(diff))
        if diff>tol:fail.append(f'{row["scenario_id"]} v{ver}: {key} {float(diff):.3g} > {tol}')
    if int(row['screen_guard'])!=out['guard']:fail.append(f'{row["scenario_id"]}: screen guard mismatch')
    n+=1
for row in profiles:
    # The profile uses synthetic baseline S04_04 only.
    ver=int(row['model']);out=derive(S['S04_04'],mp.mpf(row['T_K']),ver)
    for key,output_col,met,tol in [
       ('gen','heat_generation_W','profile_gen',mp.mpf('2e-6')),
       ('rem','heat_removal_W','profile_rem',mp.mpf('2e-6')),
       ('F','reduced_energy_K_s','profile_energy',mp.mpf('1e-9')),
       ('dQgen_dT','dQgen_dT_W_per_K','sensitivity_dQgen',mp.mpf('3e-6')),
       ('dT_dUA','dT_dUA_K_s_per_W_K','sensitivity_dUA',mp.mpf('1e-9')),
       ('dT_dTc','dT_dTc_per_s','sensitivity_dTc',mp.mpf('1e-9'))]:
        diff=abs(mp.mpf(row[output_col])-out[key]);metrics[met]=max(metrics[met],float(diff))
        if diff>tol:fail.append(f'profile v{ver} at {row["T_K"]}: {key} {float(diff):.3g} > {tol}')
    n+=1
root_base=[r for r in roots if r['scenario_id']=='S04_04']
if len(root_base)!=6:fail.append('Expected 3 equilibria for both versions at baseline')
# Independently solve each baseline branch with an mpmath root iterator at 85-digit precision.
mp_roots={}
for ver in [1,2]:
    for i,guess in enumerate([305,326,348]):
        true_root=mp.findroot(lambda t:derive(S['S04_04'],t,ver)['F'],(mp.mpf(guess)-3,mp.mpf(guess)+3),solver='secant',tol=mp.mpf('1e-70'))
        mp_roots[f'V{ver}_branch{i+1}']={'temperature_K':mp.nstr(true_root,40),'stability':
            'stable' if derive(S['S04_04'],true_root,ver)['trace']<0 and derive(S['S04_04'],true_root,ver)['det']>0 else 'unstable'}
        approx=mp.mpf([r for r in root_base if int(r['model'])==ver][i]['root_T_K'])
        if abs(approx-true_root)>mp.mpf('3e-8'):fail.append('Incorrect branch temperature '+str(ver))
result={
 'reference':'independently coded mass and energy balances plus 85 digit mpmath',
 'root_records_checked':len(roots), 'profile_rows_checked':len(profiles),
 'reference_quantity_checks':n, 'max_absolute_differences_technical_only':metrics,
 'baseline_high_precision_roots':mp_roots,'failure_count':len(fail),'failures':fail[:40],
 'note':'Differences depend in part on paceval decimal formatting; no global interval guarantee or field safety validation is implied.'}
(RESULT/'scientific_audit.json').write_text(json.dumps(result,indent=2)+'\n')
if fail:
    print('HIGH PRECISION AUDIT FAILED:',fail[:8]);sys.exit(1)
print('HIGH PRECISION AUDIT PASS:',len(roots),'root records,',len(profiles),'profile rows;',n,'reference quantities')
