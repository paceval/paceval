#!/usr/bin/env python3
"""Generate reproducible scientific figures only from published example CSVs."""
from pathlib import Path
import argparse,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

DARK='#112b43';CYAN='#009fc4';GREEN='#25a182';ORANGE='#e9a23b';RED='#cc5b57';GRAY='#687b86'
plt.rcParams.update({'font.size':10,'axes.titlesize':14,'axes.labelsize':10,'figure.dpi':145,
    'axes.spines.right':False,'axes.spines.top':False,'svg.fonttype':'none'})

def read(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def export(fig,dest,stem):
    fig.savefig(dest/(stem+'.png'),bbox_inches='tight',dpi=175,facecolor='white')
    fig.savefig(dest/(stem+'.svg'),bbox_inches='tight',facecolor='white')
    plt.close(fig)
def grouped(rows,name):return np.array([float(x[name]) for x in rows])

def make(data,dest):
    dest.mkdir(parents=True,exist_ok=True)
    hour=read(data/'hourly_trace.csv'); evals=read(data/'evaluations.csv')
    rules=read(data/'rules.csv');summary=read(data/'rule_summary.csv')
    update=read(data/'model_update.csv');tinc=read(data/'tinc_samples.csv')
    # 01: architecture: clearly distinguish host from paceval.
    fig,ax=plt.subplots(figsize=(11,2.65));ax.axis('off');ax.set_xlim(0,11);ax.set_ylim(0,3)
    boxes=[(0.15,'Hourly traces\n& data-quality checks'),(2.95,'Eligibility, caps\n& measured delivery'),(5.75,'paceval\n100 reusable graphs'),(8.55,'Rule aggregation\n& independent audit')]
    for idx,(x,txt) in enumerate(boxes):
        color=CYAN if idx==2 else DARK
        ax.add_patch(FancyBboxPatch((x,.92),2.3,1.22,boxstyle='round,pad=.11,rounding_size=.17',
            facecolor='#eaf7fa' if idx==2 else '#edf1f4',edgecolor=color,linewidth=1.9))
        ax.text(x+1.15,1.53,txt,ha='center',va='center',color=DARK,fontsize=10,fontweight='bold')
        if idx<3:ax.add_patch(FancyArrowPatch((x+2.43,1.52),(x+2.76,1.52),arrowstyle='-|>',mutation_scale=17,color=GREEN,linewidth=1.7))
    ax.text(1.31,.42,'C++ host',ha='center',fontsize=10,color=GRAY)
    ax.text(4.1,.42,'C++ host',ha='center',fontsize=10,color=GRAY)
    ax.text(6.95,.42,'Mathematical execution',ha='center',fontsize=10,color=GREEN)
    ax.text(9.71,.42,'C++ host + Python oracle',ha='center',fontsize=10,color=GRAY)
    export(fig,dest,'01_execution_architecture')
    # 02: full day load, baseline vs actual, energy shifted to rebound
    a=hour[:24];h=grouped(a,'hour')
    fig,ax=plt.subplots(figsize=(10,4.35));ax.plot(h,grouped(a,'baseline_kwh'),label='Baseline demand',lw=2.25,color=DARK)
    ax.plot(h,grouped(a,'actual_kwh'),label='Synthetic metered demand',lw=2.25,color=CYAN)
    ax.axvspan(16.5,19.5,color=ORANGE,alpha=.12,label='DR event (17–19)')
    ax.axvspan(19.5,22.5,color=GREEN,alpha=.12,label='Recovery (20–22)')
    ax.set(xlabel='Hour of day',ylabel='kWh in one-hour interval',title='Physical accounting: peak reduction and same-day recovery')
    ax.set_xticks(np.arange(0,24,2));ax.grid(alpha=.2);ax.legend(frameon=False,ncol=2,fontsize=9)
    export(fig,dest,'02_hourly_load_and_recovery')
    # 03 price signal
    fig,ax=plt.subplots(figsize=(10,3.8));ax.plot(h,grouped(a,'price_event_eur_kwh'),'-o',ms=3,color=CYAN,label='Electricity price in each hour')
    ax.plot(h,grouped(a,'price_recovery_eur_kwh'),'--',lw=2,color=ORANGE,label='Modeled recovery-period reference price')
    ax.axvspan(16.5,19.5,color=GREEN,alpha=.12)
    ax.set(xlabel='Hour of day',ylabel='EUR/kWh',title='Illustrative dynamic prices and the recovery reference')
    ax.set_xticks(np.arange(0,24,2));ax.grid(alpha=.25);ax.legend(frameon=False)
    export(fig,dest,'03_hourly_price_and_recovery_rate')
    # 04 values by rule: 4 families
    labels=[int(x['rule_id']) for x in summary];vals=grouped(summary,'total_value_eur');families=[int(x['family']) for x in rules]
    fig,ax=plt.subplots(figsize=(10,4));palette=[DARK,CYAN,GREEN,ORANGE]
    ax.bar(labels,vals,color=[palette[f] for f in families],width=.85)
    ax.set(xlabel='Versioned rule ID',ylabel='14-day modeled net benefit (EUR)',title='100 configurable mathematical rules evaluated on the same hourly traces')
    ax.grid(axis='y',alpha=.2)
    for f,c in enumerate(palette):ax.bar([],[],color=c,label='Family '+str(f+1))
    ax.legend(frameon=False,ncol=4,fontsize=9)
    export(fig,dest,'04_total_modeled_benefit_by_rule')
    # 05 family stats boxes
    fig,ax=plt.subplots(figsize=(8.2,4.1));blocks=[vals[[i for i,f in enumerate(families) if f==k]] for k in range(4)]
    b=ax.boxplot(blocks,patch_artist=True,labels=['Price + reward','Under-delivery','Comfort cost','Cubic fatigue'],showfliers=False)
    for p,c in zip(b['boxes'],palette):p.set(facecolor=c,alpha=.72)
    ax.set(ylabel='14-day modelled net benefit (EUR)',title='The effect of rule-family design on synthetic valuation')
    ax.tick_params(axis='x',labelsize=9);ax.grid(axis='y',alpha=.25)
    export(fig,dest,'05_rule_family_distribution')
    # 06 numerical validation scatter/residuals, use two independently plotted figures
    sample=evals[::max(1,len(evals)//900)][:900]
    xx=grouped(sample,'native_value_eur');yy=grouped(sample,'value_eur')
    fig,ax=plt.subplots(figsize=(7,4.4));ax.scatter(xx,yy,s=14,alpha=.42,color=CYAN)
    mn=min(min(xx),min(yy));mx=max(max(xx),max(yy));ax.plot([mn,mx],[mn,mx],color=ORANGE,lw=1.5,label='y = x')
    ax.set(xlabel='Independent native C++ value (EUR)',ylabel='paceval value (EUR)',title='Numerical agreement for a deterministic subsample')
    ax.grid(alpha=.23);ax.legend(frameon=False)
    export(fig,dest,'06_paceval_vs_native_reference')
    # 07 examples of exclusion/capping and event engagement
    events=[row for row in hour if row['event']=='1']
    d=[];claimed=[];captions=[]
    for row in events:
        q=float(row['requested_kwh']);cap=float(row['capacity_kwh']);
        actualred=max(0,float(row['baseline_kwh'])-float(row['actual_kwh']))
        eligible=min(q,cap,actualred) if row['quality']=='1' else 0
        d.append(eligible);claimed.append(q)
        captions.append(f"{row['day']}-{row['hour']}")
    fig,ax=plt.subplots(figsize=(10.2,4.3));ii=np.arange(len(events));ax.bar(ii,claimed,width=.8,alpha=.4,label='Requested kWh',color=ORANGE)
    ax.bar(ii,d,width=.55,label='Eligible / metered kWh',color=CYAN)
    ax.set(xlabel='DR event hour (chronological)',ylabel='kWh',title='Metered delivery, capacity capping and rejected claims')
    ax.grid(axis='y',alpha=.22);ax.legend(frameon=False)
    export(fig,dest,'07_requested_vs_eligible_delivery')
    # 08 versioning: changed rule 17
    if update:
        ids=np.array([int(x['hour_index']) for x in update]);before=grouped(update,'old_value_eur');after=grouped(update,'new_value_eur')
        fig,ax=plt.subplots(figsize=(10,4));ax.plot(ids,before,color=DARK,lw=1.6,label='Rule 17 (v1)')
        ax.plot(ids,after,color=GREEN,lw=1.65,ls='--',label='Rule 17 (v2, reward +0.015 EUR/kWh)')
        ax.set(xlabel='Hourly sample index',ylabel='Modeled value (EUR)',title='Controlled version update: only the selected formula is rebuilt')
        ax.grid(alpha=.2);ax.legend(frameon=False)
        export(fig,dest,'08_versioned_rule_update')
    # 09 TINC controlled raw bounds; bounds may be identical to the point for exact inputs.
    t_idx=np.array([int(x['sample_id']) for x in tinc]);point=grouped(tinc,'raw_point');lo=grouped(tinc,'raw_lower');hi=grouped(tinc,'raw_upper')
    fig,ax=plt.subplots(figsize=(9.4,3.8));ax.plot(t_idx,point,'o',markersize=4,color=CYAN,label='Raw TINC result')
    ax.plot(t_idx,lo,linewidth=.9,color=ORANGE,alpha=.8,label='Raw bounds')
    ax.plot(t_idx,hi,linewidth=.9,color=ORANGE,alpha=.8)
    ax.set(xlabel='Controlled dyadic sample ID',ylabel='EUR (simple price-spread kernel)',title='24 sample-wise TINC interval checks against a 90-digit oracle')
    ax.grid(alpha=.22);ax.legend(frameon=False)
    export(fig,dest,'09_tinc_raw_interval_audit')
    print('Generated 9 figures as PNG+SVG in',dest)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--examples',type=Path,default=Path(__file__).resolve().parent.parent/'examples');p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'figures')
    a=p.parse_args();make(a.examples,a.out)
