#!/usr/bin/env python3
"""Independent 80-digit mpmath check of actual paceval-exported formula results.
This script is outside the C++ mathematical execution path.
"""
import csv,json,math
from pathlib import Path
import sympy as sp
import mpmath as mp
ROOT=Path(__file__).resolve().parent.parent
mp.mp.dps=80
symbols=sp.symbols('x v y w mu zeta t')
local={str(s):s for s in symbols}
local.update({'sqrt':sp.sqrt,'exp':sp.exp})
registry={r['id']:r for r in csv.DictReader((ROOT/'results'/'formula_registry.csv').open())}
compiled={}
keys=[('expression','expression_value'),('lie_expression','lie_value'),('normalized_lie_expression','normalized_lie'),('squared_lie_expression','lie_squared')]
for ident,fields in registry.items():
    compiled[ident]=[sp.lambdify(symbols,sp.sympify(fields[eq].replace('^','**'),locals=local),modules='mpmath') for eq,_ in keys]
checks=0;worst=0.0;worst_label=''
for r in csv.DictReader((ROOT/'examples'/'high_precision_reference_samples.csv').open()):
    vals=[mp.mpf(r[s]) for s in ('x','v','y','w','mu','zeta','t')]
    for (eq,actual),fn in zip(keys,compiled[r['candidate_id']]):
        expected=fn(*vals)
        observed=mp.mpf(r[actual])
        scaled=abs(observed-expected)/(1+abs(expected))
        delta=float(scaled)
        if delta>worst:worst=delta;worst_label=f"{r['candidate_id']} {eq}"
        assert math.isfinite(delta) and delta<3e-10,(r['candidate_id'],eq,delta)
        checks+=1
report={'precision_decimal_digits':80,'paceval_output_values_checked':checks,'all_checks_passed':True,
        'largest_scaled_difference':worst,'worst_case':worst_label,
        'method':'Independent SymPy parsing and 80-digit mpmath calculation from original exported formulas and held-out coordinate inputs; separate from the C++/paceval runtime'}
(ROOT/'results'/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('80-digit independent numerical checks:',checks,'worst:',worst)
