#!/usr/bin/env python3
"""Independent high-precision validation of the published synthetic portfolio study.

Uses the serialized model coefficients and factor inputs, NOT paceval's formula
string or native C++ expression evaluator. Empirical VaR and ES are recomputed
from the exported P&L records. Requires mpmath (100-decimal precision).
"""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import mpmath as mp

mp.mp.dps = 100

def rows(folder, name):
    with (folder / name).open(newline='', encoding='utf8') as f:
        yield from csv.DictReader(f)

def mpdouble(value):
    # CSV contains binary64 numbers written with 17 significant decimal digits;
    # recreate that exact tested binary64 input, then promote to 100-digit mpf.
    return mp.mpf(float(value))

def high_precision_pnl(rule, shock):
    c = [mpdouble(rule[x]) for x in ('delta_eq', 'delta_ir', 'delta_fx', 'delta_cr',
                                   'gamma_eq', 'gamma_ir', 'gamma_cr',
                                   'cross_eq_fx', 'drawdown')]
    eq, ir, fx, cr = [mpdouble(shock[x]) for x in ('eq', 'ir', 'fx', 'cr')]
    y = c[0]*eq + c[1]*ir + c[2]*fx + c[3]*cr
    family = int(rule['family'])
    if family >= 1: y += mp.mpf('0.5')*c[4]*eq**2 + mp.mpf('0.5')*c[5]*ir**2
    if family >= 2: y += mp.mpf('0.5')*c[6]*cr**2 + c[7]*eq*fx
    if family >= 3: y -= c[8]*max(mp.mpf(0), -eq)
    return y

def metrics(values):
    loss = sorted(-v for v in values)
    n = len(loss)
    n_tail = math.ceil(.025*n)
    return {'var95_loss':loss[math.ceil(.95*n)-1],
            'var975_loss':loss[math.ceil(.975*n)-1],
            'es975_loss':sum(loss[-n_tail:])/n_tail,
            'worst_loss':loss[-1], 'mean_loss':sum(loss)/n}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',type=Path,default=Path(__file__).resolve().parent.parent/'examples')
    p.add_argument('--json',type=Path,default=None)
    a=p.parse_args(); F=a.folder
    rules={int(r['rule_id']):r for r in rows(F,'rules.csv')}
    shocks={int(r['scenario_id']):r for r in rows(F,'factor_shocks.csv')}
    dist_ids={k for k,s in shocks.items() if s['type']=='distribution'}
    vals=defaultdict(list); verified=0; max_abs=0.; errors=0
    # Keep this reference independent of the C++ output used by the risk engine.
    # Validate 10 samples from EACH formula version spanning the scenario grid.
    n=len(dist_ids)
    sample_indices=set([0,1,2,n//5,n//3,n//2,(2*n)//3,(4*n)//5,n-2,n-1])
    for rec in rows(F,'evaluations.csv'):
        rid=int(rec['rule_id']); sid=int(rec['scenario_id']);
        v=float(rec['paceval_pnl']); vals[rid].append(v)
        assert sid in dist_ids and math.isfinite(v),('invalid scenario',rec)
        if sid in sample_indices:
            hp=high_precision_pnl(rules[rid],shocks[sid]); delta=abs(mpdouble(rec['paceval_pnl'])-hp)
            max_abs=max(max_abs,float(delta));verified+=1
            if delta > mp.mpf('1e-8')+mp.mpf('1e-12')*abs(hp):errors+=1
        native=float(rec['native_pnl'])
        assert abs(v-native)<=1e-8*(1+abs(native)),'native discrepancy'
    assert len(vals)==len(rules),'model count mismatch'
    count=sum(map(len,vals.values()));assert count==len(rules)*n,'evaluation count mismatch'
    assert verified==len(rules)*len(sample_indices),'high precision sample count mismatch'
    for s in rows(F,'risk_metrics.csv'):
        rid=int(s['rule_id']); recalculated=metrics(vals[rid]);
        for key,v in recalculated.items():
            stored=float(s[key]); assert math.isclose(stored,v,abs_tol=1e-7,rel_tol=1e-11),(rid,key,stored,v)
    checked_stress=0
    for r in rows(F,'stress_results.csv'):
        rid=int(r['rule_id']);sid=int(r['scenario_id']);
        assert shocks[sid]['type']=='named_stress'
        hp=high_precision_pnl(rules[rid],shocks[sid]); got=mpdouble(r['paceval_pnl'])
        assert abs(got-hp)<=mp.mpf('1e-8')+mp.mpf('1e-12')*abs(hp)
        checked_stress+=1
    contained_raw=contained_host=0
    for r in rows(F,'tinc_samples.csv'):
        eq=mpdouble(r['eq']);fx=mpdouble(r['fx']);ref=eq*eq+fx*fx
        contained_raw += mpdouble(r['raw_lower'])<=ref<=mpdouble(r['raw_upper'])
        contained_host += mpdouble(r['host_lower_1ulp'])<=ref<=mpdouble(r['host_upper_1ulp'])
    assert errors==0, f'{errors} high-precision mismatches'
    assert contained_host==24,'host-expanded TINC sample did not contain reference'
    assert checked_stress==len(rules)*len(shocks.keys()-dist_ids),'stress count mismatch'
    summary={'model_versions':len(rules),'distribution_scenarios':n,
      'payoff_values_native_crosschecked':count,
      'high_precision_100_digit_pnl_samples':verified,
      'max_high_precision_sample_abs_discrepancy':max_abs,
      'empirical_risk_statistics_independently_checked':len(vals),
      'stress_values_high_precision_checked':checked_stress,
      'tinc_samples':24,'tinc_raw_point_contained':int(contained_raw),
      'tinc_host_one_ulp_contained':int(contained_host),
      'note':'Sample-wise one-ULP host expansion is NOT a universal rigorous interval guarantee.'}
    if a.json: a.json.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
