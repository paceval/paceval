#!/usr/bin/env python3
"""Independent 110-decimal-digit point-value checks for paceval TINC samples.

A sampled containment result is NOT a proof of rigorous interval arithmetic.
The reference uses the *binary64 input values and graph constants*, promoted to
mpmath exact values, so the same expression is compared across backends.
"""
import argparse
import csv
import math
from pathlib import Path
import mpmath as mp

mp.mp.dps = 110


def reference(row):
    # Exact binary64 inputs, then 110-digit arithmetic.
    x = {key: mp.mpf(float(row[key])) for key in (
        't', 'contrast', 'tau', 'freq', 'phase', 'hits', 'trials', 'theta1', 'theta2')}
    if row['formula'] == 'ramsey':
        # C++ paceval source uses this correctly rounded binary64 literal for 2*pi.
        two_pi_graph = mp.mpf(float(6.283185307179586))
        return (1 + x['contrast'] * mp.exp(-x['t'] / x['tau']) *
                mp.cos(two_pi_graph * x['freq'] * x['t'] + x['phase'])) / 2
    if row['formula'] == 'circuit':
        return mp.cos(x['theta1']) * mp.cos(x['theta2'])
    raise ValueError(f"Unexpected formula: {row['formula']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    with args.csv.open(newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 24, f'Expected 24 TINC reference cases, got {len(rows)}'
    failures = 0
    worst_gap = mp.mpf(0)
    print(f'110-digit independent reference; {len(rows)} TINC point samples:')
    for row in rows:
        val = reference(row)
        lo = mp.mpf(float(row['lower']))
        hi = mp.mpf(float(row['upper']))
        contained = lo <= val <= hi
        if not contained:
            failures += 1
            gap = lo-val if val < lo else val-hi
            worst_gap = max(worst_gap, gap)
            print(f"OUTSIDE: {row['formula']} sample {row['sample_index']}, gap={mp.nstr(gap,8)}")
    print(f'HIGH_PRECISION_RESULT: {len(rows)-failures}/{len(rows)} contained, failures={failures}, worst gap={mp.nstr(worst_gap,8)}')
    print('Pointwise containment is evidence for these samples, not a formal interval certification.')
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
