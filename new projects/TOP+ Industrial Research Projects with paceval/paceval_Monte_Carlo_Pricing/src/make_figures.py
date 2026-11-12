#!/usr/bin/env python3
"""Recreate all scientific PNG/SVG figures from the published CSV examples."""
import argparse
import csv
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from mpmath import mp

mp.dps=70
p=argparse.ArgumentParser();p.add_argument('--examples',default='examples');p.add_argument('--figures',default='figures');args=p.parse_args()
ex=Path(args.examples); out=Path(args.figures);out.mkdir(parents=True,exist_ok=True)
BLUE='#17609e'; TEAL='#00a8ad'; GREEN='#139d80'; ORANGE='#ee9b31'; DARK='#193853'; GREY='#64778a'
plt.rcParams.update({'figure.figsize':(9.2,4.9),'font.size':10.4,'axes.titlesize':13.5,'axes.labelsize':10.5,
 'axes.edgecolor':'#bcccd9','axes.labelcolor':DARK,'text.color':DARK,'xtick.color':DARK,'ytick.color':DARK,
 'grid.color':'#d9e4eb','grid.alpha':0.7,'axes.spines.top':False,'axes.spines.right':False})
def load(name):return list(csv.DictReader((ex/name).open(newline='')))
def save(name,fig):
 fig.tight_layout(pad=1.45)
 for ext in ('png','svg'):fig.savefig(out/f'{name}.{ext}',dpi=170,bbox_inches='tight',facecolor='white')
 plt.close(fig)

# Architecture chart, rendered without external Graphviz dependency for easy regeneration.
fig,ax=plt.subplots(figsize=(10,4.4));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
boxes=[('Deterministic GBM\n+ antithetic paths',.05,'#e6f2f7'),('Path features\nST, average, maximum',2.65,'#e6f2f7'),('paceval reusable\npayoff graphs',5.25,'#d6f6ed'),('Host pricing\n+ validation',7.85,'#e6f2f7')]
for label,x,col in boxes:
 from matplotlib.patches import FancyBboxPatch
 box=FancyBboxPatch((x,1.55),2.05,.95,boxstyle='round,pad=0.1',fc=col,ec=TEAL if 'paceval' in label else BLUE,lw=1.6)
 ax.add_patch(box);ax.text(x+1.025,2.02,label,ha='center',va='center',weight='bold',fontsize=10)
for x in [2.25,4.85,7.45]:ax.annotate('',xy=(x+.37,2.02),xytext=(x,2.02),arrowprops={'arrowstyle':'-|>','lw':2,'color':TEAL})
ax.text(5.05,.7,'five compiled formulas  |  100 parameterized contracts  |  batch evaluations',ha='center',size=11,color=DARK)
ax.set_title('What paceval executes vs. what the C++ host owns',pad=16,fontweight='bold');save('01_architecture',fig)

# Piecewise terminal-payoff cross-section: actual payoff formulas at fixed r,T.
st=np.linspace(60,150,400);k=100.;cap=12.;discount=np.exp(-.03)
fig,ax=plt.subplots();ax.plot(st,discount*np.maximum(st-k,0),label='European call',color=BLUE,lw=2)
ax.plot(st,discount*np.maximum(k-st,0),label='European put',color=ORANGE,lw=2)
ax.plot(st,discount*np.minimum(np.maximum(st-k,0),cap),label='Capped call',color=GREEN,lw=2)
ax.axvline(k,ls='--',lw=1,color=GREY);ax.text(k+1,25,'Strike = 100',size=9,color=GREY)
ax.set(title='Discounted payoff profiles for three terminal-price contracts',xlabel='Terminal asset value',ylabel='Discounted payoff',ylim=(-1,52));ax.grid(True);ax.legend();save('02_payoff_profiles',fig)

paths=load('path_samples.csv');st=np.array([float(d['terminal_price']) for d in paths]);av=np.array([float(d['arithmetic_average']) for d in paths])
fig,ax=plt.subplots();ax.scatter(st[::2],st[1::2],s=29,c=TEAL,alpha=.77,ec='none');ax.plot(np.linspace(60,160,250),(100**2*np.exp(2*(0.03-0.5*0.2**2)))/np.linspace(60,160,250),color=GREY,ls=':',lw=1,label='Antithetic GBM terminal-value identity')
ax.set(title='Antithetic terminal prices from paired Monte Carlo paths',xlabel='Terminal value of +Z trajectory',ylabel='Terminal value of -Z trajectory');ax.grid(True);save('03_antithetic_paths',fig)

prices=load('prices.csv');eur=[d for d in prices if d['analytic_price']!='NA'];xs=np.array([int(d['contract_id']) for d in eur]);delta=np.array([float(d['analytic_difference']) for d in eur]);se=np.array([float(d['antithetic_pair_se']) for d in eur]);colors=[BLUE if d['family']=='european_call' else ORANGE for d in eur]
fig,ax=plt.subplots();ax.errorbar(xs,delta,yerr=1.96*se,fmt='none',ecolor='#b0bfca',elinewidth=1.3,capsize=2,zorder=1);ax.scatter(xs,delta,c=colors,s=26,zorder=2)
ax.axhline(0,color=GREY,ls='--');ax.grid(True);ax.set(title='European option prices vs. analytic Black-Scholes reference',xlabel='Contract ID (call: blue, put: amber)',ylabel='Monte Carlo minus analytic price');save('04_black_scholes_agreement',fig)

names=['european_call','european_put','capped_call','asian_call','lookback_call']
amounts=[[float(d['paceval_price']) for d in prices if d['family']==name] for name in names]
fig,ax=plt.subplots();bx=ax.boxplot(amounts,patch_artist=True,showfliers=False,tick_labels=['Call','Put','Capped call','Asian call','Lookback call']);
for patch,color in zip(bx['boxes'],[BLUE,ORANGE,GREEN,TEAL,'#636bb0']):patch.set_facecolor(color);patch.set_alpha(.43)
ax.grid(axis='y');ax.set(title='100 synthetic contract variations across five payoff families',ylabel='Monte Carlo model value',xlabel='Contract family');save('05_contract_variations',fig)

checks=load('payoff_audit.csv');errors=[]
for row in checks:
 vals={k:mp.mpf(float(row[k])) for k in ['terminal_price','arithmetic_average','observed_maximum','strike','cap','rate','time']}
 d=mp.exp(-vals['rate']*vals['time']);S=vals['terminal_price'];A=vals['arithmetic_average'];M=vals['observed_maximum'];K=vals['strike'];cap=vals['cap'];name=row['family'];pos=lambda z:max(0,z)
 true={'european_call':lambda:pos(S-K)*d,'european_put':lambda:pos(K-S)*d,'capped_call':lambda:(pos(S-K)-pos(S-K-cap))*d,'asian_call':lambda:pos(A-K)*d,'lookback_call':lambda:pos(M-K)*d}[name]()
 errors.append(float(abs(true-mp.mpf(float(row['paceval_payoff'])))))
fig,ax=plt.subplots();ax.hist([max(e,1e-18) for e in errors],bins=np.logspace(-18,-13,26),color=BLUE,edgecolor='white');ax.set_xscale('log');ax.set(title='100-decimal independent audit of 300 payoff samples',xlabel='Absolute difference to high-precision reference',ylabel='Sample count');ax.grid(axis='y');save('06_high_precision_audit',fig)

update=load('model_update.csv');ids=np.array([int(d['path_id']) for d in update]);old=np.array([float(d['old_payoff']) for d in update]);new=np.array([float(d['new_payoff']) for d in update]);
fig,ax=plt.subplots();ax.plot(ids,old,'o-',label='Original approved contract',color=BLUE);ax.plot(ids,new,'s--',label='Updated strike, same paceval graph',color=GREEN)
ax.set(title='Contract version update: strike changes, graph is reused',xlabel='Path sample ID',ylabel='Discounted call payoff');ax.grid(True);ax.legend();save('07_contract_update',fig)

r=load('tinc_samples.csv');width=np.array([float(d['upper'])-float(d['lower']) for d in r]);fig,ax=plt.subplots();ax.bar(range(len(width)),width,color=TEAL)
ax.set(title='TINC numerical intervals: discounted terminal-value kernel',xlabel='Sample',ylabel='Reported interval width');ax.grid(axis='y');ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0));save('08_tinc_intervals',fig)
print('Generated 8 scientific diagrams in PNG and SVG.')
