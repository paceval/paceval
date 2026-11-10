"""Independent, reproducible 110-digit decimal numerical check of massless invariant m^2.

Does not use paceval. mpmath is required (pip install mpmath).
If passed a TINC CSV from real paceval, checks sampled enclosure of 110-digit
reference. This is an empirical check only: Arb/FLINT would be needed to
certify rigorous enclosures under stated rounding assumptions.
"""
import argparse
import csv
import math
from pathlib import Path
import mpmath as mp
mp.mp.dps = 110


def highprecision(pt1, pt2, de, dp):
    # mp.mpf(binary64 float) preserves the EXACT supplied binary64 inputs.
    e, p = mp.mpf(float(de)), mp.mpf(float(dp))
    return 4 * mp.mpf(float(pt1)) * mp.mpf(float(pt2)) * (mp.sinh(e / 2)**2 + mp.sin(p / 2)**2)


def analyze():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tinc-csv', type=Path)
    parser.add_argument('--strict-tinc', action='store_true', help='Return nonzero if any sampled enclosure fails')
    parser.add_argument('--out', type=Path, default=Path('results/high_precision_edges.csv'))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for k in range(2, 16):
        a = 10.0 ** -k
        ref = highprecision(50., 60., a, a)
        direct = 2*50.*60.*(math.cosh(a)-math.cos(a))
        stable = 4*50.*60.*(math.sinh(a/2)**2+math.sin(a/2)**2)
        rdirect = float(abs(mp.mpf(direct) - ref) / ref)
        rstable = float(abs(mp.mpf(stable) - ref) / ref)
        rows.append({'angle': format(a, '.17g'), 'm2_mp_110_digits': mp.nstr(ref, 110),
                     'direct_binary64': repr(direct), 'stable_binary64': repr(stable),
                     'relative_error_direct': format(rdirect, '.14g'),
                     'relative_error_stable': format(rstable, '.14g')})
        print(f'angle 1e-{k:02}: direct rel error={rdirect:.4g}; stable rel error={rstable:.4g}')
        assert rstable < 1e-13, f'Stable formula failed independent numerical check at 1e-{k}'
    assert float(rows[-1]['relative_error_direct']) > 0.99
    with args.out.open('w', newline='', encoding='utf-8') as f:
        wr=csv.DictWriter(f, fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
    print('HIGH PRECISION PASS, saved:', args.out)
    if args.tinc_csv:
        with args.tinc_csv.open(newline='', encoding='utf-8') as f: data=list(csv.DictReader(f))
        failures=[];included=0
        tally={}
        for r in data:
            ref=highprecision(float(r['pt1']), float(r['pt2']), float(r['deta']), float(r['dphi']))
            lower=mp.mpf(float(r['lower']));upper=mp.mpf(float(r['upper']))
            key=r['formula']; count, passes = tally.get(key,(0,0)); count+=1
            if lower <= ref <= upper: included+=1; passes+=1
            else: failures.append((key,r['angle'],mp.nstr(ref,35)))
            tally[key]=(count,passes)
        print('TINC 110-digit sampled inclusion:', included, '/', len(data))
        for formula,(n,ok) in sorted(tally.items()):print(f'  {formula}: {ok}/{n} enclosed')
        if failures:
            print('SAMPLES NOT ENCLOSED:', failures)
            print('WARNING: these sample intervals do not enclose the high-precision reference. Backend:', data[0]['backend'])
            if args.strict_tinc: raise SystemExit(2)
        else: print('All sampled 110-digit references enclosed. Not a proof of rigorous interval correctness.')


if __name__ == '__main__': analyze()
