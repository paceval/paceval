#!/usr/bin/env python3
"""Recreate the published figures strictly from included replay CSV files."""
import argparse, csv, math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from collections import Counter

INK='#122c48'; NAVY='#102b4d'; CYAN='#007cc3'; GREEN='#008c78'; CORAL='#d97632'; GRAY='#677b8b'; BG='#f4f8fb'

def load(path):
    with open(path,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def axes():
    fig,ax=plt.subplots(figsize=(10.5,5.2));fig.patch.set_facecolor('white')
    ax.grid(True,alpha=.16);ax.spines[['top','right']].set_visible(False)
    return fig,ax

def save(fig,figures,stem):
    fig.tight_layout(pad=2.2)
    fig.savefig(figures/f'{stem}.png',dpi=175,bbox_inches='tight',facecolor='white')
    fig.savefig(figures/f'{stem}.svg',bbox_inches='tight',facecolor='white')
    plt.close(fig)

def make(examples,figures):
    figures.mkdir(parents=True,exist_ok=True)
    tele=load(examples/'telemetry.csv');scores=load(examples/'replay_results.csv');rules=load(examples/'rules.csv')
    updated=load(examples/'rule_update_comparison.csv');tinc=load(examples/'tinc_samples.csv')
    rulemap={int(r['rule_id']):r for r in rules}

    # Reproducible scientific architecture, not a screenshot of a real gateway.
    fig,ax=plt.subplots(figsize=(11,4.6));fig.patch.set_facecolor('white');ax.set_xlim(0,12.5);ax.set_ylim(0,5);ax.axis('off')
    boxes=[(0.1,1.85,2.45,1.75,'Telemetric replay','50 sensor channels\nQuality / timestamp checks'),
           (3.0,1.85,2.5,1.75,'Edge C++ host','Validate units and bounds\nVersioned rule registry'),
           (5.95,1.85,2.55,1.75,'paceval engine','100 reusable graphs\nBatched formula evaluation'),
           (8.95,1.85,3.35,1.75,'Host-owned decisions','Persistence & hysteresis\nMonitoring output and audit')]
    for ix,(x,y,w,h,top,detail) in enumerate(boxes):
        color=CYAN if ix==2 else NAVY
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.16',fc=BG,ec=color,lw=2))
        ax.text(x+w/2,y+h*.68,top,ha='center',va='center',color=color,fontweight='bold',fontsize=12)
        ax.text(x+w/2,y+h*.32,detail,ha='center',va='center',fontsize=9.3,color=INK,linespacing=1.55)
        if ix<3:ax.annotate('',xy=(boxes[ix+1][0]-.08,2.7),xytext=(x+w+.08,2.7),arrowprops=dict(arrowstyle='-|>',lw=2.3,color=GREEN))
    ax.text(6.25,4.65,'Offline reproducible gateway mathematical pipeline',color=INK,ha='center',fontsize=17,fontweight='bold')
    ax.text(6.25,.92,'OPC UA / MQTT protocol adapters and hard real-time scheduling are NOT part of this prototype',ha='center',color=GRAY,fontsize=10)
    save(fig,figures,'01_gateway_architecture')

    fig,ax=axes()
    r17=[r for r in scores if int(r['rule_id'])==17]
    x=[int(r['tick']) for r in r17];valid=[float(r['score']) if r['score'] else float('nan') for r in r17]
    ax.plot(x,valid,color=CYAN,lw=2,label='Rule 17 · version 1.0')
    ax.plot([int(r['tick']) for r in updated],[float(r['updated_score']) if r['updated_score'] else float('nan') for r in updated],color=CORAL,lw=1.6,label='Rule 17 · updated version 1.1')
    ax.axhline(float(rulemap[17]['threshold']),ls='--',color=GRAY,label='Declared score threshold')
    ax.set(title='One pre-approved rule can be updated without changing the other 99',xlabel='Replay tick (100 ms synthetic cadence)',ylabel='Dimensionless rule score')
    ax.legend(loc='upper right',fontsize=9)
    save(fig,figures,'02_versioned_rule_update')

    counts=Counter(r['quality'] for r in tele)
    fig,ax=axes()
    keys=['GOOD','STALE','BAD','MISSING']; vals=[counts[k] for k in keys]
    bars=ax.bar(keys,vals,color=[GREEN,CYAN,CORAL,GRAY],width=.55)
    for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+35,str(v),ha='center',color=INK,fontweight='bold')
    ax.set(title='Input-quality screening precedes mathematical evaluation',ylabel='Telemetry measurements',ylim=(0,max(vals)*1.12))
    save(fig,figures,'03_input_quality')

    fig,ax=axes()
    families=['Weighted linear','Hyperbolic tangent','Quadratic severity','Cross-feature interaction']
    values=[[] for _ in range(4)]
    for r in scores:
        if r['score']:values[int(rulemap[int(r['rule_id'])]['family'])].append(float(r['score']))
    ax.boxplot(values,patch_artist=True,showfliers=False,boxprops={'facecolor':'#cde6f1','edgecolor':CYAN},medianprops={'color':CORAL,'linewidth':2})
    ax.set_xticklabels(families,rotation=15,ha='right')
    ax.set(title='Four mathematical model families across 100 rule versions',ylabel='Valid sample score (dimensionless)')
    save(fig,figures,'04_rule_family_scores')

    # A three-rule state heatmap: gray=invalid, pale blue=normal, orange=alert.
    from matplotlib.colors import ListedColormap
    chosen=[15,56,84]
    fig,ax=plt.subplots(figsize=(10.5,4.3));fig.patch.set_facecolor('white')
    matrix=[]
    for rid in chosen:
        series=[r for r in scores if int(r['rule_id'])==rid]
        matrix.append([0 if r['status']=='NO_DATA' else (2 if r['status']=='ALERT' else 1) for r in series])
    im=ax.imshow(matrix,aspect='auto',interpolation='nearest',cmap=ListedColormap(['#b9c2ca','#b7e6f2','#e89951']),vmin=0,vmax=2,extent=[0,240,2.5,-0.5])
    ax.set_yticks([0,1,2],labels=[f'Rule {rid}' for rid in chosen])
    ax.set(title='Real monitoring transitions for three selected rules',xlabel='Replay tick (100 ms synthetic cadence)')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor='#b9c2ca',label='NO_DATA'),Patch(facecolor='#b7e6f2',label='NORMAL'),Patch(facecolor='#e89951',label='ALERT')],loc='upper center',bbox_to_anchor=(.5,-.12),ncol=3,frameon=False)
    save(fig,figures,'05_monitoring_state')

    fig,ax=axes()
    from mpmath import mp
    mp.dps=85
    rule=rulemap[0]
    def m(z):return mp.mpf(z)
    lows=[];highs=[];points=[]
    for row in tinc:
        t=(m(row['T'])-70)/40;v=m(row['V'])/2;i=max(mp.mpf('0'),m(row['I'])-m(rule['current_limit_A']))/8
        ref=m(rule['w1'])*t+m(rule['w2'])*v+m(rule['w3'])*i
        lows.append(float((m(row['tinc_low'])-ref)*mp.mpf('1e17')))
        highs.append(float((m(row['tinc_high'])-ref)*mp.mpf('1e17')))
        points.append(float((m(row['paceval_value'])-ref)*mp.mpf('1e17')))
    k=np.arange(len(tinc))
    ax.vlines(k,lows,highs,color=CYAN,lw=2,label='TINC interval relative to reference')
    ax.scatter(k,points,s=25,color=GREEN,label='Returned paceval value',zorder=3)
    ax.axhline(0,color=CORAL,lw=1.6,ls='--',label='90-digit reference')
    ax.set(title='24 independently audited TINC samples (rule 0)',xlabel='Selected sample index',ylabel='Difference from reference (×10⁻¹⁷)')
    ax.legend(fontsize=9,loc='best')
    save(fig,figures,'06_tinc_reference_audit')

    fig,ax=axes()
    x=np.linspace(40,110,140);y=np.linspace(0,5,110)
    T,V=np.meshgrid(x,y);r=rulemap[0]
    # Fix current at the selected rule's threshold +1 A. Fully synthetic surface.
    excess=max(0,1.)/8
    Z=float(r['w1'])*(T-70)/40 + float(r['w2'])*(V/2)+float(r['w3'])*excess
    contours=ax.contourf(T,V,Z,levels=22,cmap='YlGnBu')
    fig.colorbar(contours,ax=ax,label='Dimensionless condition score')
    ax.contour(T,V,Z,levels=[float(r['threshold'])],colors=[CORAL],linewidths=2)
    ax.set(title='Synthetic response surface for one selected mathematical rule',xlabel='Temperature [°C]',ylabel='Vibration [mm/s]')
    save(fig,figures,'07_diagnostic_response_surface')
    print('Created 7 scientific figures from documented example data')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--examples',required=True);p.add_argument('--figures',required=True)
    a=p.parse_args();make(Path(a.examples),Path(a.figures))
