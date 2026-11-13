"""Independent 80-decimal-digit verification of ALL stored paceval sample rows.
Uses mpmath outside productive C++. Does not use paceval or call native C++.
"""
import csv, json, sys, math
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
F=lambda d:mp.mpf(str(d))
pi=mp.pi

def g(x,v):
    r=F('.12')+F('.75')*x+F('.09')*mp.sin(9*x)+F('.035')*mp.sin(37*x)+F('.04')*mp.exp(-((x-F('.72'))/F('.06'))**2)
    return r+(F('.002')*mp.sin(5*x)+F('.001')*x if v==2 else 0)

def high_ref(p,version,N=4096):
    x,T,d,ref,tol,ux,ut,ud,umod=[F(p[k]) for k in ['x','T','drift','reference','tolerance','u_x','u_T','u_d','u_model']]
    k=min(N-1,int(mp.floor(x*N)));lo=mp.mpf(k)/N;hi=mp.mpf(k+1)/N
    S=g(lo,version)+(g(hi,version)-g(lo,version))*N*(x-lo)
    m=(g(hi,version)-g(lo,version))*N
    G=S*(1+F('.00035')*(T-20))+F('.0005')*(T-20)+F('.000075')*mp.sin(7*x)*(T-20)+d*(F('.001')+F('.0015')*x)
    dx=m*(1+F('.00035')*(T-20))+F('.000525')*mp.cos(7*x)*(T-20)+F('.0015')*d
    dt=F('.00035')*S+F('.0005')+F('.000075')*mp.sin(7*x)
    dd=F('.001')+F('.0015')*x
    unc=mp.sqrt((dx*ux)**2+(dt*ut)**2+(dd*ud)**2+umod**2)
    residual=G-ref
    gate=tol-abs(residual)-2*unc
    reject=tol-abs(residual)+2*unc
    q=1/(1+abs(residual)/(tol+unc))
    return dict(interpolant=S,local_slope=m,corrected_value=G,sensitivity_x=dx,sensitivity_T=dt,
                sensitivity_drift=dd,combined_uncertainty=unc,residual=residual,
                acceptance_margin=gate,rejection_margin=reject,quality_fraction=q)

samples=list(csv.DictReader((R/'results/calibrated_samples.csv').open()))
source=list(csv.DictReader((R/'examples/synthetic_sensor_inputs.csv').open()))
lookup={(r['scenario'],int(r['seq'])):r for r in source}
N=int(json.loads((R/'results/sdk_run_summary.json').read_text())['intervals_per_version'])
max_abs=mp.mpf('0');max_key='';checks=0;worst={};fail=[]
for i,row in enumerate(samples):
    r=lookup[(row['scenario'],int(row['seq']))];v=int(row['version'][-1]);expected=high_ref(r,v,N)
    for key,e in expected.items():
        diff=abs(F(row[key])-e);checks+=1
        if diff>max_abs:max_abs=diff;max_key=f"row {i} {row['scenario']} {row['version']} {key}"
        worst[key]=max(worst.get(key,mp.mpf('0')),diff)
        if diff>F('5e-11'):
            fail.append(f"{max_key} discrepancy {mp.nstr(diff,8)}")
    dec='ACCEPT' if expected['acceptance_margin']>=0 else ('REJECT' if expected['rejection_margin']<0 else 'REVIEW')
    if dec!=row['decision']: fail.append(f"row {i}: decision {row['decision']} expected {dec}")
assert len(samples)==len(source)*2,(len(samples),len(source))
result={'method':'Independent 80-decimal-digit mpmath; all stored samples audited',
        'sample_rows':len(samples),'quantity_comparisons':checks,'precision_decimal_digits':80,
        'max_abs_discrepancy':float(max_abs),'worst_case':max_key,
        'per_quantity_max_abs':{k:float(v) for k,v in worst.items()},
        'decision_agreement':not bool(fail),'tolerance':5e-11,'pass':not bool(fail),
        'limitations':'Synthetic model and independent decimal arithmetic; not traceable calibration or interval proof.'}
(R/'results/independent_80digit_audit.json').write_text(json.dumps(result,indent=2)+'\n')
if fail:raise ValueError('\n'.join(fail[:5]))
print('PASS independent 80-digit audit:',len(samples),'rows,',checks,'quantity checks; maximum discrepancy',mp.nstr(max_abs,6))
