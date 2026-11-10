#!/usr/bin/env python3
"""Independent multiprecision check for all seven published graph outputs.

Usage:
 python3 src/validate_outputs.py examples/sensors.csv examples/evaluations.csv

This validates the *explicit synthetic mathematical functions*, not tokamak
plasma physics or the suitability of the advisory signal for control.
"""
import csv
import sys
from pathlib import Path
import mpmath as mp
mp.mp.dps = 85

def values(row):
    return {key:mp.mpf(float(val)) for key,val in row.items() if key!='sample_id'}

def reference(row):
    v=values(row)
    i,b=v['i'],v['b']
    d=v['a0']+v['a1']*i+v['a2']*b+v['a3']*i*b+v['a4']*b*b
    nonlin=v['b0']+v['b1']*mp.tanh(v['k']*i)+v['b2']*mp.exp(-v['c']*b*b)
    grad_i=v['a1']+v['a3']*b
    grad_b=v['a2']+v['a3']*i+2*v['a4']*b
    sigma=mp.sqrt(grad_i*grad_i*v['si']**2+grad_b*grad_b*v['sb']**2)
    margin=1-(i/v['ilim'])**2-(b/v['blim'])**2
    advisory=v['kp']*(v['target']-d)-v['kd']*v['di']
    return dict(zip(('diagnostic','nonlinear_surrogate','gradient_current',
                     'gradient_field','propagated_sigma','ellipse_margin',
                     'advisory_signal'),(d,nonlin,grad_i,grad_b,sigma,margin,advisory)))

def main(input_csv,output_csv):
    with Path(input_csv).open(newline='',encoding='utf8') as f:
        cases=list(csv.DictReader(f))
    with Path(output_csv).open(newline='',encoding='utf8') as f:
        observations=list(csv.DictReader(f))
    if len(cases)!=len(observations):raise SystemExit('Input/output row counts differ')
    fails=[];biggest=0.0;n=0
    for case,ob in zip(cases,observations):
        if case['sample_id']!=ob['sample_id']:raise SystemExit('Sample order differs')
        ref=reference(case)
        for name,exact in ref.items():
            got=mp.mpf(float(ob[name]))
            diff=abs(exact-got)
            biggest=max(biggest,float(diff));n+=1
            if diff>mp.mpf('2e-11')*(1+abs(exact)):
                fails.append((case['sample_id'],name,mp.nstr(diff,12)))
        flag='outside' if ref['ellipse_margin']<0 else 'inside'
        if ob['host_envelope_flag']!=flag:
            fails.append((case['sample_id'],'host_envelope_flag',flag))
    print('Independent 85-digit function audit:',n,'values;',len(fails),'failures; max absolute error',f'{biggest:.3g}')
    for f in fails[:10]:print('FAIL',*f)
    if fails:raise SystemExit(1)
    print('PASS: all seven formula outputs and the host-owned classification agree')
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: validate_outputs.py inputs.csv evaluations.csv')
    main(*sys.argv[1:])
