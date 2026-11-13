#!/usr/bin/env python3
"""Independent mathematical oracle for the synthetic RBF compensation family.
Does not parse the generated paceval expression, call paceval, or import model_generator.py.
Numerical audit details are deliberately separate from public performance reporting.
"""
from pathlib import Path
from collections import defaultdict
import json,csv,math,sys
from decimal import Decimal,ROUND_HALF_UP
import mpmath as mp
mp.mp.dps=80
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'results/local_sdk_results.csv').open()))
assert len(rows)==520

def fixed(v,n):
    return format(Decimal.from_float(float(v)).quantize(Decimal('1').scaleb(-n), rounding=ROUND_HALF_UP), f'.{n}f')

def params(k,v,precision=False):
    # independently specify the deterministic coefficient sequence and its exact serialized decimals
    scalar=mp.mpf if precision else float
    a=scalar(fixed(((k%11)-5)*0.00009*(1+0.06*v),9))
    mx=scalar(fixed(((k*37)%257)/256,6))
    my=scalar(fixed(((k*53)%263)/262,6))
    mz=scalar(fixed(((k*71)%269)/268,6))
    scale=scalar(fixed(0.08+0.014*(k%5),6))
    c=scalar(fixed(((k%7)-3)*0.012,6))
    return a,mx,my,mz,scale,c

def fields(row, v, prec=False):
    cast=mp.mpf if prec else float
    x,y,z,T=[cast(row[k]) for k in ('x','y','z','temp')]
    exp=mp.exp if prec else math.exp
    n=cast(20)
    b=cast('0.130000' if v==0 else '0.135000')+cast('0.002000' if v==0 else '0.002200')*(T-n)+cast('0.014000' if v==0 else '0.013000')*x-cast('0.011000' if v==0 else '0.009000')*y+cast('0.009000' if v==0 else '0.011000')*z
    dT=cast('0.002000' if v==0 else '0.002200')
    dx=cast('0.014000' if v==0 else '0.013000')
    for k in range(256):
        a,mx,my,mz,den,c=params(k,v,prec)
        gauss=exp(-((x-mx)**2+(y-my)**2+(z-mz)**2)/den)
        factor=1+c*(T-n)/n
        b+=a*gauss*factor
        dT+=a*gauss*c/n
        dx+=a*gauss*factor*(-2*(x-mx)/den)
    return b,dT,dx

audit={'independent_implementation':True,'precision_digits':80,'whole_dataset_rows':len(rows),'field_checks':0,'composite_checks':0,'high_precision_checks':0,'maximum_absolute_disagreement_internal':0,'passed':False}
# Every complete result field checked independently, not just intermediate terms.
for r in rows:
    v1=fields(r,0);v2=fields(r,1)
    for expected,key in zip(v1+v2,['correction_v1','temperature_sensitivity_v1','x_sensitivity_v1','correction_v2','temperature_sensitivity_v2','x_sensitivity_v2']):
        err=abs(float(r[key])-float(expected));audit['maximum_absolute_disagreement_internal']=max(audit['maximum_absolute_disagreement_internal'],err)
        assert err<1e-11,(r['case_id'],key,err)
        audit['field_checks']+=1
    A,B=float(v1[0]),float(v2[0]);T=float(r['temp']);tar=float(r['target']);tol=float(r['tolerance']);raw=float(r['raw'])
    composite=[B-A,B-tar,((B-tar)/tol)**2+.08*((T-25)/25)**2+.20*abs(B-A)/tol,
               1-(((B-tar)/tol)**2+.08*((T-25)/25)**2+.20*abs(B-A)/tol),
               .024-abs(B-A),.55*abs(B-tar)/tol+.25*abs(B-A)/tol+.20*abs(T-25)/25,50-T,raw-B]
    for wanted,key in zip(composite,['version_delta','target_residual','quality_score','quality_margin','version_margin','governance_score','temperature_guard','corrected_measurement']):
        err=abs(float(r[key])-wanted);audit['maximum_absolute_disagreement_internal']=max(audit['maximum_absolute_disagreement_internal'],err)
        assert err<1e-11,(r['case_id'],key,err)
        audit['composite_checks']+=1
    expected_decision='ACCEPT' if composite[3]>=0 and composite[4]>=0 and composite[6]>=0 else 'REVIEW' if composite[3]>=-0.60 and composite[6]>=0 else 'REJECT'
    assert r['decision']==expected_decision
    audit['composite_checks']+=1

# 80-digit oracle recalculates all six core values for a preregistered spread of 24 cases.
selection=[int(i*(len(rows)-1)/23) for i in range(24)]
for ix in selection:
    r=rows[ix]
    for ver,keys in [(0,['correction_v1','temperature_sensitivity_v1','x_sensitivity_v1']),(1,['correction_v2','temperature_sensitivity_v2','x_sensitivity_v2'])]:
        v=fields(r,ver,True)
        for expected,key in zip(v,keys):
            assert abs(mp.mpf(r[key])-expected)<mp.mpf('2e-11'),(ix,key)
            audit['high_precision_checks']+=1

audit['passed']=True
(root/'results/high_precision_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('PASS independent mathematical verification: fields',audit['field_checks'],'composites and decisions',audit['composite_checks'],'80-digit checks',audit['high_precision_checks'])
