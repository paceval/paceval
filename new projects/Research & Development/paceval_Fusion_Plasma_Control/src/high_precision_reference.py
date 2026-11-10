#!/usr/bin/env python3
"""Independent 110-digit pointwise audit of the paceval TINC output.

Usage: python3 src/high_precision_reference.py examples/tinc_samples.csv
Requires mpmath.  The exact binary64 input values passed through the C API
are converted to MP multiprecision numbers *without decimal re-rounding*.

A set of 24 pointwise containment tests is useful diagnostic evidence, but
cannot prove rigorous interval guarantees for every possible input.
"""
import csv
import sys
from pathlib import Path
import mpmath as mp
mp.mp.dps = 110
FIELDS = "i b di si sb target a0 a1 a2 a3 a4 b0 b1 b2 k c ilim blim kp kd".split()

def expected(row):
    v = {k: mp.mpf(float(row[k])) for k in FIELDS}
    if row['formula'] == 'diagnostic':
        return v['a0'] + v['a1']*v['i'] + v['a2']*v['b'] + v['a3']*v['i']*v['b'] + v['a4']*v['b']**2
    if row['formula'] == 'ellipse_margin':
        return 1-(v['i']/v['ilim'])**2-(v['b']/v['blim'])**2
    raise ValueError('Unknown formula: ' + row['formula'])

def main(path):
    with Path(path).open(encoding='utf-8', newline='') as handle:
        records=list(csv.DictReader(handle))
    if len(records)!=24:
        raise SystemExit('Expected exactly 24 interval samples; got '+str(len(records)))
    failures=[]
    for rec in records:
        reference=expected(rec)
        lower=mp.mpf(float(rec['tinc_lower']))
        upper=mp.mpf(float(rec['tinc_upper']))
        computed=mp.mpf(float(rec['paceval_result']))
        if not (lower <= reference <= upper and lower <= computed <= upper):
            failures.append((rec['sample_id'],rec['formula'],mp.nstr(reference,26),mp.nstr(lower,26),mp.nstr(upper,26)))
    print('TINC independently checked against 110-decimal-digit arithmetic:', len(records)-len(failures),'/',len(records),'enclosed')
    for row in failures:print('NOT ENCLOSED:',*row)
    if failures:raise SystemExit(1)
    print('PASS: pointwise test suite (not a universal interval-proof)')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 src/high_precision_reference.py path/to/tinc_samples.csv')
    main(sys.argv[1])
