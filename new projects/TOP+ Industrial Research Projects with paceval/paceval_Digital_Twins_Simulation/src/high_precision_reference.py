#!/usr/bin/env python3
"""Independent 110-decimal-digit check of TINC sample intervals.

Uses the exact IEEE-754 inputs emitted by the C++ demonstrator. This is a
finite set of pointwise tests, not a proof of general interval rigor.
Run: python3 src/high_precision_reference.py examples/tinc_samples.csv
Requires: python3 -m pip install mpmath
"""
import csv
import sys
from pathlib import Path
import mpmath as mp
mp.mp.dps = 110
VARS = ("t1", "t2", "tamb", "power", "c1", "c2", "k12", "h1", "h2", "krad", "gain", "offset")

def reference(name, v):
    t1, t2, ta, p, c1, c2, k12, h1, h2, krad, gain, offset = (v[k] for k in VARS)
    thermal_loss = h2*(t2-ta) + krad*((t2/mp.mpf(300))**4-(ta/mp.mpf(300))**4)
    if name == 'single':
        return (p-h1*(t1-ta))/c1
    if name == 'two_rhs1':
        return (p-k12*(t1-t2)-h1*(t1-ta))/c1
    if name == 'two_rhs2':
        return (k12*(t1-t2)-thermal_loss)/c2
    raise ValueError('Unknown formula '+name)

def check(path):
    with Path(path).open(newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    assert rows, 'No validation samples'
    failures=[]
    for row in rows:
        # Convert through float first to recover the binary64 value actually
        # passed to the vendor C API. mp.mpf(float) is exact binary conversion.
        v={k:mp.mpf(float(row[k])) for k in VARS}
        true=reference(row['formula'],v)
        lo=mp.mpf(float(row['tinc_lower']))
        hi=mp.mpf(float(row['tinc_upper']))
        got=mp.mpf(float(row['paceval_result']))
        if not (lo <= true <= hi and lo <= got <= hi):
            failures.append((row['case_id'],row['formula'],str(true),str(lo),str(hi)))
    print('TINC independent reference: %d/%d enclosed (mpmath 110 decimal digits)' % (len(rows)-len(failures), len(rows)))
    for failure in failures[:5]: print('FAIL',failure)
    if failures: raise SystemExit(1)
    assert len(rows)==24, 'Expected exactly 24 test points'
    print('PASS: all 24 pointwise TINC enclosures contain independent references')

if __name__ == '__main__':
    if len(sys.argv)!=2: raise SystemExit('Usage: high_precision_reference.py path/to/tinc_samples.csv')
    check(sys.argv[1])
