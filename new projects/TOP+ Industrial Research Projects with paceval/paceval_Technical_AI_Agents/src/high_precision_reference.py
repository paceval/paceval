#!/usr/bin/env python3
"""Independent 110-digit oracle for the mathematical models, no paceval imports.

The input *binary64* SI numbers are treated as exact starting points for the
TINC audit; this is crucial for meaningful inclusion checks. Mathematical
references are evaluated in mpmath, not copied from the C++ reference.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
import mpmath as mp

mp.mp.dps = 110

def exact(v: str):
    return mp.mpf(float(v))  # exact binary64 value at 110-digit working precision

def evaluate(model: str, x):
    a,b,c,d,e,f = x
    if model == 'axial_stress': return a/b
    if model == 'electrical_power': return a*b
    if model == 'kinetic_energy': return mp.mpf('0.5')*a*b*b
    if model == 'heat_flow': return a*(b-c)
    if model == 'voltage_drop': return a*b
    if model == 'cantilever_deflection': return a*b**3/(3*c*d)
    if model == 'aerodynamic_drag': return mp.mpf('0.5')*a*b*c*d**2
    if model == 'proposal_proxy': return a*b/(c+d)+e*mp.sqrt(f*f)
    raise ValueError(f'Unknown high-precision model {model}')

SI_SCALES = {
 "N":1,"kN":1e3,"m":1,"cm":1e-2,"mm":1e-3,
 "m2":1,"cm2":1e-4,"mm2":1e-6,"m4":1,"cm4":1e-8,
 "Pa":1,"kPa":1e3,"MPa":1e6,"GPa":1e9,"V":1,"mV":1e-3,
 "A":1,"mA":1e-3,"W":1,"kW":1e3,"J":1,"kJ":1e3,
 "kg":1,"g":1e-3,"m/s":1,"km/h":1/3.6,"K":1,"W/K":1,
 "ohm":1,"kg/m3":1,"1":1,"N*s/m2":1,"N/m":1
}

def run(results_path, tinc_path, cases_path):
    checked = 0
    max_relative = mp.mpf('0')
    statuses = Counter()
    with open(results_path, newline='', encoding='utf-8') as handle:
        results = list(csv.DictReader(handle))
    with open(cases_path, newline='', encoding='utf-8') as handle:
        cases = {r['request_id']:r for r in csv.DictReader(handle)}
    for row in results:
        statuses[row['status']] += 1
        if row['status'] != 'OK':
            continue
        case=cases[row['request_id']]
        x=[]
        for i in range(6):
            if not case[f'v{i}']:x.append(mp.mpf(0))
            else:x.append(mp.mpf(float(float(case[f'v{i}'])*SI_SCALES[case[f'u{i}']])))
        # Output scaling is defined by the request; the C++ double conversion
        # is reconstructed, then mathematical evaluation is independently done.
        reference = evaluate(row['model_id'],x)/exact(str(SI_SCALES[case['output_unit']]))
        actual = exact(row['result'])
        native = exact(row['native_reference'])
        tolerance=mp.mpf('6e-12')*(1+mp.fabs(reference))
        if mp.fabs(actual-reference)>tolerance or mp.fabs(native-reference)>tolerance:
            raise AssertionError(f"Independent high-precision mismatch {row['request_id']}")
        checked += 1
    interval_total, interval_contained = 0, 0
    violations = []
    with open(tinc_path, newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            x = [exact(row[f'x{i}']) for i in range(6)]
            y = evaluate(row['model_id'],x)
            low,high = exact(row['lower_si']),exact(row['upper_si'])
            interval_total += 1
            if low <= y <= high: interval_contained += 1
            else: violations.append((row['request_id'],row['model_id'],mp.nstr(y,35),row['lower_si'],row['upper_si']))
            rel = mp.fabs(exact(row['result_si'])-y)/(1+mp.fabs(y))
            max_relative = max(max_relative,rel)
    print(f'HIGH_PRECISION dps={mp.mp.dps} accepted_outputs={checked} TINC_containment={interval_contained}/{interval_total} max_relative_discrepancy={mp.nstr(max_relative,8)}')
    if violations:
        for v in violations: print('INTERVAL_EXCLUSION',*v)
    assert interval_total == 24
    assert statuses['OK'] == checked

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--results',required=True)
    ap.add_argument('--tinc',required=True)
    ap.add_argument('--cases',required=True)
    a=ap.parse_args()
    run(a.results,a.tinc,a.cases)
