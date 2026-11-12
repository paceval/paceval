#!/usr/bin/env python3
"""Independent 100-digit audit of every recorded premium and all raw TINC endpoints.

The model implementations here are independent of the paceval expression parser
and the native C++ reference.  Every 17-digit CSV number is first re-parsed as
binary64, then converted EXACTLY to an mpmath number before arithmetic; this
models the real inputs supplied to paceval, rather than the rounded CSV text.
"""
import argparse, csv, json, math
from pathlib import Path
import mpmath as mp
mp.mp.dps = 100

def csvrows(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def exact(s):
    v = float(s)
    assert math.isfinite(v)
    return mp.mpf(v)

def reference(m, p):
    b,a,c,d,g,h,f = (exact(m[k]) for k in ('base','a','c','m','g','h','f'))
    age,claims,km,cover,excess=(exact(p[k]) for k in
      ('asset_age_years','claims','mileage_1000km','coverage_code','deductible_1000eur'))
    family=int(m['family'])
    if family==0: return b*(1+a*age)*(1+c*claims)
    if family==1: return b*(1+a*age)*(1+c*claims)*(1+d*(km-12)/12)*(1+g*(cover-1))
    if family==2: return b*(1+a*age)*(1+c*claims)*(1+g*(cover-1))*mp.exp(d*(km-12)/12)/(1+h*excess)
    return b*(1+a*age+c*claims+d*km/12+g*(cover-1)+f*age*claims)/(1+h*excess)

def audit(folder:Path):
    p=csvrows(folder/'policies.csv');models=csvrows(folder/'models.csv')
    byid={r['model_id']:r for r in models}
    assert len(byid)==len(models) and len(p)>0
    n=0;maxabs=mp.mpf(0);maxrel=mp.mpf(0)
    with open(folder/'premiums.csv',encoding='utf8',newline='') as f:
        for r in csv.DictReader(f):
            m=byid[r['model_id']];row=p[int(r['policy_id'])]
            value=reference(m,row);observed=exact(r['premium_eur']);d=abs(value-observed)
            # Float64 numerical evaluation allowance; enforced for all rows.
            assert d <= mp.mpf('1e-10')*(1+abs(value)),(r['model_id'],r['policy_id'],str(d))
            maxabs=max(maxabs,d);maxrel=max(maxrel,d/(1+abs(value)));n+=1
    assert n==len(models)*len(p)
    # Input tag is excluded from both the mathematical model and paceval's
    # variable list. This tests a single explicit counterfactual property only.
    assert len(p)%2==0
    for i in range(0,len(p),2):
        assert p[i]['pair_id']==p[i+1]['pair_id']
        assert p[i]['nonrating_tag']=='0' and p[i+1]['nonrating_tag']=='1'
        assert all(p[i][k]==p[i+1][k] for k in
          ('asset_age_years','claims','mileage_1000km','coverage_code','deductible_1000eur'))
    # Every raw TINC interval must contain the independent high precision value.
    t=csvrows(folder/'tinc_samples.csv');included=0
    for row in t:
        real=exact(row['asset_age_years'])**2+exact(row['claims'])**2
        low=exact(row['raw_min']); high=exact(row['raw_max'])
        assert low <= high
        assert low <= real <= high,('TINC interval failed', row['policy_id'], str(real), str(low), str(high))
        included+=1
    summary={"decimal_precision_digits":100,"models":len(models),"policies":len(p),
             "evaluations_checked":n,"max_abs_difference":float(maxabs),
             "max_scaled_difference":float(maxrel),"counterfactual_pairs":len(p)//2,
             "tinc_raw_intervals_checked":len(t),"tinc_reference_included":included,
             "status":"PASS","note":"Finite sample checks are not a proof of universally outward-rounded intervals or a regulatory fairness audit."}
    path=folder/'high_precision_audit.json';path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print(json.dumps(summary,indent=2));return summary
if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('folder',type=Path)
    audit(arg.parse_args().folder)
