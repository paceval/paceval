#!/usr/bin/env python3
"""Check files freshly produced by the four Linux smoke executables."""
from pathlib import Path
import csv, math, json

ROOT = Path(__file__).resolve().parents[1]

def rows(file):
    with (ROOT / 'results' / file).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

summary = {}
for suffix in ('native', 'paceval'):
    a = rows(f'smoke_geometry.{suffix}.csv')
    assert len(a) == 50, (suffix, len(a))
    assert sum(float(r['w']) == -1 for r in a) == 7
    assert sum(float(r['w']) > -1 and float(r['advance']) > 0 for r in a) == 43
    key = [r for r in a if float(r['rho0']) == 10 and float(r['w']) == -.5 and float(r['D']) == 1]
    assert len(key) == 1
    k = key[0]
    advance = float(k['advance'])
    pct = float(k['relative_pct'])
    assert abs(advance - 1.0377148766929377) < 1e-8
    assert abs(pct - 20.96279244046836) < 1e-6
    summary[suffix] = {'cases': len(a), 'advance': advance, 'percent': pct}

w = rows('smoke_static.csv')
maxerr = max(abs(float(x['error'])) for x in w)
assert len(w) > 100 and maxerr < 1e-8
summary['static_wave_max_error'] = maxerr
p = rows('smoke_planar.csv')
maxplanar = max(abs(float(x['field_receiver']) - 1) for x in p)
assert len(p) >= 5 and maxplanar < 1e-10
summary['planar_constant_error'] = maxplanar
c = rows('smoke_cosmology.csv')
assert len(c) == 2
v = [float(x['geometric_advance_seconds']) for x in c]
assert abs(v[0] - 1.595174048923579) < .001
assert abs(v[1] - 45.657868896584525) < .01
summary['cosmology_N100_seconds'] = v
print(json.dumps(summary, indent=2))
print('PASS: freshly generated outputs match bounded reference expectations')
