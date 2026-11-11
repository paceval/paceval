#!/usr/bin/env python3
"""Independent high-precision and decision-state audit of example outputs.

No paceval invocation. 110 decimal digits; all binary64 input values are
converted to exact mpmath inputs. Output/error tolerances are explicit. TINC
interval containment is reported strictly, never silently repaired.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
import math
import mpmath as mp

mp.mp.dps = 110
INPUTS = ('p1','p2','x','quality','a','b','eps','threshold')

def high_precision_score(row):
    v = {k:mp.mpf(float(row[k])) for k in INPUTS}
    family = int(row['family'])
    weight = mp.mpf(float(row['weight']))
    p1,p2,x,q,a,b,eps = (v[k] for k in INPUTS[:-1])
    s = p1 / (p1 + p2 + eps) + a*mp.tanh(b*x)
    extras = (q-mp.mpf('0.5'), (p1-p2)*q,
              x*x/(1+x*x), (p1-p2)**2, mp.sin(x)*q)
    return s + weight*extras[family]

def verify(scores_csv, tinc_csv):
    failed, compared, largest_error = 0,0,mp.mpf(0)
    states = defaultdict(lambda: [False,mp.mpf(0),0])
    with open(scores_csv,newline='') as f:
        reader=csv.DictReader(f)
        for row in reader:
            expected=high_precision_score(row)
            margin=expected-mp.mpf(float(row['threshold']))
            observed=mp.mpf(float(row['score']))
            observed_margin=mp.mpf(float(row['margin']))
            for got,ref in ((observed,expected),(observed_margin,margin)):
                err=abs(got-ref);compared+=1;largest_error=max(largest_error,err)
                if err>mp.mpf('4e-12')*(1+abs(ref)):failed+=1
            key=(row['trace_id'],row['version_id'])
            has,ema,state=states[key]
            if not has:ema=observed
            else:ema=mp.mpf('0.25')*observed+mp.mpf('0.75')*ema
            t=mp.mpf(float(row['threshold']))
            if ema>=t+mp.mpf('0.025'):state=1
            elif ema<=t-mp.mpf('0.025'):state=0
            states[key]=[True,ema,state]
            # Host's binary64 EMA is checked with a rounding-aware tolerance.
            if abs(ema-mp.mpf(float(row['ema'])))>mp.mpf('4e-12') or state!=int(row['latched']):failed+=1
    checked, enclosed, misses=0,0,[]
    with open(tinc_csv,newline='') as f:
        for row in csv.DictReader(f):
            score=high_precision_score(row)
            ref=score if row['kind']=='score' else score-mp.mpf(float(row['threshold']))
            lo=mp.mpf(float(row['lower']));hi=mp.mpf(float(row['upper']))
            checked+=1
            if lo<=ref<=hi:enclosed+=1
            else:misses.append((row['trace_id'],row['step'],row['version_id'],mp.nstr(ref-lo,12),mp.nstr(ref-hi,12)))
    print(f"Independent MP audit: {compared} score/margin outputs, {failed} failures, max error {mp.nstr(largest_error,7)}")
    print(f"TINC containment vs 110-digit reference: {enclosed}/{checked}; misses: {misses[:8]}")
    return 0 if not failed and not misses and checked==24 else 1

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--scores',type=Path,required=True)
    p.add_argument('--tinc',type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(verify(a.scores,a.tinc))
