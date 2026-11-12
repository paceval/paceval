#!/usr/bin/env python3
"""Reproduce all eight research diagrams from the released example CSV files."""
import csv
from collections import Counter, defaultdict
from pathlib import Path
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BG='#0b1726'; FG='#d8e7f1'; SUB='#98b1c2'; CYAN='#38d7e5'; BLUE='#68aaff'; AMBER='#ffd274'; GREEN='#65d6aa'

def read(folder,name):
    with (folder/name).open(newline='') as f:
        return list(csv.DictReader(f))

def style(ax):
    ax.set_facecolor(BG);ax.tick_params(colors=FG,labelsize=10)
    for sp in ax.spines.values():sp.set_color('#456073')
    ax.xaxis.label.set_color(FG);ax.yaxis.label.set_color(FG)
    ax.title.set_color(FG);ax.grid(color='#456073',alpha=.26)

def new():
    fig,ax=plt.subplots(figsize=(10,4.8),dpi=160);fig.patch.set_facecolor(BG);style(ax);return fig,ax

def save(fig,figdir,basename):
    fig.tight_layout(pad=2.2)
    for suffix in ('png','svg'):
        fig.savefig(figdir/f'{basename}.{suffix}',facecolor=fig.get_facecolor(),bbox_inches='tight',dpi=180)
    plt.close(fig)

def make(folder,figdir):
    folder=Path(folder);figdir=Path(figdir);figdir.mkdir(exist_ok=True,parents=True)
    tasks=read(folder,'requests_results.csv');sens=read(folder,'sensitivity_results.csv')
    updates=read(folder,'model_update.csv');tinc=read(folder,'tinc_samples.csv')
    tinc_stress=read(folder,'tinc_stress_samples.csv')
    # 01: workflow architecture with operational trust boundaries.
    fig,ax=new();ax.set_xlim(0,10);ax.set_ylim(0,3);ax.axis('off')
    names=['Structured\nagent request','Host schema\n+ unit checks','paceval reusable\nfinancial graph','Independent\nnumeric audit','Traceable\nresult']
    for i,name in enumerate(names):
        x=.12+i*2.04
        ax.text(x+.85,1.45,name,ha='center',va='center',fontsize=11,color=FG,fontweight='bold',
                bbox=dict(boxstyle='round,pad=.65',fc='#133d58',ec=CYAN,lw=1.7))
        if i<4:ax.annotate('',xy=(x+1.94,1.43),xytext=(x+1.77,1.43),arrowprops=dict(arrowstyle='-|>',color=GREEN,lw=2))
    ax.text(5,.34,'Only approved models and finite, unit-checked inputs reach the mathematical engine',color=SUB,ha='center',fontsize=11)
    save(fig,figdir,'01_validated_agent_workflow')
    # 02 NPV sensitivities for three example tasks; one task used to avoid apples-to-oranges labels.
    fig,ax=new();subset=[r for r in sens if r['request_id']=='TASK_1000'];
    x=[float(r['rate'])*100 for r in subset];y=[float(r['paceval']) for r in subset]
    ax.plot(x,y,'-o',color=CYAN,linewidth=2.4,markersize=4);ax.set_xlabel('Annual discount rate (%)');ax.set_ylabel('Net present value (synthetic currency units)');ax.set_title('NPV sensitivity: fixed six-period cash-flow scenario')
    save(fig,figdir,'02_npv_rate_sweep')
    # 03 Across all four model families; show distinct measures rather than combining units.
    fig,ax=new();samples={}
    for row in sens:
        if row['request_id'] in ('TASK_1000','TASK_1001','TASK_1002','TASK_1003'):
            samples.setdefault(row['model'],[]).append((int(row['sample']),float(row['paceval'])))
    for i,(m,arr) in enumerate(sorted(samples.items())):
        arr.sort();base=arr[7][1];scale=max(abs(base),1e-3)
        ax.plot([j for j,_ in arr],[(v-base)/scale*100 for _,v in arr],label=m,color=(CYAN,BLUE,GREEN,AMBER)[i],lw=2)
    ax.legend(frameon=False,labelcolor=FG,ncol=2,loc='best');ax.set_xlabel('Sweep sample index');ax.set_ylabel('Change relative to sample 7 (%)');ax.set_title('Relative sensitivity across four approved formula families')
    save(fig,figdir,'03_four_models_sensitivity')
    # 04 Data-driven result counts.
    fig,ax=new();cnt=Counter(t['status'] for t in tasks)
    ax.bar(['Accepted','Rejected'],[cnt.get('OK',0),cnt.get('REJECTED',0)],color=[GREEN,AMBER],width=.52)
    for i,v in enumerate([cnt.get('OK',0),cnt.get('REJECTED',0)]):ax.text(i,v+1,str(v),ha='center',color=FG,weight='bold')
    ax.set_ylim(0,115);ax.set_ylabel('Requests');ax.set_title('100 independently specified tasks and 20 intentionally invalid cases')
    save(fig,figdir,'04_request_validation')
    # 05: one graph per model is created, then successfully reused by later accepted tasks.
    fig,ax=new();valid=[x for x in tasks if x['status']=='OK'];count=Counter(x['model'] for x in valid)
    names=list(sorted(count));ax.bar(names,[1]*len(names),label='Initial use',color=CYAN)
    ax.bar(names,[count[n]-1 for n in names],bottom=[1]*len(names),label='Subsequent request reuse',color=BLUE)
    ax.tick_params(axis='x',labelrotation=12);ax.legend(frameon=False,labelcolor=FG);ax.set_ylabel('Accepted tasks');ax.set_title('Four persistent paceval execution graphs shared across tasks')
    save(fig,figdir,'05_graph_reuse')
    # 06 Native reference discrepancy, histogram includes zero errors.
    fig,ax=new();errors=np.array([float(r['abs_difference']) for r in sens]);
    positive=np.maximum(errors,1e-17)
    ax.hist(np.log10(positive),bins=26,color=CYAN,edgecolor=BG)
    ax.set_xlabel('log10 absolute difference (values below 1e-17 shown at 1e-17)')
    ax.set_ylabel('Evaluations');ax.set_title('1,600 scalar comparisons with an independent native C++ reference')
    save(fig,figdir,'06_native_reference_accuracy')
    # 07 Model update: only the discounted fifth-year CF is adjusted.
    fig,ax=new();u=sorted(updates,key=lambda r:int(r['sample']))
    ax.plot([int(r['sample']) for r in u],[float(r['old_value']) for r in u],'-o',color=CYAN,label='Approved NPV v1')
    ax.plot([int(r['sample']) for r in u],[float(r['new_value']) for r in u],'--s',color=AMBER,label='New NPV v2 (c5 × 0.98)')
    ax.legend(frameon=False,labelcolor=FG);ax.set_xlabel('Sensitivity sample');ax.set_ylabel('NPV (synthetic currency units)');ax.set_title('Controlled model update without rebuilding unrelated graphs')
    save(fig,figdir,'07_model_version_change')
    # 08: exact IEEE binary64 input audit; show raw results of both graphs.
    from decimal import Decimal,localcontext
    def inclusion(rows, prefix):
        result=[]
        with localcontext() as ctx:
            ctx.prec=100
            for r in rows:
                conv=lambda key:Decimal.from_float(float(r[key]))
                truth=conv('principal')/(Decimal(1)+conv('rate'))
                result.append(conv(prefix+'lower')<=truth<=conv(prefix+'upper'))
        return result
    direct=inclusion(tinc,'baseline_'); improved=inclusion(tinc,'raw_')
    direct_broad=inclusion(tinc_stress,'baseline_'); improved_broad=inclusion(tinc_stress,'raw_')
    fig,ax=new();x=np.arange(len(tinc))
    ax.bar(x-.2,[int(t) for t in direct],width=.38,color=AMBER,label=f'Direct: {sum(direct)}/{len(direct)}')
    ax.bar(x+.2,[int(t) for t in improved],width=.38,color=GREEN,label=f'Reformulated: {sum(improved)}/{len(improved)}')
    ax.set_yticks([0,1],labels=['Not enclosed','Enclosed']);ax.set_xlabel('Original 24 sample indices');ax.set_ylim(-.15,1.38)
    ax.legend(frameon=False,labelcolor=FG,loc='upper right',ncol=2)
    ax.set_title(f'Raw TINC inclusion, exact binary64 references | broader audit: {sum(improved_broad)}/{len(improved_broad)} reformulated')
    save(fig,figdir,'08_tinc_point_audit')
    print('Created 8 scientific diagrams (PNG and SVG)')

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('examples',type=Path);p.add_argument('figures',type=Path)
    a=p.parse_args();make(a.examples,a.figures)
