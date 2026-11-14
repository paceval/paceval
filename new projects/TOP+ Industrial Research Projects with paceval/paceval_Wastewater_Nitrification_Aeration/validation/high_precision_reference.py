#!/usr/bin/env python3
"""Independent 90-digit model audit of selected real paceval MCP decimal outputs.
This is NOT the primary production engine and does not execute paceval.
"""
import csv,json,sys
from pathlib import Path
import mpmath as mp
mp.mp.dps=90
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]

def reference(row):
    # Evaluate an independently written algorithm with the input decimal strings;
    # no execution of the paceval source expression is performed here.
    v={k:mp.mpf(value) for k,value in row.items() if k!='case_id'}
    n=v['NH4'];oxy=v['DO']; x=v['Xn']; satO=oxy/(v['KO']+oxy)
    first=v['muN']*x/v['YN'] * n/(v['KN']+n) *satO
    second=v['muN']*x/v['YN']*n/(v['KN']+n+n*n/v['KI'])*satO*mp.power(v['theta'],v['Temp']-v['Tref'])
    eff1=min(first,n/v['tau']);eff2=min(second,n/v['tau'])
    o1=v['aN']*eff1+v['bX']*x;o2=v['aN']*eff2+v['bX']*x
    out1=n-eff1*v['tau'];out2=n-eff2*v['tau'];otr=v['KL']*(v['DOsat']-oxy)
    power1=o1*v['Vol']/(1000*v['alphaO2']);power2=o2*v['Vol']/(1000*v['alphaO2'])
    g1=int(out1<=v['Nlimit'] and otr>=o1 and oxy>=v['DOmin'] and power1<=v['Pmax'])
    g2=int(out2<=v['Nlimit'] and otr>=o2 and oxy>=v['DOmin'] and power2<=v['Pmax'])
    return dict(nh4out_v1=out1,nh4out_v2=out2,OUR_v2=o2,oxygen_transfer=otr,OTR=otr,oxygen_margin_v2=otr-o2,power_v2=power2,guard_v1=g1,guard_v2=g2,rate_v1=first,rate_v2=second)

def read(file):
    with file.open() as f:return list(csv.DictReader(f))

count=0
for inp,res,kind in [
    ('observed_grid_inputs.csv','mcp_grid_selected_observations.csv','grid'),
    ('observed_hourly_inputs.csv','mcp_hourly_selected_observations.csv','hourly')]:
    ins=read(R/'examples'/inp);outs=read(R/'results'/res)
    assert len(ins)==len(outs) and len(ins)>0
    for i,(s,o) in enumerate(zip(ins,outs)):
        r=reference(s)
        for key,shown in o.items():
            if key=='hour' or key in ('NH4','DO','Temp','KL'): continue
            if key not in r:raise AssertionError('Unrecognized archive quantity '+key)
            actual=mp.mpf(shown);expect=mp.mpf(r[key]);difference=abs(actual-expect)
            if difference>mp.mpf('1e-9')*max(1,abs(expect)):
                raise AssertionError(f'{kind} #{i} {key}: observed={shown}, expected={mp.nstr(expect,30)}')
            count+=1
assert count==512,(count,'Selected results')

# Independent TINC inclusion check against the EXACT IEEE-754 input values of
# the remote JSON numbers. Point checks do not prove a continuum of inputs.
tinc=json.loads((R/'results'/'tinc_point_samples.json').read_text())
checks=0
for row in tinc['cases']:
    vals=dict(NH4=row['NH4'],DO=row['DO'],Xn=70,muN=.025,YN=.2,KN=1.5,KO=.8,tau=3.2,aN=4.57,bX=.003,alphaO2=1.8,Vol=2400,Temp=row['Temp'],Tref=20,theta=1.07,KI=60,KL=row['KL'])
    v={k:mp.mpf(float(value)) for k,value in vals.items()}
    rate=(v['muN']/v['YN'])*v['Xn']*v['NH4']/(v['KN']+v['NH4']+v['NH4']**2/v['KI'])*v['DO']/(v['KO']+v['DO'])*v['theta']**(v['Temp']-v['Tref'])
    eff=min(rate,v['NH4']/v['tau'])
    expected={'nh4_out':v['NH4']-eff*v['tau'],'power':(v['aN']*eff+v['bX']*v['Xn'])*v['Vol']/(1000*v['alphaO2'])}
    for name,ref in expected.items():
        lo=mp.mpf(row[name]['lower']);hi=mp.mpf(row[name]['upper'])
        assert lo<=ref<=hi,f'TINC missing exact-binary reference {row} {name}'
        checks+=1
assert checks==6
print(f'PASS: {count} selected remote decimal reference checks, {checks} TINC printed-bound point inclusions. This is not full ASM or a global interval proof.')
