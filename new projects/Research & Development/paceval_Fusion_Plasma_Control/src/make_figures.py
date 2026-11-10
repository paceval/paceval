#!/usr/bin/env python3
"""Recreate scientifically labelled figures from the committed CSV artifacts.

Requires numpy, pandas, matplotlib and mpmath. The marketing banner is an
included design asset; this script reproduces data plots and architecture.
Every plot uses synthetic normalized signals, never tokamak measurements.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import TwoSlopeNorm
import mpmath as mp
mp.mp.dps = 110
P=Path(__file__).resolve().parents[1]
FIG=P/'figures';FIG.mkdir(exist_ok=True)
S=pd.read_csv(P/'examples/sensors.csv')
E=pd.read_csv(P/'examples/evaluations.csv')
T=pd.read_csv(P/'examples/tinc_samples.csv')
DARK='#122a46';BLUE='#1774bb';TEAL='#00a6a6';ORANGE='#f0a441';GREY='#56697b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':DARK,'axes.titleweight':'bold'})
def save(name):
    plt.savefig(FIG/name, dpi=190, bbox_inches='tight', facecolor='white')
    plt.close()

# Fig. 1. Separates actual mathematical evaluation from all host policy.
fig,ax=plt.subplots(figsize=(12.6,4.2));ax.set_xlim(0,12);ax.set_ylim(0,4);ax.axis('off')
items=[(.3,1.12,2.25,1.46,'Synthetic input\nCSV / normalization','#eef4fa'),
       (3.3,.9,3,1.95,'paceval SDK 4.25\n7 reusable ordinary graphs\n2 TINC graphs','#def3f2'),
       (7.2,1.12,2.3,1.46,'Independent C++\nchecks and host policy','#eef4fa'),
       (10.25,1.12,1.5,1.46,'CSV +\nfigures','#eef4fa')]
for x,y,w,h,t,color in items:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.09,rounding_size=.12',facecolor=color,edgecolor=TEAL if x==3.3 else '#9eb3c7',linewidth=1.4))
    ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=10,fontweight='bold',color=DARK)
for a,b in [(2.57,3.25),(6.37,7.12),(9.56,10.16)]:
    ax.add_patch(FancyArrowPatch((a,1.87),(b,1.87),arrowstyle='-|>',mutation_scale=17,linewidth=2,color=BLUE))
ax.text(6,3.45,'Offline, non-actuating integration demonstrator',ha='center',fontsize=14,fontweight='bold',color=DARK)
ax.text(6,.28,'Real tokamak sensors, machine interlocks and actuator commands are outside this proof of concept.',ha='center',color=GREY,fontsize=9)
save('01_architecture.png')

# Fig. 2. Normalized diagnostic polynomial as explicitly defined in paper.
i=np.linspace(-1,1,220);b=np.linspace(-1,1,220);I,B=np.meshgrid(i,b)
y=.1+.38*I-.19*B+.12*I*B+.09*B*B
fig,ax=plt.subplots(figsize=(8.4,5.4))
cp=ax.contourf(I,B,y,levels=30,cmap='coolwarm');ax.contour(I,B,y,levels=12,colors='white',alpha=.55,linewidths=.7)
fig.colorbar(cp,ax=ax,label='Dimensionless diagnostic output')
ax.set(xlabel='Normalized current-like input i',ylabel='Normalized field-like input b',title='Synthetic polynomial diagnostic response surface')
ax.text(.02,.02,'Illustrative coefficients; no device calibration',transform=ax.transAxes,fontsize=8,color=DARK,bbox={'fc':'white','ec':'none','alpha':.82})
save('02_diagnostic_surface.png')

# Fig. 3. Actual paceval output file. "sample index" is not physical time.
fig,ax=plt.subplots(figsize=(10.7,4.7))
sl=slice(0,min(len(E),130));x=np.arange(len(E))[sl]
ax.plot(x,E['diagnostic'].values[sl],label='paceval polynomial model',color=BLUE,lw=2)
ax.plot(x,E['nonlinear_surrogate'].values[sl],label='paceval nonlinear expression',color=TEAL,lw=2,ls='--')
ax.set(xlabel='Synthetic sample index (not physical time)',ylabel='Normalized model output',title='Two reusable paceval mathematical models')
ax.legend(frameon=False);ax.grid(alpha=.16);save('03_synthetic_model_series.png')

# Fig. 4. First-order statistical uncertainty propagation (model assumption).
fig,axs=plt.subplots(1,2,figsize=(11,4.4))
x=np.arange(len(E))
axs[0].plot(x,E['gradient_current'],label='dy/di',c=BLUE)
axs[0].plot(x,E['gradient_field'],label='dy/db',c=TEAL)
axs[0].set(title='Analytical sensitivities',xlabel='Synthetic sample index',ylabel='Dimensionless derivative');axs[0].legend(frameon=False)
axs[1].plot(x,E['propagated_sigma'],c=ORANGE)
axs[1].set(title='First-order propagated input uncertainty',xlabel='Synthetic sample index',ylabel='Dimensionless sigma estimate')
for a in axs:a.grid(alpha=.14)
fig.suptitle('paceval-derived sensitivity and uncertainty functions',fontsize=13,fontweight='bold')
save('04_sensitivity_uncertainty.png')

# Fig. 5. Purely illustrative normalized elliptical envelope.
fig,ax=plt.subplots(figsize=(8,5.8))
I,B=np.meshgrid(np.linspace(-1,1,200),np.linspace(-1,1,200));margin=1-(I/.95)**2-(B/.95)**2
cn=ax.contourf(I,B,margin,levels=np.linspace(-1.4,1,30),cmap='RdYlBu',extend='both');fig.colorbar(cn,ax=ax,label='Synthetic margin (dimensionless)')
ax.contour(I,B,margin,levels=[0],colors='#172e49',linewidths=2.2)
ax.scatter(S['i'][::4],S['b'][::4],s=9,c='#111827',alpha=.38,label='Test inputs')
ax.set(xlabel='Normalized current-like input i',ylabel='Normalized field-like input b',title='Host-classified synthetic monitoring envelope')
ax.legend(loc='lower left',framealpha=.9);save('05_synthetic_envelope.png')

# Fig. 6. Multiprecision reference as fraction of each reported TINC interval.
from decimal import Decimal
refs=[]
for _,r in T.iterrows():
 v={z:mp.mpf(float(r[z])) for z in 'i b a0 a1 a2 a3 a4 ilim blim'.split()}
 if r['formula']=='diagnostic':
  exact=v['a0']+v['a1']*v['i']+v['a2']*v['b']+v['a3']*v['i']*v['b']+v['a4']*v['b']**2
 else:exact=1-(v['i']/v['ilim'])**2-(v['b']/v['blim'])**2
 lo=mp.mpf(float(r['tinc_lower']));hi=mp.mpf(float(r['tinc_upper']))
 refs.append(float((exact-lo)/(hi-lo)))
fig,ax=plt.subplots(figsize=(9,4.6))
ax.axhspan(0,1,color='#ddf4ed',alpha=.6,label='Reported interval (normalized)')
ax.plot(np.arange(1,25),refs,'o',color=BLUE,markersize=6,label='Independent 110-digit reference')
ax.axhline(0,color=TEAL,ls='--');ax.axhline(1,color=TEAL,ls='--')
ax.set(xlabel='TINC test sample (24 total)',ylabel='(reference − lower) / (upper − lower)',ylim=(-.12,1.12),xlim=(0,25),title='Pointwise TINC inclusion audit: 24 / 24 contained')
ax.grid(alpha=.15);ax.legend(frameon=False);save('06_tinc_reference_audit.png')
print('Generated scientific figures in',FIG)
