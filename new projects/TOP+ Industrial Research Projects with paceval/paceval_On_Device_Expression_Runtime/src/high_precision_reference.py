#!/usr/bin/env python3
"""Independent arbitrary-precision audit of published synthetic paceval results.

Compute each of five formula families with mpmath, not with paceval or C++.
The parsed input decimal strings round-trip the actual C++ double values.
No performance assertions, physical model validity, or universal TINC claims.
"""
import argparse
import csv
import json
from pathlib import Path
import mpmath as mp

mp.mp.dps = 100

def reference(family: int, offset: mp.mpf, vals):
    x, a, b, c, d = vals
    if family == 0:
        return a * mp.sin(b*x) + c*mp.exp(-(d*x)) + offset
    if family == 1:
        return a*mp.cos(b*x) + c/(1+d*x*x) + offset
    if family == 2:
        return a*x*x+b*x+c*mp.exp(-(d*x))+offset
    if family == 3:
        return a*mp.tanh(b*x)+c*mp.sin(d*x)+offset
    if family == 4:
        return a*mp.log(1+b*x*x)+c*mp.sqrt(1+d*x*x)+offset
    raise ValueError("unsupported family")

def as_mpf(s):
    # CSV text holds a round-trip decimal representation of a float64 value.
    # Conversion to float first models those actual binary inputs precisely.
    return mp.mpf(float(s))

def audit(directory: Path, report: Path, expect_models=None):
    catalogs = {}
    with (directory/'models.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            i=int(r['id']); family=int(r['family'])
            assert r['formula'], 'empty expression'
            # Formula has a 9-decimal literal that is passed to paceval as text.
            expression_offset = mp.mpf(r['formula'].rsplit(')+(',1)[1][:-1])
            catalogs[i]=(family, expression_offset)
    if expect_models is not None and len(catalogs)!=expect_models:
        raise AssertionError(f'expected {expect_models} models, got {len(catalogs)}')
    total=0; failed=[]; max_abs=mp.mpf('0')
    with (directory/'evaluations.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            i=int(r['model_id']); family,offset=catalogs[i]
            assert family==int(r['family'])
            vals=[as_mpf(r[k]) for k in ('x','a','b','c','d')]
            ref=reference(family,offset,vals)
            value=as_mpf(r['paceval_value'])
            err=abs(value-ref)
            max_abs=max(err,max_abs)
            if err > mp.mpf('2e-11')*(1+abs(ref)):
                failed.append((i,r['sample'],mp.nstr(err,12)))
            total+=1
    assert not failed, f'precision failures: {failed[:5]}'
    interval_n=0; enclosure_n=0; missed=[]; max_width=mp.mpf('0')
    with (directory/'tinc_samples.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            vals=[as_mpf(r[k]) for k in ('x','a','b','c','d')]
            ref=reference(0,mp.mpf('0.000100000'),vals)
            # Printed lower/upper are float64 round-trip strings. Reconstitute
            # those binary endpoints for exact containment, without epsilon.
            lo=as_mpf(r['lower']); hi=as_mpf(r['upper'])
            max_width=max(max_width,hi-lo)
            interval_n+=1
            if lo<=ref<=hi: enclosure_n+=1
            else: missed.append(int(r['sample']))
    # A missed interval is reported honestly, not silently given a tolerance.
    # The main mathematical feasibility is independently tested above.
    data={'models':len(catalogs),'precision_digits':100,'validated_evaluations':total,
          'failed_evaluations':len(failed),'max_absolute_error':mp.nstr(max_abs,15),
          'tinc_samples':interval_n,'tinc_containment_count':enclosure_n,
          'tinc_missed_samples':missed,'tinc_max_interval_width':mp.nstr(max_width,15),
          'validation_scope':'synthetic bounded formulas and inputs; x86-64 Linux runtime'}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))
    return data

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--expect-models',type=int)
    args=parser.parse_args()
    audit(args.directory,args.report or args.directory/'high_precision_validation.json',args.expect_models)
