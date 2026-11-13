#!/usr/bin/env python3
"""Independent numerical audit of trained frozen MLP and paceval postprocessing.
80 significant decimal digits. Independent implementations; never uses C++ output as a computation input.
"""
from pathlib import Path
from decimal import Decimal,localcontext
import csv, json, math, argparse, random
D=Decimal
ROOT=Path(__file__).resolve().parents[1]
FEATURES=list(csv.DictReader((ROOT/'examples/synthetic_bearing_features.csv').open()))
NORMS=list(csv.DictReader((ROOT/'examples/normalization.csv').open()))
OUTPUTS=list(csv.DictReader((ROOT/'results/inference_results.csv').open()))
WEIGHTS=list(csv.DictReader((ROOT/'examples/frozen_network_weights.csv').open()))

def weights(vers):
    layout=[(8,8),(8,4),(4,1)]
    mats=[[[D(0) for _ in range(n)] for _ in range(m)] for m,n in layout]
    biases=[[D(0) for _ in range(n)] for _,n in layout]
    for row in WEIGHTS:
        if row['version']!=vers:continue
        layer=int(row['layer'])-1; i=int(row['input']);j=int(row['neuron']);v=D(row['weight'])
        if i==-1:biases[layer][j]=v
        else:mats[layer][i][j]=v
    return mats,biases

def sigmoid(z):
    if z>=0:return D(1)/(D(1)+(-z).exp())
    t=z.exp();return t/(D(1)+t)

def reference(model,features):
    mats,biases=model
    x=[(D(features[f])-D(NORMS[i]['mean']))/D(NORMS[i]['std']) for i,f in enumerate(list(features.keys())[-8:])]
    for mat,bias in zip(mats,biases):
        x=[sigmoid(bias[j]+sum((x[i]*mat[i][j] for i in range(len(x))),D(0))) for j in range(len(bias))]
    return x[0]

def audit():
    random.seed(20261113)
    records={r['version'] if 'version' in r else r['model_version']:[] for r in OUTPUTS[:1]}
    grouped={'v1':[],'v2':[]}
    for row in OUTPUTS:grouped[row['model_version']].append(row)
    mismatches=[];worst=0;checked=0;floatparity=0;threshold_flips=0
    # 384 per version, spread across train/validation/test/shift_test.
    chosen=sorted(set([0,1,32,64,255,767,768,1023,1024,1279,1280,1535]+random.sample(range(1536),372)))
    with localcontext() as ctx:
        ctx.prec=80
        for vers in ['v1','v2']:
            model=weights(vers)
            for idx in chosen:
                raw=FEATURES[idx]; out=grouped[vers][idx]
                hi=reference(model,raw)
                lo=D(out['paceval_layered_score'])
                flat=D(out['paceval_flattened_score'])
                nat=D(out['native_cpp_score'])
                difference=float(abs(hi-lo))
                worst=max(worst,difference)
                if difference>1e-12:mismatches.append([vers,idx,'high precision',difference])
                if abs(lo-flat)>D('2e-11') or abs(lo-nat)>D('2e-11'):mismatches.append([vers,idx,'parity'])
                if (hi>=D('0.5')) != (lo>=D('0.5')):threshold_flips+=1
                nrm=[(D(raw[k])-D(NORMS[j]['mean']))/D(NORMS[j]['std']) for j,k in enumerate(list(raw.keys())[-8:])]
                delta=(D('0.08') if vers=='v1' else D('0.11'))*nrm[0]-(D('0.035') if vers=='v1' else D('0.025'))*nrm[7]+D('0.02')*nrm[6]
                corrected=(hi-D('0.5'))+delta
                advisory=sigmoid(D(3)*corrected)
                if abs(advisory-D(out['advisory_index']))>D('2e-12'):mismatches.append([vers,idx,'advisory'])
                p=(D('0.7')*hi+D('0.2')*advisory+D('0.1')*abs(hi-D('0.5')))
                if abs(p-D(out['inspection_priority']))>D('2e-12'):mismatches.append([vers,idx,'priority'])
                checked+=1
    assert not mismatches,mismatches[:6]
    assert threshold_flips==0,f'near threshold flips: {threshold_flips}'
    report={'status':'PASS','decimal_precision':80,'audited_samples_per_version':len(chosen),'independent_network_and_score_comparisons':checked*3,'max_absolute_difference_in_neural_output':worst,'threshold_flips_on_audit':threshold_flips,'note':'Synthetic dataset; finite-sample checks are not global error bounds'}
    (ROOT/'results/independent_high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':audit()
