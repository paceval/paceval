#!/usr/bin/env python3
"""Rebuild numbered scientific figures from C++/paceval exported CSV only."""
from pathlib import Path
import csv, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import TwoSlopeNorm

def rows(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
ROOT=Path(__file__).resolve().parents[1]; EX=ROOT/'examples'; OUT=ROOT/'figures'; OUT.mkdir(exist_ok=True)
state=rows(EX/'indicator_states.csv');score=rows(EX/'score_results.csv');ver=rows(EX/'version_comparison.csv');surface=rows(EX/'score_surface.csv')
t=np.array([int(x['bar']) for x in state]);price=np.array([float(x['price']) for x in state]);ema=np.array([float(x['ema20']) for x in state]);rsi=np.array([float(x['rsi14']) for x in state]);hist=np.array([float(x['macd'])-float(x['signal']) for x in state]);vol=np.array([float(x['realized_vol20']) for x in state]);
S=np.array([float(x['score_paceval']) for x in score]).reshape(len(t),128)
C='#0e2037'; BLUE='#0b77ac';ORANGE='#ef773f';GREEN='#008b77';
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','figure.facecolor':'white'})
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=190,bbox_inches='tight',pad_inches=.16)
 fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.16)
 plt.close(fig)
# Workflow: diagram not from numerical data, but grounded architecture labels.
fig,ax=plt.subplots(figsize=(12.6,2.9));ax.set(xlim=(0,12),ylim=(0,2));ax.axis('off')
items=[('Causal synthetic\nclose series',.2),('paceval EMA\nRSI / MACD features',2.7),('128 versioned\nscore graphs',5.2),('Native + 80-digit\nindependent audit',7.7),('PNG / PDF\nreport figures',10.2)]
from matplotlib.patches import FancyBboxPatch
for n,(label,x) in enumerate(items):
 ax.add_patch(FancyBboxPatch((x,.67),1.75,.75,boxstyle='round,pad=0.1,rounding_size=.12',facecolor='#eaf2f7',edgecolor=BLUE,lw=1.8));ax.text(x+.875,1.045,label,ha='center',va='center',fontsize=9,color=C,fontweight='bold')
 if n<4:ax.annotate('',xy=(x+2.35,1.045),xytext=(x+1.86,1.045),arrowprops=dict(arrowstyle='-|>',lw=1.8,color=ORANGE))
ax.text(6,.18,'Host controls state, input order, warm-up, formula IDs and verification; paceval evaluates expression graphs.',ha='center',fontsize=9,color='#586a78')
save(fig,'01_execution_architecture')
fig,ax=plt.subplots(figsize=(10.8,4.7));ax.plot(t,price,label='Synthetic closing price',c=BLUE,lw=1.6);ax.plot(t,ema,label='paceval EMA(20)',c=ORANGE,lw=1.7);ax.set(xlabel='Synthetic bar index',ylabel='Arbitrary price units',title='Sequential close prices and reusable paceval EMA updates');ax.legend(frameon=False);ax.grid(alpha=.16);save(fig,'02_price_and_ema')
fig,ax=plt.subplots(figsize=(10.8,4.8));ax.plot(t,rsi,c=BLUE,lw=1.5,label='RSI(14), Wilder smoothing');ax.axhline(70,c=ORANGE,ls='--',lw=1);ax.axhline(30,c=GREEN,ls='--',lw=1);ax.set(xlabel='Bar index',ylabel='RSI index [0, 100]',title='Causal RSI state: values from paceval smoothing graphs');ax.grid(alpha=.16);ax2=ax.twinx();ax2.plot(t,hist,color='#9981bb',alpha=.65,lw=1,label='MACD histogram');ax2.set_ylabel('MACD histogram (price units)');save(fig,'03_rsi_macd')
fig,ax=plt.subplots(figsize=(10.8,4.7));
for id,c in [(0,BLUE),(31,ORANGE),(63,GREEN),(95,'#8a68a9'),(127,'#c64a69')]:ax.plot(t,S[:,id],label=f'Model {id:03d}',lw=1.4,color=c)
ax.set(title='Interchangeable, versioned paceval score kernels',xlabel='Bar index',ylabel='Bounded mathematical score [0,1]',ylim=(0,1));ax.grid(alpha=.14);ax.legend(ncol=5,fontsize=9,frameon=False,loc='upper center');save(fig,'04_five_score_models')
fig,ax=plt.subplots(figsize=(11,4.7));im=ax.imshow(S.T,aspect='auto',origin='lower',extent=(t[0],t[-1],0,127),cmap='coolwarm',vmin=0,vmax=1);fig.colorbar(im,ax=ax,label='paceval score [0, 1]');ax.set(title='All 128 candidate models, every causally evaluated bar',xlabel='Bar index',ylabel='Formula ID');save(fig,'05_score_family_map')
M=np.array([float(x['momentum_scaled']) for x in surface]).reshape(61,61);Q=np.array([float(x['rsi_centered']) for x in surface]).reshape(61,61);Z=np.array([float(x['score_paceval']) for x in surface]).reshape(61,61)
fig=plt.figure(figsize=(10.7,6.0));ax=fig.add_subplot(projection='3d');ax.plot_surface(M,Q,Z,cmap='coolwarm',edgecolor='none',alpha=.97,antialiased=True);ax.set(xlabel='Scaled EMA momentum',ylabel='Centered RSI',zlabel='Score [0,1]',title='Actual paceval evaluations: controlled two-feature score surface');ax.view_init(26,-62);save(fig,'06_score_response_surface')
v1=np.array([float(x['score_v1']) for x in ver]);v2=np.array([float(x['score_v2']) for x in ver]);fig,ax=plt.subplots(figsize=(10.8,4.7));ax.plot(t,v1,c=BLUE,label='Original score formula v1');ax.plot(t,v2,c=ORANGE,label='Updated coefficients v2',ls='--');ax.set(xlabel='Bar index',ylabel='Bounded score',title='Controlled version update: original graph remains available');ax.grid(alpha=.14);ax.legend(frameon=False);save(fig,'07_controlled_model_update')
errors=np.array([float(x['abs_difference']) for x in score]);fig,ax=plt.subplots(figsize=(10,4.5));ax.hist(np.maximum(errors,1e-18),bins=np.logspace(-18,-14,22),color=BLUE,edgecolor='white');ax.set(xscale='log',xlabel='Absolute |paceval − separate native C++|',ylabel='Number of score evaluations',title='Arithmetic agreement across 48,640 paceval score results');ax.grid(alpha=.14);save(fig,'08_numerical_audit')
print('Created eight scientific figures in PNG and vector PDF')
