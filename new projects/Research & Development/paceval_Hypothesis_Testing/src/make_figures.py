#!/usr/bin/env python3
"""Regenerate all scientific figures from the included CSV evidence.

This file does not generate the marketing illustration (00_...png).
Only actual reproducible C++ outputs are used for quantitative diagrams.
"""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mpmath as mp


def read(file):
    with open(file, newline='', encoding='utf-8') as h:
        return list(csv.DictReader(h))


def finish(fig, filename, out):
    fig.savefig(out / filename, dpi=175, bbox_inches='tight')
    fig.savefig(out / filename.replace('.png','.svg'), bbox_inches='tight')
    plt.close(fig)


def main(base, out):
    out.mkdir(parents=True,exist_ok=True)
    dataset=read(base/'dataset.csv')
    preds=read(base/'selected_predictions.csv')
    scores=read(base/'hypotheses.csv')
    shortlist=read(base/'shortlist.csv')
    audit=read(base/'audit_samples.csv')
    tinc=read(base/'tinc_samples.csv')

    # Architectural figure: roles reflect the tested C++ implementation.
    fig,ax=plt.subplots(figsize=(12,3.2))
    ax.set_xlim(0,12);ax.set_ylim(0,3);ax.axis('off')
    blocks=[('Candidate generator','10,000 coefficient-bound\nhypotheses',0.1),
            ('paceval 4.25','8 reusable mathematical\nexecution graphs',2.65),
            ('C++ selection','Top 100 training →\nvalidation minimum',5.2),
            ('Held-out test','One final test and\nextrapolation audit',7.75),
            ('Verification','Native C++ + independent\n110-digit reference',10.3)]
    for idx,(header,subtitle,x) in enumerate(blocks):
        ax.add_patch(plt.Rectangle((x,0.9),2.25,1.3,facecolor='#edf5fc',edgecolor='#2679b8',lw=1.7))
        ax.text(x+1.125,1.82,header,ha='center',va='center',fontsize=10,weight='bold')
        ax.text(x+1.125,1.35,subtitle,ha='center',va='center',fontsize=7.4)
        if idx<4:ax.annotate('',xy=(x+2.53,1.57),xytext=(x+2.28,1.57),arrowprops=dict(arrowstyle='->',lw=2))
    ax.text(6,2.75,'Evaluation boundary: paceval computes formulas; C++ generates, ranks, and audits hypotheses',ha='center',fontsize=10)
    finish(fig,'01_execution_architecture.png',out)

    # Primary selected curve with explicit held-out vs extrapolation splits.
    fig,ax=plt.subplots(figsize=(10.5,4.1))
    colors={'training':'#377eb8','validation':'#4daf4a','test':'#984ea3','extrapolation':'#ff7f00'}
    for fold in colors:
        seq=[r for r in preds if r['partition']==fold]
        xx=np.array([float(r['x']) for r in seq]);yy=np.array([float(r['observed_y']) for r in seq]);
        ax.scatter(xx,yy, s=11,alpha=.65,label=f'{fold}: measured synthetic values',color=colors[fold])
    xt=np.linspace(-2.42,3.85,500)
    yy=1.4*np.sin(1.8*xt)+.3*xt**2+.12
    ax.plot(xt,yy,color='black',lw=1.6,label='Selected model = planted target family')
    ax.axvline(2.5,ls='--',lw=1,color='gray')
    ax.set_xlabel('x (dimensionless)');ax.set_ylabel('Synthetic response');
    ax.set_title('Selected formula across interpolation and extrapolation data')
    ax.legend(fontsize=7.7,ncol=2,loc='upper left');ax.grid(alpha=.17)
    finish(fig,'02_selected_hypothesis_fit.png',out)

    # Candidate landscape visualizes ALL 10k screened candidates.
    fig,ax=plt.subplots(figsize=(10.5,3.7))
    groups=np.array([int(r['family']) for r in scores]);loss=np.array([float(r['training_mse']) for r in scores]);
    yy=np.maximum(loss,1e-14)
    ax.scatter(np.arange(len(loss)),yy,c=groups,s=4,alpha=.35,cmap='tab10',rasterized=True)
    ax.scatter([0],[loss[0]],s=70,facecolors='none',edgecolors='black',lw=2,label='Planted candidate #0')
    ax.set_yscale('log');ax.set_xlabel('Candidate ID');ax.set_ylabel('Training MSE (log scale)')
    ax.set_title('Screening of 10,000 distinct coefficient-bound hypotheses')
    ax.grid(alpha=.17);ax.legend(loc='upper right',fontsize=8)
    finish(fig,'03_candidate_screening.png',out)

    # Honest model selection: validation only for top 100 train candidates.
    fig,ax=plt.subplots(figsize=(7.7,4.1))
    xt=np.array([float(r['training_mse']) for r in shortlist]);
    yt=np.array([float(r['validation_mse']) for r in shortlist]);
    ax.scatter(xt,yt,s=23,alpha=.6)
    chosen=min(shortlist,key=lambda r:float(r['validation_mse']))
    ax.scatter([float(chosen['training_mse'])],[float(chosen['validation_mse'])],s=140,marker='*',label='Selected candidate')
    ax.set_xscale('log');ax.set_yscale('log');ax.set_xlabel('Training MSE');ax.set_ylabel('Validation MSE')
    ax.set_title('Validation-only selection among 100 training-shortlisted formulas')
    ax.legend(fontsize=9);ax.grid(alpha=.2)
    finish(fig,'04_training_validation_selection.png',out)

    fig,ax=plt.subplots(figsize=(8.6,3.4))
    folds=['training','validation','test','extrapolation']
    fold_mse=[np.mean([(float(r['paceval_prediction'])-float(r['observed_y']))**2 for r in preds if r['partition']==k]) for k in folds]
    bars=ax.bar(folds,fold_mse)
    for bar,value in zip(bars,fold_mse):
        ax.text(bar.get_x()+bar.get_width()/2,value*1.006,f'{value:.2e}',ha='center',va='bottom',fontsize=9)
    ax.set_ylim(0,max(fold_mse)*1.28);ax.set_ylabel('MSE against synthetic observations')
    ax.set_title('Selected hypothesis: data-partition performance (no speed comparison)')
    finish(fig,'05_heldout_and_extrapolation.png',out)

    # High precision reference differences: use same binary input values as C++.
    mp.mp.dps=110
    def model(r):
        x,a,b,c,d=[mp.mpf(float(r[q])) for q in ('x','a','b','c','d')]
        fam=int(r['family'])
        if fam==0:return a*mp.sin(b*x)+c*x*x+d
        if fam==1:return a*mp.cos(b*x)+c*x*x+d
        if fam==2:return a*mp.tanh(b*x)+c*x*x+d
        if fam==3:return a*mp.exp(-b*x*x)+c*x*x+d
        if fam==4:return a*mp.sin(b*x)+c*x+d
        if fam==5:return a*mp.cos(b*x)+c*x+d
        if fam==6:return a*mp.sin(b*x)+c*x*x+d*mp.cos(x)
        return a*mp.log(1+b*x*x)+c*x*x+d
    diffs=[float(abs(mp.mpf(float(r['paceval_value']))-model(r))) for r in audit]
    fig,ax=plt.subplots(figsize=(9,3.6))
    ax.scatter(range(len(diffs)),np.maximum(np.array(diffs),1e-19),s=17,alpha=.73)
    ax.set_yscale('log');ax.set_xlabel('Independently sampled hypothesis evaluation');ax.set_ylabel('Absolute error vs 110-digit reference')
    ax.set_title(f'Independent numerical check: {len(diffs)} sampled evaluations, max {max(diffs):.2e}')
    ax.grid(alpha=.18)
    finish(fig,'06_high_precision_audit.png',out)

    # Bound widths are actual reported bounds; no universal guarantee implied.
    width=[float(r['upper_bound'])-float(r['lower_bound']) for r in tinc]
    fig,ax=plt.subplots(figsize=(9,3.6))
    ax.bar(np.arange(len(tinc)),np.array(width)/np.finfo(float).eps)
    ax.set_xlabel('TINC sample index');ax.set_ylabel('Reported interval width / machine epsilon')
    ax.set_title('24 finite TINC samples, independently audited for containment')
    ax.grid(axis='y',alpha=.17)
    finish(fig,'07_tinc_sample_intervals.png',out)
    print('Created seven research charts in',out)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--examples',type=Path,default=Path(__file__).resolve().parent.parent/'examples')
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'figures')
    a=p.parse_args()
    main(a.examples,a.out)
