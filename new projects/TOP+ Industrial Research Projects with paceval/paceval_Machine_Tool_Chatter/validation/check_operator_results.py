#!/usr/bin/env python3
"""Verify archived operator outputs against independent integer/Boolean semantics."""
from pathlib import Path
import json,sys
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
data=json.loads((R/'results'/'operator_selftest_observed.json').read_text())
a=data['observed']; expected={'negative_remainder':[-1]*3,'negative_modulo':[9]*3,'minimum':[4]*3,'maximum':[5]*3,'logical_and':[1,1,0],'not_or':[0,1,1],'logical_xor':[1,0,1]}
assert all(a[k]==v for k,v in expected.items())
print('Remote operator semantics: PASS, 21 graph-point results')
