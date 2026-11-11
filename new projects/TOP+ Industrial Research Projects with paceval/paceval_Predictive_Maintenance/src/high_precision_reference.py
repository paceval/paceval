#!/usr/bin/env python3
"""Independent 90-decimal-digit audit for the published C++/paceval study.

Reconstructs each documented 50-model scoring formula in mpmath, not via
paceval or a C++ reference binary. TINC containment is checked only at the
24 reported sample points, not claimed globally.
"""
import argparse
import csv
import json
from pathlib import Path
import mpmath as mp
mp.mp.dps=90


def expected(model, R, K, T):
    m=model
    a=mp.mpf('0.35')+mp.mpf('0.045')*(m%11)
    b=mp.mpf('0.18')+mp.mpf('0.05')*(m%7)
    c=mp.mpf('0.12')+mp.mpf('0.04')*(m%9)
    d=mp.mpf('-1.4')+mp.mpf('0.065')*(m%13)
    z=a*R+b*K+c*T+d
    if m%4==1:z+=mp.mpf('0.035')*R*K
    if m%4==2:z+=mp.mpf('0.03')*R*R
    if m%4==3:z+=mp.mpf('0.045')*mp.tanh(K)
    return 1/(1+mp.exp(-z))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--scores',default='../examples/evaluation.csv')
    ap.add_argument('--tinc',default='../examples/tinc_samples.csv')
    ap.add_argument('--output',default='../examples/high_precision_validation.json')
    args=ap.parse_args()
    checked=0;bad=0;max_delta=mp.mpf(0)
    with open(args.scores,newline='') as f:
        for row in csv.DictReader(f):
            m=int(row['model_id'])
            rms=mp.mpf(row['rms_g']);kurt=mp.mpf(row['kurtosis']);temp=mp.mpf(row['temp_C'])
            R=rms/mp.mpf('0.3');K=(kurt-3)/3;T=(temp-60)/20
            ref=expected(m,R,K,T)
            observed=mp.mpf(row['score'])
            delta=abs(observed-ref);max_delta=max(max_delta,delta)
            if delta>mp.mpf('3e-11')*(1+abs(ref)):bad+=1
            checked+=1
    tintotal=0;tinbad=[]
    with open(args.tinc,newline='') as f:
        for row in csv.DictReader(f):
            ref=expected(0,mp.mpf(row['R']),mp.mpf(row['K']),mp.mpf(row['T']))
            if not (mp.mpf(row['lower'])<=ref<=mp.mpf(row['upper'])):
                tinbad.append((row['asset_id'],row['window_id']))
            tintotal+=1
    data={'precision_decimal_digits':mp.mp.dps,'evaluations_checked':checked,
          'tolerance_violations':bad,'max_absolute_difference':mp.nstr(max_delta,17),
          'tinc_samples_checked':tintotal,'tinc_samples_containing_reference':tintotal-len(tinbad),
          'non_enclosing_sample_identifiers':tinbad,
          'research_scope':'Independent numerical checks on a synthetic, asset-disjoint cohort; no field fault-prediction claim',
          'status':'PASS' if bad==0 else 'FAIL'}
    Path(args.output).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))
    if bad or tinbad:raise SystemExit(1)

if __name__=='__main__':main()
