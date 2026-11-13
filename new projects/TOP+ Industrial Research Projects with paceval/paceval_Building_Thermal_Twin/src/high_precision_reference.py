#!/usr/bin/env python3
"""Independent 80-digit mpmath validation of actual paceval CSV output.
Input decimals are parsed exactly as written. This file is not used for generating
published numerical results or paceval outputs.
"""
import argparse,csv,json
from pathlib import Path
from mpmath import mp
mp.dps=80
M=mp.mpf

def prediction(r,v,ua,c,kw,alpha):
    ti,to,g,qh,qi,w,shade=[M(r[k]) for k in ('Ti_degC','To_degC','Gsolar_W','Qhvac_W','Qinternal_W','wind_ms','shade_fraction')]
    conductance=ua+(kw*w if v==2 else M(0))
    solar=alpha*g*(1-shade if v==2 else M(1))
    net=qh+qi+solar-conductance*(ti-to)
    t=ti+M(900)/c*net
    demand=conductance*(M(21)-to)-solar-qi
    dT=-M(900)*(ti-to)/c
    return t,demand,dT

def score(r,v,i,ua,c,kw,alpha):
    t,q,dT=prediction(r,v,ua,c,kw,alpha)
    residual=t-M(r['observed_next_degC'])
    wr=M(1) if i==0 else M('0.8')+M('0.05')*i
    we=M(0) if i==0 else M('0.01')+M('0.003')*(i%5)
    wc=M(0) if i==0 else M('0.015')+M('0.005')*(i%3)
    wp=M(0) if i==0 else M('0.001')+M('0.0005')*(i%4)
    cost=wr*residual**2+we*(q/1000)**2+wc*((t-21)/2)**2+wp*((ua-215)/100)**2
    deriv=2*wr*residual*dT+2*we*q*(21-M(r['To_degC']))/M(1000000)+wc*(t-21)*dT/2+2*wp*(ua-215)/M(10000)
    return cost,deriv

def audit(root,limit=100):
    with (root/'examples/observations.csv').open() as f: inputs=list(csv.DictReader(f))
    with (root/'results/time_series.csv').open() as f: trace=list(csv.DictReader(f))
    with (root/'results/model_sweep.csv').open() as f: sweep=list(csv.DictReader(f))
    with (root/'results/score_variants.csv').open() as f: variants=list(csv.DictReader(f))
    if len(inputs)!=len(trace) or not inputs:raise AssertionError('Executed output row count mismatch')
    best=min((r for r in sweep if r['version']=='v2'),key=lambda r:M(r['mean_squared_residual_K2']))
    ua,c,kw,alpha=[M(best[k]) for k in ('UA_WperK','C_JperK','kwind_WperKmps','alpha')]
    maxscaled=M(0);cnt=0
    def compare(got,expected,label):
        nonlocal maxscaled,cnt
        scaled=abs(M(got)-expected)/(1+abs(expected))
        maxscaled=max(maxscaled,scaled);cnt+=1
        if scaled>M('3e-11'):raise AssertionError(f'{label}: scaled error {scaled}')
    for idx in range(0,len(inputs),max(1,len(inputs)//limit)):
        r,s=inputs[idx],trace[idx]
        for v in (1,2):
            t,q,_=prediction(r,v,ua,c,kw,alpha)
            compare(s[f'pred_v{v}_degC'],t,'full forecast')
            compare(s[f'residual_v{v}_K'],t-M(r['observed_next_degC']),'residual')
            compare(s[f'required_heat_v{v}_W'],q,'signed heat-demand proxy')
        t,q,dt=prediction(r,2,ua,c,kw,alpha)
        compare(s['lower_margin_v2_K'],t-M(18),'lower guard')
        compare(s['upper_margin_v2_K'],M(25)-t,'upper guard')
        _,ds=score(r,2,0,ua,c,kw,alpha)
        compare(s['ds_dUA_v2'],ds,'baseline score analytic sensitivity')
        cost02,ds02=score(r,2,1,ua,c,kw,alpha)
        compare(s['ds02_dUA_v2'],ds02,'composite score analytic sensitivity')
        compare(s['composite_score02_v2'],cost02,'composite score full value')
    for entry in variants:
        v=int(entry['model_version'][1:]);i=int(entry['function_id'][-2:])-1
        expected=sum((score(r,v,i,ua,c,kw,alpha)[0] for r in inputs),M(0))/len(inputs)
        compare(entry['mean_cost'],expected,'whole average cost '+entry['function_id'])
    summary={'status':'PASS','source':'original paceval C++ execution CSVs',
             'mpmath_decimal_digits':mp.dps,'samples':len(inputs),
             'independent_high_precision_comparisons':cnt,
             'max_scaled_error_technical_audit_only':str(maxscaled),
             'best_v2_parameters':{k:str(best[k]) for k in ('UA_WperK','C_JperK','kwind_WperKmps','alpha')},
             'reference_conditions':'one-step teacher-forced forecasting; synthetic truth generated from v2; no real-building validation'}
    (root/'results/high_precision_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--limit',type=int,default=100);a=p.parse_args();audit(a.root,a.limit)
