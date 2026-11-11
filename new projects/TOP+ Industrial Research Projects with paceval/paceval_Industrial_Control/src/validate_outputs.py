#!/usr/bin/env python3
"""Independent 110-digit evaluation of saved paceval real-runtime CSV results.

This script deliberately contains no calls to paceval, and does not measure
runtime. It checks the implemented formulas, closed-loop continuity, discrete
input/rate restrictions, and pointwise TINC interval inclusion (not a proof
of interval correctness for arbitrary input). Only Python and mpmath required.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
import mpmath as mp

mp.mp.dps = 110

def exact_float(s):
    # Reconstruct the EXACT input IEEE-754 float from its 17-digit CSV roundtrip.
    # mp.mpf(float) preserves the exact finite binary value, unlike mp.mpf(str).
    return mp.mpf(float(s))

def formulas(r):
    p={k:exact_float(r[k]) for k in ('x','u','uprev','target','a','b','d','c','q','ru','slew','xlim','umax','dumax')}
    x,u,v=p['x'],p['u'],p['uprev']
    nx=p['a']*x+p['b']*u+p['d']+p['c']*x**3
    return dict(next_state=nx, tracking_cost=p['q']*(nx-p['target'])**2,
                actuation_cost=p['ru']*u**2,slew_cost=p['slew']*(u-v)**2,
                state_margin=p['xlim']**2-nx**2,
                actuation_margin=p['umax']**2-u**2,
                slew_margin=p['dumax']**2-(u-v)**2,
                sensitivity=p['a']+3*p['c']*x**2,
                quadratic_state_energy=p['q']*x**2)

def check(trajectory,tinc):
    with Path(trajectory).open(newline='') as f: data=list(csv.DictReader(f))
    assert data, 'No trajectory rows'
    n=0; worst=mp.mpf(0); failures=[]
    states=defaultdict(list)
    for row in data:
        states[row['scenario']].append(row)
    scenarios=Path(trajectory).parent/'scenarios.csv'
    if not scenarios.exists():
        scenarios=Path(__file__).resolve().parent.parent/'examples'/'scenarios.csv'
    with scenarios.open(newline='') as f:
        setups={r['scenario']:r for r in csv.DictReader(f)}
    for name,rows in states.items():
        assert name in setups, f'Unknown scenario {name}'
        s=setups[name]
        previous=mp.mpf(0)
        baseline=exact_float(s['x_initial'])
        for index,row in enumerate(rows):
            p=dict(x=row['x_before'],u=row['control'],uprev=str(float(previous)),
                   target=row['target'],a=s['a'],b=s['b'],d=row['disturbance'],
                   c=s['c'],q=s['q'],ru=s['ru'],slew=s['slew'],
                   xlim=s['xlim'],umax=s['umax'],dumax=s['dumax'])
            results=formulas(p)
            assert abs(exact_float(row['target'])-exact_float(s['target']))<mp.mpf('1e-14'), 'Setpoint mismatch'
            if index==0: assert abs(exact_float(row['x_before'])-exact_float(s['x_initial']))<mp.mpf('1e-12'), 'Wrong initial state'
            zero_exact=exact_float(s['a'])*baseline+exact_float(row['disturbance'])+exact_float(s['c'])*baseline**3
            assert abs(exact_float(row['zero_input_reference_x'])-zero_exact)<mp.mpf('2e-12'), 'Zero-input reference mismatch'
            baseline=exact_float(row['zero_input_reference_x'])
            for label,truth in results.items():
                if label=='quadratic_state_energy': continue
                csv_label={'next_state':'x_after','sensitivity':'sensitivity'}.get(label,label)
                observed=exact_float(row[csv_label]);err=abs(observed-truth)
                worst=max(worst,err);n+=1
                if err>mp.mpf('2e-12')*(1+abs(truth)):
                    failures.append((name,index,label,str(err)))
            u=exact_float(row['control'])
            assert u in tuple(mp.mpf(v) for v in (-1,-.5,0,.5,1)), 'Control outside input grid'
            assert abs(u-previous)<=exact_float(s['dumax'])+mp.mpf('1e-12'), 'Rate limit exceeded'
            assert results['state_margin']>=-mp.mpf('1e-12'), 'State envelope exceeded'
            if index+1<len(rows):
                next_before=exact_float(rows[index+1]['x_before'])
                assert abs(next_before-exact_float(row['x_after']))<mp.mpf('2e-12'), 'Broken trajectory continuity'
            previous=u
    with Path(tinc).open(newline='') as f:intervals=list(csv.DictReader(f))
    strict=0;near=0;misses=[]
    for row in intervals:
        value=formulas(row)[row['graph']]
        lo,hi=exact_float(row['tinc_lower']),exact_float(row['tinc_upper'])
        assert lo<=hi, 'Reversed interval'
        if lo<=value<=hi:strict+=1
        else:
            misses.append((row['scenario'],row['step'],row['graph'],str(value),row['tinc_lower'],row['tinc_upper']))
            if abs(value-(lo if value<lo else hi))<=mp.mpf('2e-14')*(1+abs(value)): near+=1
    print(f'PASS independent 110-digit mathematical reference: {n} values, worst absolute difference {float(worst):.3e}; mismatches {len(failures)}')
    print(f'TINC pointwise inclusion (exact binary floating-point input values): {strict}/{len(intervals)}; {len(misses)} strict misses, {near} misses within 2e-14 scale')
    for item in misses[:5]:print('  TINC strict miss:',*item)
    if failures:raise SystemExit('FAIL high-precision formula checks: '+repr(failures[:5]))
    return len(data),n,strict,len(intervals)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--trajectory',required=True);parser.add_argument('--tinc',required=True)
    a=parser.parse_args();check(a.trajectory,a.tinc)
