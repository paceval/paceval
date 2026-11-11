#!/usr/bin/env python3
"""Independent 110-decimal-digit audit for published mathematical samples.

This checks point evaluations of the model RHS, not certified trajectory or
universal interval bounds. The reference implementation does not call paceval.
"""
import argparse
import csv
import json
import pathlib
import mpmath as mp

mp.mp.dps = 110

def math_rhs(f, x, v, u, a, b, c, d):
    x,v,u,a,b,c,d = (mp.mpf(q) for q in (x,v,u,a,b,c,d))
    z=a*x+b*v+c*u
    if f==0:return z
    if f==1:return z+d*x*x*x
    if f==2:return z+d*x*x
    if f==3:return z+d*mp.sin(x)
    if f==4:return z+d*v*v*v
    if f==5:return z+d*x*v
    if f==6:return z+d*mp.tanh(x)
    raise ValueError(f)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('results',type=pathlib.Path)
    ap.add_argument('--output',type=pathlib.Path,default=None)
    ar=ap.parse_args()
    n=0;failed=0;max_abs=mp.mpf(0)
    with (ar.results/'audit_samples.csv').open(newline='') as fh:
        for r in csv.DictReader(fh):
            ref=math_rhs(int(r['family']),*(r[k] for k in ('x','v','u','a','b','c','d')))
            err=abs(ref-mp.mpf(r['paceval']));max_abs=max(max_abs,err);n+=1
            if err>mp.mpf('2e-9')*(1+abs(ref)):failed+=1
    contain=0;total=0;viol=[]
    with (ar.results/'tinc_samples.csv').open(newline='') as fh:
        for r in csv.DictReader(fh):
            ref=math_rhs(int(r['family']),*(r[k] for k in ('x','v','u','a','b','c','d')))
            lo,hi=mp.mpf(r['lower']),mp.mpf(r['upper']);total+=1
            if lo<=ref<=hi:contain+=1
            else: viol.append({'scenario':r['scenario'],'row':total,'reference':mp.nstr(ref,24),'lower':r['lower'],'upper':r['upper']})
    report={"precision_decimal_digits":mp.mp.dps,"rhs_samples_checked":n,"rhs_within_tolerance":n-failed,
            "maximum_absolute_rhs_error":mp.nstr(max_abs,10),"tinc_samples":total,
            "tinc_pointwise_containment":contain,"tinc_noncontainment_details":viol,
            "tolerance_policy":"abs(error) <= 2e-9 * (1+abs(reference))"}
    if ar.output:ar.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if failed or contain!=total:raise SystemExit(1)
if __name__=='__main__':main()
