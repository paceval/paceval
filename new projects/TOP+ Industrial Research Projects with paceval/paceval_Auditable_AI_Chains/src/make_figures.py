#!/usr/bin/env python3
"""Regenerate the reproducible scientific diagrams from published example CSVs.
The hero image is separate (illustrative marketing artwork, not measurement data).
"""
from pathlib import Path
import csv
from collections import Counter,defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
import numpy as np

def data(p):
    with Path(p).open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))

def build(root):
    root=Path(root); ex=root/'examples'; fig=root/'figures';fig.mkdir(exist_ok=True)
    results=data(ex/'results.csv');steps=data(ex/'steps.csv');audit=data(ex/'audit_steps.csv')
    version=data(ex/'version_comparison.csv');tinc=data(ex/'tinc_samples.csv')
    style={'font.size':10,'axes.spines.top':False,'axes.spines.right':False}
    plt.rcParams.update(style)
    def save(n):
        plt.tight_layout(pad=2.0)
        plt.savefig(fig/n, dpi=170, bbox_inches='tight')
        plt.savefig((fig/n).with_suffix('.svg'),bbox_inches='tight')
        plt.close()
    # Architecture with exact expression graph semantics.
    f,ax=plt.subplots(figsize=(12.2,4.4));ax.set_xlim(0,12);ax.set_ylim(0,4);ax.axis('off')
    def panel(x,y,w,h,heading,body):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.13',edgecolor='#1877a0',facecolor='#ebf5fa',linewidth=2))
        ax.text(x+w/2,y+h*.70,heading,ha='center',va='center',size=12,weight='bold',color='#173651')
        ax.text(x+w/2,y+h*.35,body,ha='center',va='center',size=9.3,color='#325777')
    panel(.35,1.38,2,1.25,'Schema validation','IDs, units, domains')
    panel(3,2.55,1.75,.84,'SQUARE','t1 = x*x')
    panel(5,2.55,1.75,.84,'LOG1P','t2 = ln(1+t1)')
    panel(3,.53,1.75,.84,'DENOM','t3 = 1+a*x')
    panel(7.15,1.4,1.9,1.1,'RATIO v1/v1.1','z = t2/t3 (+ .05*x)')
    panel(9.85,1.37,1.85,1.3,'Audit verification','SHA-256 + oracle')
    def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=16,color='#137d97',linewidth=1.7))
    arrow((2.48,2),(3,2.99));arrow((4.86,2.99),(5,2.99));arrow((6.85,2.99),(7.16,2.13))
    arrow((2.48,1.62),(3,.95));arrow((4.87,.96),(7.16,1.74));arrow((9.18,2),(9.85,2))
    ax.text(6.05,.37,'Only approved expression graphs are evaluated by paceval; the host owns the trust boundary.',ha='center',size=9.4)
    save('01_reusable_chain_architecture.png')
    # Request acceptance breakdown
    fig_,ax=plt.subplots(figsize=(9,4.6));names=['Accepted','Rejected'];counts=[sum(r['status']=='OK' for r in results),sum(r['status']=='REJECTED' for r in results)]
    bars=ax.bar(names,counts,color=['#087ca5','#e88a63'],width=.5)
    for bar in bars:ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1,str(int(bar.get_height())),ha='center',weight='bold')
    ax.set_ylim(0,122);ax.set_ylabel('Number of requests');ax.set_title('Deterministic workload: validated and rejected cases')
    save('02_request_outcomes.png')
    # Step values: four stages for an illustrative subset.
    sampleids=[r['request_id'] for r in results if r['status']=='OK'][:30]
    d=defaultdict(dict)
    for r in steps:d[r['request_id']][int(r['step'])]=float(r['value'])
    fig_,ax=plt.subplots(figsize=(10,4.8))
    for j,label in enumerate(['SQUARE: t1','LOG1P: t2','DENOM: t3','RATIO: z'],1):
        ax.plot(range(len(sampleids)),[d[x][j] for x in sampleids],label=label,linewidth=1.65,marker='o',markersize=2.5)
    ax.set_xlabel('Accepted request index (first 30)');ax.set_ylabel('Computed value (dimensionless)')
    ax.set_title('Stage-by-stage mathematical trace for the same requests');ax.legend(ncol=2,fontsize=9)
    save('03_intermediate_values.png')
    # Error distribution plotted as independent high-precision errors when available.
    errors=np.array([float(r['abs_error']) for r in steps]);fig_,ax=plt.subplots(figsize=(9,4.5))
    ax.hist(np.log10(np.maximum(errors,1e-18)),bins=23,color='#1d86aa',edgecolor='white')
    ax.set_xlabel('log10(|paceval - native C++|), zeros displayed at 1e-18')
    ax.set_ylabel('Number of step results');ax.set_title('Observed double-precision agreement with independent C++')
    save('04_numerical_agreement.png')
    # Versioning change in final expression.
    x=np.array([float(r['x']) for r in version]);old=np.array([float(r['version_1_0']) for r in version]);new=np.array([float(r['version_1_1']) for r in version]);
    fig_,ax=plt.subplots(figsize=(9,4.5));ax.plot(x,old,'o-',label='Version 1.0');ax.plot(x,new,'s--',label='Version 1.1')
    ax.set_xlabel('x (dimensionless)');ax.set_ylabel('Final chain value');ax.set_title('Versioned final-node change; intermediate graphs remain identical');ax.legend()
    save('05_formula_versioning.png')
    # TINC non-inclusion shown explicitly, no false 'all pass'.
    vals=np.array([float(r['value']) for r in tinc]);low=np.array([float(r['low']) for r in tinc]);high=np.array([float(r['high']) for r in tinc]);
    fig_,ax=plt.subplots(figsize=(9.5,4.4));xx=np.array([float(r['x']) for r in tinc]);
    ax.plot(xx,vals,'o',markersize=5,color='#1e7da4',label='TINC point estimate')
    ax.fill_between(xx,low,high,color='#37b9d6',alpha=.38,label='Reported TINC interval')
    ax.set_xlabel('x (dimensionless)');ax.set_ylabel('ln(1+x²)');ax.set_title('Sample-wise TINC diagnostic; exact near-zero edge case audited separately');ax.legend(fontsize=8)
    save('06_tinc_sample_diagnostic.png')
    # Hash chaining, physical sequence and head digest of 680 entries.
    fig_,ax=plt.subplots(figsize=(10,3.7));ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(0,3)
    ax.text(5,2.73,'Every audit record commits to its predecessor using SHA-256',ha='center',weight='bold',size=13)
    for i,(x,title,detail) in enumerate([(0.3,'Input','hash(request)'),(2.7,'Step 1…4','formula + value'),(5.15,'Result','final value'),(7.55,'Anchor','record_hash')]):
        ax.add_patch(FancyBboxPatch((x,1),2.05,1,boxstyle='round,pad=.10',edgecolor='#217b98',facecolor='#e6f4f8',lw=1.7))
        ax.text(x+1.025,1.65,title,ha='center',weight='bold',size=11)
        ax.text(x+1.025,1.29,detail,ha='center',size=8)
        if i<3:ax.add_patch(FancyArrowPatch((x+2.12,1.50),(x+2.45,1.5),arrowstyle='-|>',mutation_scale=14,color='#1a94af'))
    ax.text(5,.43,'Demo records: '+str(len(audit))+'  |  Final SHA-256: '+audit[-1]['record_hash'][:21]+'…',ha='center',fontsize=10)
    save('07_hash_linked_audit.png')
    # Rejection categories, counts
    rejection=Counter(r['reason'] for r in results if r['status']=='REJECTED')
    labs=list(rejection);values=[rejection[i] for i in labs]
    fig_,ax=plt.subplots(figsize=(10,5.4));ax.barh(labs,values,color='#dd895f');ax.invert_yaxis()
    ax.set_xlabel('Rejected inputs');ax.set_title('Policy violations detected before mathematical execution')
    save('08_rejection_reasons.png')
    print('Generated 8 science figures in PNG and SVG from audited example data')
if __name__=='__main__':
    import sys
    build(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent)
