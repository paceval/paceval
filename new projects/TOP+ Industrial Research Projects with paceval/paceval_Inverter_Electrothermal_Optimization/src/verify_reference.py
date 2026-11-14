#!/usr/bin/env python3
"""Independent analytic thermo-electric reference. Never imports paceval or parses graphs."""
from __future__ import annotations
import argparse,csv,json,math,random,sys
from pathlib import Path
import numpy as np
import pandas as pd
import mpmath as mp

P=argparse.ArgumentParser();P.add_argument('--results',type=Path,required=True);P.add_argument('--small',action='store_true');args=P.parse_args()
root=args.results
r=pd.read_csv(root/'inverter_results.csv',low_memory=False)
assert {'scenarioId','junctionTempC','version','solverStatus','decision'}<=set(r),r.columns
assert len(r)%2==0 and set(r.version)=={1,2}
N=len(r)//2
assert r.groupby('scenarioId').size().eq(2).all()
success=r[r.solverStatus=='OK'].copy()
fail=r[r.solverStatus!='OK'].copy()

# Algebraic independent closed-form reference, including the nonlinear quadratic feedback.
def terms(c,version,typed=float):
    f=typed
    I=f(c['currentA']);V=f(c['dcVoltageV']);fs=f(c['frequencyHz']);rip=f(c['rippleA'])
    if version==1:
        A=I*I*f('.018');B=A*f('.0038');D=f('0');
        S=fs*f('.0026')*(V/f(800))*(I/f(100));G=f('0')
    else:
        A=(I*I+rip*rip/f(12))*f('.018');B=A*f('.0036');D=A*f('.0000012')
        C=fs*f('.0026')*(V/f(800))**f('1.04')*(I/f(100))**f('1.06')
        E=fs*f('.00030')*(V/f(800))*(I/f(100))
        S=C+E;G=C*f('.0009')+E*f('.0013')
    return A,B,D,S,G

def root_closed(c,version):
    p0,p1,p2,sw,sw1=terms(c,version)
    h=float(c['rthKperW']);amb=float(c['ambientC']);
    # 25 + x - ambient - h*(P0+P1*x+P2*x^2)=0, x=Tj-25.
    a=-h*p2;b=1-h*(p1+sw1);cc=25-amb-h*(p0+sw)
    if abs(a)<1e-16:
        roots=[-cc/b] if abs(b)>1e-14 else []
    else:
        disc=b*b-4*a*cc
        if disc<0:return None
        q=-.5*(b+math.copysign(math.sqrt(disc),b))
        roots=[q/a,cc/q] if abs(q)>1e-20 else [-b/(2*a)]
    eligible=[25+x for x in roots if amb-1e-8<=25+x<=250+1e-8]
    return min(eligible) if eligible else None

def calc(c,version,t):
    I=float(c['currentA']);V=float(c['dcVoltageV']);fs=float(c['frequencyHz']);rip=float(c['rippleA'])
    p0,p1,p2,s0,s1=terms(c,version)
    x=t-25;pc=p0+p1*x+p2*x*x;ps=s0+s1*x;pt=pc+ps
    dpt=p1+2*p2*x+s1;stab=1-float(c['rthKperW'])*dpt
    if version==1:dpdi=2*I*.018*(1+.0038*x)+fs*.0026*(V/800)/100
    else:
        rr=.018*(1+.0036*x+.0000012*x*x)
        dpdi=(2*I*rr+fs*(.0026*(V/800)**1.04*1.06*(I/100)**.06/100*(1+.0009*x)+
                            .00030*(V/800)/100*(1+.0013*x)))
    dpdf=ps/fs if fs>0 else (.0026*(V/800)*(I/100) if version==1 else
       .0026*(V/800)**1.04*(I/100)**1.06*(1+.0009*x)+.00030*(V/800)*(I/100)*(1+.0013*x))
    tm=float(c['junctionLimitC'])-t;lm=float(c['lossLimitW'])-pt
    score=.55*(pt/float(c['lossLimitW']))**2+.45*((t-float(c['ambientC']))/(float(c['junctionLimitC'])-float(c['ambientC'])))**2
    share=ps/max(pt,1e-12)
    guard=int(t<=float(c['junctionLimitC']) and pt<=float(c['lossLimitW']) and stab>0)
    if stab<=0 or tm< -18 or lm< -40 or score>1.70:decision='REJECT'
    elif tm>=0 and lm>=0 and score<=.88:decision='ACCEPT'
    else:decision='REVIEW'
    return dict(conductionW=pc,switchingW=ps,totalLossW=pt,tempMarginK=tm,lossMarginW=lm,
                feedbackMargin=stab,lossSensitivityWperA=dpdi,tempSensitivityKperA=float(c['rthKperW'])*dpdi/stab,
                freqSensitivityKperHz=float(c['rthKperW'])*dpdf/stab,switchingShare=share,stressScore=score,
                booleanGuard=guard,decision=decision)

maxabs=0;checked=0;counts={};bad_count=0
for version in [1,2]:
    sub=r[r.version==version]
    counts[version]=dict(status=sub.solverStatus.value_counts().to_dict(),decisions=sub.decision.value_counts().to_dict())
    for row in sub.to_dict('records'):
        ref=root_closed(row,version)
        if row['solverStatus']!='OK':
            # Solver failure is allowed only if the model domain has no steady root.
            assert ref is None,(version,row['scenarioId'],ref,row['solverStatus']);bad_count+=1;continue
        assert ref is not None,(version,row['scenarioId'])
        tj=float(row['junctionTempC']);d=abs(tj-ref);maxabs=max(maxabs,d);assert d<4e-6,(version,row['scenarioId'],'Tj',d)
        values=calc(row,version,tj)
        for k,x in values.items():
            if k=='decision':assert row[k]==x,(version,row['scenarioId'],k,row[k],x)
            else:
                z=abs(float(row[k])-x);maxabs=max(maxabs,z);assert z<max(2e-6,abs(float(x))*5e-9),(version,row['scenarioId'],k,z)
                checked+=1
assert checked>0
# Independent comparison table check.
z=pd.read_csv(root/'version_comparison.csv')
w=r[r.solverStatus=='OK'].pivot(index='scenarioId',columns='version',values=['junctionTempC','totalLossW','switchingShare'])
assert len(z)==len(w.dropna())
for key,field in [('junctionRevisionDeltaK','junctionTempC'),('lossRevisionDeltaW','totalLossW'),('switchShareRevisionDelta','switchingShare')]:
    a=w[field][2]-w[field][1]
    delta=np.abs(z.set_index('scenarioId')[key].reindex(a.index).to_numpy()-a.to_numpy())
    assert float(np.nanmax(delta))<2e-8,(key,float(np.nanmax(delta)))
# Validate the entire thermal trajectory using a physically independent Euler formula.
trajectory=pd.read_csv(root/'transient_profiles.csv')
assert len(trajectory)==5760
transchecks=0
for (v,profile,cooling),sub in trajectory.groupby(['version','profile','cooling'],sort=True):
    sub=sub.sort_values('step');assert len(sub)==480
    T=28.;energy=0.;rth=[.12,.24][int(cooling)]
    for row in sub.to_dict('records'):
        current=row['currentA'];fs=row['frequencyHz']
        c=dict(currentA=current,dcVoltageV=720.,frequencyHz=fs,ambientC=28.,rthKperW=rth,rippleA=9.)
        x=T-25;p0,p1,p2,s0,s1=terms(c,int(v));loss=p0+p1*x+p2*x*x+s0+s1*x
        T=T+.25*(loss-(T-28)/rth)/60.;energy+=.25*loss
        assert abs(T-row['junctionTempC'])<2e-7
        assert abs(loss-row['lossW'])<2e-6
        assert abs(energy-row['cumulativeLossJ'])<3e-5
        transchecks+=3
# high precision checks on independent full formula and solved thermal balances.
mp.mp.dps=80
samp=success.sample(n=min(512,len(success)),random_state=20261114)
hp=0
for c in samp.to_dict('records'):
    version=int(c['version']);t=mp.mpf(str(c['junctionTempC']));
    p0,p1,p2,s0,s1=terms(c,version,typed=lambda x:mp.mpf(str(x)))
    x=t-mp.mpf(25)
    pt=p0+p1*x+p2*x*x+s0+s1*x
    f=t-mp.mpf(str(c['ambientC']))-mp.mpf(str(c['rthKperW']))*pt
    assert abs(f)<mp.mpf('0.000003'),(version,c['scenarioId'],f)
    assert abs(pt-mp.mpf(str(c['totalLossW'])))<mp.mpf('.000003')
    hp+=2
report=dict(scenarios=N,output_rows=len(r),successes=len(success),excluded_from_domain=len(fail),
   native_scalar_checks=checked,full_trajectory_checks=transchecks,high_precision_checks_80digit=hp,
   model_counts=counts,all_reference_checks='PASS',detailed_max_abs_difference=maxabs)
(root/'independent_reference_audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS analytic full model:',checked,'scalar checks;',transchecks,'transient checks;',hp,'80-digit checks; valid',len(success))
