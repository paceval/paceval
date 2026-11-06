#!/usr/bin/env python3
"""Regression against v1.2 archived rows, high-precision control and convergence."""
from __future__ import annotations
import csv, json, math, os, pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'results'/'scan_refined_v12.csv'
BIN=ROOT/'bin'/'braneworld_v13_linux_x86_64'
REF_ADV=1.03771487669293765152978766858
REF_PERCENT=20.9627924404683615700

def getrows(path):
    return {(float(r['rho0']),float(r['w']),float(r['D'])):r for r in csv.DictReader(open(path,newline=''))}

def verify(cpp_path):
    orig=getrows(BASE)
    rows=getrows(cpp_path)
    assert len(orig)==47 and len(rows)==50,(len(orig),len(rows))
    assert set(orig).issubset(rows)
    extra=set(rows)-set(orig)
    assert extra=={(.1,-1.,1.),(1.,-1.,.1),(10.,-1.,.1)},extra
    max_delta=max(abs(float(orig[k]['advance'])-float(rows[k]['advance'])) for k in orig)
    max_pct=max(abs(float(orig[k]['relative_pct'])-float(rows[k]['relative_pct'])) for k in orig)
    key=rows[(10.,-.5,1.)]
    assert abs(float(key['advance'])-REF_ADV)<1e-8
    assert abs(float(key['relative_pct'])-REF_PERCENT)<1e-6
    assert max_delta<1e-8 and max_pct<1e-6,(max_delta,max_pct)
    return {'validated_archived_rows':47,'additional_de_sitter_cases':sorted(map(list,extra)),
            'max_abs_advance_discrepancy_v12':max_delta,
            'max_abs_relative_pct_discrepancy_v12':max_pct,
            'key_advance':float(key['advance']), 'key_relative_pct':float(key['relative_pct'])}

if __name__=='__main__':
    out={'native':verify(ROOT/'results'/'native_scan_v13.csv'),'paceval':verify(ROOT/'results'/'paceval_scan_v13.csv')}
    print(json.dumps(out,indent=2))
    (ROOT/'validation'/'regression_summary.json').write_text(json.dumps(out,indent=2)+'\n')
