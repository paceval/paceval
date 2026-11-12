#!/usr/bin/env python3
"""Create a small, independently evaluated plotting subset from evaluations.csv."""
from pathlib import Path
import csv
import sys
import mpmath as mp
sys.path.insert(0,str(Path(__file__).resolve().parent))
from high_precision_reference import reference,as_mpf
mp.mp.dps=100
root=Path(__file__).resolve().parents[1]
models={}
with (root/'examples/models.csv').open() as f:
    for r in csv.DictReader(f):
        models[int(r['id'])]=(int(r['family']),mp.mpf(r['formula'].rsplit(')+(',1)[1][:-1]))
with (root/'examples/evaluations.csv').open() as f, (root/'examples/high_precision_audit_samples.csv').open('w',newline='') as g:
    w=csv.writer(g);w.writerow(['model_id','family','sample','absolute_error'])
    for r in csv.DictReader(f):
        i=int(r['model_id']);s=int(r['sample'])
        if i%10!=0 or s%4!=0:continue
        fam,offset=models[i];ref=reference(fam,offset,[as_mpf(r[k]) for k in ('x','a','b','c','d')]);val=as_mpf(r['paceval_value'])
        w.writerow([i,fam,s,mp.nstr(abs(val-ref),17)])
print('Created independent high-precision plotting subset')
