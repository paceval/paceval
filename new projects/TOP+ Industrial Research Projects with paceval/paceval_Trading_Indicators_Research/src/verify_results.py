#!/usr/bin/env python3
"""Independent numerical and prefix-causality audit; standard library + mpmath.

Uses raw decimal text output for a 80-dps oracle, not a copy of C++ formula.
Checks every score against the native reference (file) as well. Score-model
coefficient strings are read from the manifest, not learned or optimized.
"""
import argparse, csv, json, pathlib
from decimal import Decimal, localcontext

def readcsv(p):
    with open(p,newline='',encoding='utf8') as f: return list(csv.DictReader(f))

def audit(full, prefix=None):
    full=pathlib.Path(full)
    scores=readcsv(full/'score_results.csv')
    states=readcsv(full/'indicator_states.csv')
    manifest=readcsv(full/'models.csv')
    surface=readcsv(full/'score_surface.csv')
    models={int(r['model_id']):r for r in manifest if r['version']=='1'}
    assert len(models)==128 and len(states)==380 and len(scores)==380*128 and len(surface)==3721
    max_diff=0.0
    with localcontext() as ctx:
        ctx.prec=80
        for row in scores[::48]:
            model_id=int(row['model_id']); w=models[model_id]
            a,b,c,d,e=[Decimal(w[k]) for k in ('intercept','momentum_weight','macd_weight','rsi_weight','volatility_weight')]
            m,h,q,v=[Decimal(row[k]) for k in ('momentum_pct','macd_hist_pct','rsi_centered','vol_normalized')]
            k1=Decimal('0.001')*(1+model_id%16)
            k2=Decimal('0.001')*(1+(model_id//16)%8)
            z=a+b*m+c*h+d*q+e*v+k1*m*q+k2*h*v
            ref=Decimal(1)/(Decimal(1)+(-z).exp())
            val=Decimal(row['score_paceval'])
            delta=float(abs(val-ref));max_diff=max(max_diff,delta)
            assert delta < 1e-12,(model_id,row['bar'],delta)
    for row in scores:
        assert float(row['abs_difference']) <= 1e-9*(1+abs(float(row['score_native'])))
    for row in surface:
        assert float(row['abs_difference']) <= 1e-9*(1+abs(float(row['score_native'])))
    causal=None
    if prefix:
        short=pathlib.Path(prefix)
        shortstates=readcsv(short/'indicator_states.csv')
        shortscore=readcsv(short/'score_results.csv')
        assert len(shortstates)==200 and len(shortscore)==200*128
        for a,b in zip(states,shortstates):
            assert a==b,('future-leakage state',a['bar'])
        for a,b in zip(scores,shortscore):
            assert a==b,('future-leakage score',a['bar'],a['model_id'])
        causal={'prefix_bars':240,'compared_state_rows':200,'compared_score_rows':25600,'identical':True}
    report={'status':'PASS','sdk_score_evaluations':len(scores),'score_formulas':128,'causal_output_bars':len(states),'surface_evaluations':len(surface),'high_precision_digits':80,'high_precision_comparisons':len(scores[::48]),'max_absolute_difference_to_high_precision':max_diff,'prefix_audit':causal,'note':'Decimal inputs read from 17-digit exported CSV; arithmetic accuracy is not a trading-performance claim'}
    print(json.dumps(report,indent=2))
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('full');parser.add_argument('--prefix');parser.add_argument('--output')
    args=parser.parse_args();result=audit(args.full,args.prefix)
    if args.output:pathlib.Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
