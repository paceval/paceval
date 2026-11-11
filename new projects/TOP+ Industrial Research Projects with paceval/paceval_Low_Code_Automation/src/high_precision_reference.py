#!/usr/bin/env python3
"""Independent 80-digit Decimal validation of the published paceval data.

The oracle is coded independently of the C++ function/evaluation code;
no paceval library or C++ graph information is used to compute the answer.
The empirical interval check is pointwise, not a proof for all inputs.
"""
import csv
from decimal import Decimal as D, localcontext
from pathlib import Path
import argparse


def reference(model, version, z):
    if model == "condition_score":
        uT,uV,uI,b0,bT,bV,bI=z
        score=b0+bT*uT+bV*uV+bI*uI
        if version=="1.1":score+=D("0.05")*uT*uV
        return 1/(1+(-score).exp())
    if model=="quotation":
        C,m,r,t,F=z
        return C*(1+m)*(t*(1+r).ln()).exp()+F
    if model=="calibration":
        T,a0,a1,a2,b,h=z
        return T+a0+a1*T+a2*T*T+b*(1+h).ln()
    raise AssertionError("unrecognized model")


def run(args):
    cases=0; max_abs=D(0); failures=[]
    with localcontext() as ctx:
        ctx.prec=80
        with Path(args.results).open(newline="",encoding="utf-8") as f:
            for row in csv.DictReader(f):
                vals=[D(x) for x in row["inputs"].split(";")]
                ref=reference(row["model"],row["version"],vals)
                value=D(row["paceval_result"])
                diff=abs(ref-value)
                max_abs=max(max_abs,diff);cases+=1
                if diff>D("3e-11")*max(D(1),abs(ref)):
                    failures.append((row["model"],row["index"],str(diff)))
        intervals=0; misses=[]
        with Path(args.tinc).open(newline="",encoding="utf-8") as f:
            for row in csv.DictReader(f):
                values=[D(x) for x in row["inputs"].split(";")]
                ref=reference("condition_score","1.0",values)
                lower,upper=D(row["lower"]),D(row["upper"])
                intervals+=1
                if not (lower<=ref<=upper):
                    misses.append((row["index"],str(ref-lower),str(ref-upper)))
    print(f"High-precision audit: {cases} calculations; maximum absolute error {max_abs:.4E}")
    print(f"TINC sample containment: {intervals-len(misses)}/{intervals}")
    if failures:print("Numerical mismatches:",failures[:10])
    if misses:print("TINC interval exclusions:",misses[:10])
    if failures or misses:raise SystemExit(1)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--results",default=str(Path(__file__).resolve().parents[1]/"examples/batch_results.csv"))
    p.add_argument("--tinc",default=str(Path(__file__).resolve().parents[1]/"examples/tinc_samples.csv"))
    run(p.parse_args())
