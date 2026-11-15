#!/usr/bin/env python3
"""Independent Python/Numpy and 80-digit mpmath audit for original paceval outputs.
Reconstructs every candidate from parameter columns, never evaluates SDK formula text.
"""
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path
import numpy as np
import mpmath as mp
mp.mp.dps=80
R=8.31446261815324
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'results')
def rows(file):
    with (root/file).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))
def indbasis(family,a,b,ea,ki,thermal,ca,cb,t):
    base=np.exp(-ea/R*(1/t-1/310))*np.power(ca,a)*np.power(cb,b)
    if family==0:
        return base*np.power(t/310,thermal)
    if family==1:return base/(1+ki*cb)
    if family==2:return base/(1+ki*ca)
    if family==3:return base/(1+ki*cb*cb)
    return base/(1+ki*ca*cb)
def b_mp(family,a,b,ea,ki,thermal,ca,cb,t):
    v=mp.exp(-ea/mp.mpf(str(R))*(1/t-1/mp.mpf(310)))*ca**a*cb**b
    if family==0:return v*(t/310)**thermal
    if family==1:return v/(1+ki*cb)
    if family==2:return v/(1+ki*ca)
    if family==3:return v/(1+ki*cb**2)
    return v/(1+ki*ca*cb)
raw=rows('synthetic_kinetics_observations.csv')
search=rows('candidate_search.csv')
chosen=rows('selected_models.csv')
preds=rows('holdout_predictions.csv')
profiles=rows('integrated_reaction_profiles.csv')
assert len(search)==1000 and len(chosen)==2
tr=[r for r in raw if r['split']=='TRAIN'];va=[r for r in raw if r['split']=='VALIDATION'];te=[r for r in raw if r['split']=='HOLDOUT']
checks=0
for c in search:
    fam=int(c['family']);a=float(c['order_A']);b=float(c['order_B']);ea=float(c['activation_energy_J_mol']);ki=float(c['inhibition_coefficient']);th=float(c['temperature_exponent']);
    ftrain=np.array([indbasis(fam,a,b,ea,ki,th,float(x['ca_mol_L']),float(x['cb_mol_L']),float(x['temperature_K'])) for x in tr])
    fval=np.array([indbasis(fam,a,b,ea,ki,th,float(x['ca_mol_L']),float(x['cb_mol_L']),float(x['temperature_K'])) for x in va])
    yy=np.array([float(x['observed_rate_mol_L_h']) for x in tr]);yv=np.array([float(x['observed_rate_mol_L_h']) for x in va]);
    kval=np.dot(ftrain,yy)/(np.dot(ftrain,ftrain)+1e-30)
    loss_tr=np.mean(np.square((kval*ftrain-yy)/(.2+yy)))
    loss_va=np.mean(np.square((kval*fval-yv)/(.2+yv)))
    score=loss_va+6e-6*int(c['complexity'])
    for name,value in [('fitted_kref',kval),('training_normalized_loss',loss_tr),('validation_normalized_loss',loss_va),('selection_score',score)]:
        assert math.isclose(float(c[name]),float(value),rel_tol=1e-8,abs_tol=1e-10),(c['candidate_id'],name,float(c[name]),float(value))
        checks+=1
best_v1=min((x for x in search if int(x['family'])==0),key=lambda q:float(q['selection_score']))
best_v2=min(search,key=lambda q:float(q['selection_score']))
assert int(chosen[0]['selected_id'])==int(best_v1['candidate_id'])
assert int(chosen[1]['selected_id'])==int(best_v2['candidate_id'])
checks+=2
high=0
for model in chosen:
    version=model['model'];rr=[r for r in preds if r['version']==version];assert len(rr)==len(te)
    fam=int(model['family']);a=mp.mpf(model['order_A']);b=mp.mpf(model['order_B']);ea=mp.mpf(model['activation_energy_J_mol']);ki=mp.mpf(model['inhibition_coefficient']);th=mp.mpf(model['thermal_exponent']);kf=mp.mpf(model['kref']);
    selected=[0,1,2,3,5,8,13,21,34,55,89,144,233,255] if len(rr)>=256 else list(range(min(len(rr),14)))
    selected+=list(range(0,len(rr),max(1,len(rr)//64)))
    selected=sorted(set(i for i in selected if i<len(rr)))
    for i in selected:
        row=rr[i];ca=mp.mpf(row['ca_mol_L']);cb=mp.mpf(row['cb_mol_L']);temp=mp.mpf(row['temperature_K']);o=mp.mpf(row['observed_rate'])
        ref=kf*b_mp(fam,a,b,ea,ki,th,ca,cb,temp)
        loss=((ref-o)/(mp.mpf('.2')+o))**2
        for key, expected in [('predicted_rate',ref),('normalized_loss',loss),('rate_margin',mp.mpf('1.6')-ref)]:
            diff=abs(mp.mpf(row[key])-expected)
            assert diff <= mp.mpf('6e-11')*max(1,abs(expected)),(version,i,key,str(diff))
            high+=1
    for row in rr:
        got=float(row['predicted_rate']);obs=float(row['observed_rate']);
        assert math.isfinite(got) and obs>0
        assert float(row['decision_indicator'])==(1.0 if got<=1.6 else 0.0)
        checks+=1
    group=[r for r in profiles if r['model']==version]
    assert len(group)==8*81
    for sc in range(8):
        series=[r for r in group if int(r['scenario'])==sc]
        a0=float(series[0]['ca_mol_L']);b0=float(series[0]['cb_mol_L'])
        last=-1
        for row in series:
            ta=float(row['time_h']);assert ta>last;last=ta
            ac=float(row['ca_mol_L']);bc=float(row['cb_mol_L']);pc=float(row['cp_mol_L'])
            assert abs(ac+pc-a0)<1e-8 and abs(bc+pc-b0)<1e-8
            assert ac>0 and bc>0 and pc>=0;checks+=4
assert int(chosen[1]['family'])==1 and float(chosen[1]['order_A'])==1 and float(chosen[1]['order_B'])==1 and float(chosen[1]['activation_energy_J_mol'])==36000 and float(chosen[1]['inhibition_coefficient'])==1.1
results={'independent_candidate_scoring_checks':4*len(search),'independent_decision_and_stoichiometry_checks':checks-4*len(search),'independent_high_precision_80_digit_values':high,'selected_models':[{k:x[k] for k in ['model','selected_id','family','kref','holdout_normalized_loss']} for x in chosen],'status':'PASS'}
(root/'independent_validation.json').write_text(json.dumps(results,indent=2)+'\n')
print('INDEPENDENT 80-DIGIT VALIDATION PASSED',json.dumps(results))
