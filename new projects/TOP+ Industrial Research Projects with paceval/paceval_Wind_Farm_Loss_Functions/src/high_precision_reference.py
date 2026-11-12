#!/usr/bin/env python3
"""Independent 110-digit audit for *binary* C++ inputs and raw paceval endpoints.

This verifies mathematical expressions, not farm-physics model validity.
No call into paceval is made. The native comparison column is diagnostic only.
"""
import argparse
import csv
import json
from pathlib import Path
from mpmath import mp

mp.dps = 110

def x(s):
    # Literal JSON-style decimal CSV encodes IEEE-754 doubles to 17 digits;
    # reconstruct the actually passed binary double, not a rounded display literal.
    return mp.mpf(float(s))

def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def run(folder):
    folder = Path(folder)
    assert (folder / 'models.csv').exists(), 'models.csv is missing'
    audits = load(folder / 'audit_samples.csv')
    worst_abs = mp.mpf('0'); failures = []
    count = 0
    for row in audits:
        if row['kind'] == 'wake':
            dx, dy, ct, k = [x(row[s]) for s in ('dx_m', 'dy_m', 'ct', 'wake_k')]
            D = mp.mpf(140); radius = mp.mpf(70)
            val = (1-mp.sqrt(1-ct))*(D/(D+2*k*dx))**2 * mp.exp(-mp.mpf('0.5')*(dy/(radius+k*dx))**2)
        elif row['kind'] == 'power':
            rho, area, cp, v = [x(row[s]) for s in ('rho', 'area_m2', 'cp', 'v_mps')]
            val = mp.mpf('0.5')*rho*area*cp*v**3 / 1000000
        else:
            failures.append('unknown formula class'); continue
        measured = x(row['paceval_value'])
        error = abs(measured-val)
        worst_abs = max(worst_abs, error)
        if error > mp.mpf('5e-11')*(1+abs(val)):
            failures.append(f"audit {count} |delta|={mp.nstr(error, 12)}")
        count += 1
    tinc = load(folder / 'tinc_samples.csv')
    enclosed = 0
    for row in tinc:
        cp, v = x(row['cp']), x(row['v_mps'])
        val = cp * v**3
        lower, upper = x(row['raw_lower']), x(row['raw_upper'])
        if lower <= val <= upper:
            enclosed += 1
        else:
            failures.append(f"TINC sample {row['sample_id']} does not enclose exact binary-input value")
    farm = load(folder / 'farm_results.csv')
    for row in farm:
        gross, net, loss, percent = [x(row[s]) for s in ('gross_power_mw','net_power_mw','wake_loss_mw','wake_loss_percent')]
        if not (0 <= net <= gross+mp.mpf('1e-9')):
            failures.append('farm constraint violated')
        if abs((gross-net)-loss)>mp.mpf('1e-10'):
            failures.append('farm loss aggregation mismatch')
        if abs(100*loss/gross-percent)>mp.mpf('1e-9'):
            failures.append('farm percentage mismatch')
    result = {'high_precision_digits':mp.dps,'formula_samples':count,
              'formula_within_tolerance':count-sum('audit ' in e for e in failures),
              'max_absolute_error':mp.nstr(worst_abs, 12),
              'tinc_samples':len(tinc),'tinc_inclusions':enclosed,
              'farm_summaries_checked':len(farm),'failures':failures[:16]}
    with open(folder/'validation.json','w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result,indent=2))
    if failures:
        raise SystemExit(1)

if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('folder');run(p.parse_args().folder)
