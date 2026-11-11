#!/usr/bin/env python3
"""Regenerate the scientific figures from included CSV data (no speed plots)."""
import csv
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
with (ROOT/'examples/batch_results.csv').open(newline='') as f:
    rows=list(csv.DictReader(f))

def chart_style():
    plt.rcParams.update({'figure.facecolor':'white','axes.facecolor':'white',
      'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,
      'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False})
chart_style()
navy='#0D2842';cyan='#0F98C9'; orange='#ED8C36'; teal='#168779'

def save(name):
    plt.savefig(OUT/name,dpi=190,bbox_inches='tight',facecolor='white')
    plt.close()

# 1. scientific system architecture
fig,ax=plt.subplots(figsize=(12,4.4))
ax.set_xlim(0,12);ax.set_ylim(0,4.4);ax.axis('off')
blocks=[(.3,'Workflow triggers','n8n / inputs'),(2.9,'Input contract','units / versions'),
        (5.5,'paceval graphs','reusable math'),(8.1,'Decisions','n8n / host'),
        (10.2,'Audited output','CSV / reports')]
for idx,(x,title,sub) in enumerate(blocks):
    w=2.1 if idx<4 else 1.6
    patch=FancyBboxPatch((x,2),w,1.2,boxstyle='round,pad=.12',fc='#EAF3F9',ec=cyan,lw=1.6)
    ax.add_patch(patch)
    ax.text(x+w/2,2.73,title,ha='center',weight='bold',color=navy,fontsize=10)
    ax.text(x+w/2,2.37,sub,ha='center',color='#47677C',fontsize=8)
    if idx<4:ax.annotate('',xy=(x+w+.37,2.6),xytext=(x+w+.03,2.6),arrowprops={'arrowstyle':'->','lw':2,'color':teal})
ax.text(6.55,1.15,'Approved condition v1.0  |  condition v1.1  |  quotation v1.0  |  calibration v1.0',
        ha='center',color=navy,fontsize=10)
ax.text(6.55,.62,'Mathematical execution belongs to paceval; workflow orchestration and domain decisions stay outside.',
        ha='center',color='#47677C',fontsize=9)
ax.set_title('Integration boundary: reusable mathematical models in low-code automation',color=navy,pad=14)
save('01_architecture.png')

# 2. surface and contour
x=np.linspace(-1,1,160);y=np.linspace(-1,1,150)
X,Y=np.meshgrid(x,y)
score=1/(1+np.exp(-(-.4+1.5*X+.8*Y)))
fig,ax=plt.subplots(figsize=(8,5.3))
im=ax.contourf(X,Y,score,30,cmap='viridis',vmin=0,vmax=1)
ax.contour(X,Y,score,levels=[.4,.6,.8],colors='white',linewidths=.9)
plt.colorbar(im,ax=ax,label='Illustrative condition score')
ax.set(xlabel='Normalized temperature deviation',ylabel='Normalized vibration severity',
       title='Approved condition-scoring model v1.0 (synthetic coefficients)')
save('02_condition_surface.png')

# 3. quote scenario curve
fig,ax=plt.subplots(figsize=(8.6,4.9))
t=np.linspace(0,20,200)
for r,c in [(.01,cyan),(.03,teal),(.05,orange)]:
    q=1000*1.2*(1+r)**t+20
    ax.plot(t,q,lw=2.2,color=c,label=f'Escalation rate {r:.0%}')
ax.set(xlabel='Term t (years)',ylabel='Illustrative quote amount (arbitrary units)',
       title='Versioned quotation: parameter scenarios')
ax.legend(frameon=False);ax.grid(alpha=.15)
save('03_quotation_scenarios.png')

# 4. calibration
fig,ax=plt.subplots(figsize=(8.6,4.9))
raw=np.linspace(-20,180,250)
for h,c in [(0,cyan),(25,teal),(80,orange)]:
    corrected=raw+1+.01*raw+.0001*raw*raw+.5*np.log1p(h)
    ax.plot(raw,corrected,lw=2.2,label=f'h = {h}',color=c)
ax.plot(raw,raw,ls=':',c='#687F8B',label='Uncorrected',lw=1.6)
ax.set(xlabel='Raw sensor value T',ylabel='Corrected output',title='Approved calibration model (synthetic curve)')
ax.legend(frameon=False);ax.grid(alpha=.15)
save('04_calibration_curves.png')

# 5. exact numerical error by model
fig,ax=plt.subplots(figsize=(9,4.7))
models=[('condition_score','1.0'),('condition_score','1.1'),('quotation','1.0'),('calibration','1.0')]
for idx,(model,version) in enumerate(models):
    subset=[float(r['abs_error']) for r in rows if r['model']==model and r['version']==version]
    # small epsilon only for plotting zero without claiming a nonzero error
    ax.scatter(np.arange(len(subset))+idx*82,[max(e,1e-18) for e in subset],s=10,
               label=f'{model} {version}',alpha=.65)
ax.set_yscale('log');ax.set_ylim(1e-19,1e-9)
ax.set(xlabel='Verification sample index by model',ylabel='Absolute difference vs native C++ (log scale)',
       title='Observed numerical agreement with independently coded C++ formulas')
ax.grid(alpha=.15,axis='y');ax.legend(frameon=False,fontsize=9)
ax.text(.01,.05,'Zero differences are plotted at 10⁻¹⁸ solely for visualization.',
        transform=ax.transAxes,fontsize=8,color='#587080')
save('05_native_validation.png')

# 6. live model version separation
fig,ax=plt.subplots(figsize=(8.7,4.9))
U=np.linspace(-1,1,200)
base=1/(1+np.exp(-(-.4+1.5*U+.8*.6)))
updated=1/(1+np.exp(-(-.4+1.5*U+.8*.6+.05*U*.6)))
ax.plot(U,base,label='condition_score v1.0',color=cyan,lw=2.5)
ax.plot(U,updated,label='condition_score v1.1',color=orange,lw=2.5)
ax.set(xlabel='Normalized temperature deviation uT',ylabel='Condition score',
       title='Version-specific execution graphs for centrally managed models')
ax.grid(alpha=.15);ax.legend(frameon=False)
save('06_model_versioning.png')

# 7. TINC sampled bounds and point values
with (ROOT/'examples/tinc_samples.csv').open(newline='') as f:
    tinc=list(csv.DictReader(f))
indices=np.arange(len(tinc))
values=np.array([float(r['result']) for r in tinc]);lo=np.array([float(r['lower']) for r in tinc]);hi=np.array([float(r['upper']) for r in tinc])
fig,ax=plt.subplots(figsize=(9,4.6))
ax.plot(indices,values,'o-',color=cyan,markersize=4,label='paceval value')
# Actual bounds narrower than visible on the score axis; indicate via inset text.
ax.fill_between(indices,lo,hi,color=orange,alpha=.3,label='paceval TINC bounds')
ax.set(xlabel='Independent sample number',ylabel='Condition score',
       title='24 pointwise TINC outputs: high-precision containment checked separately')
ax.grid(alpha=.14);ax.legend(frameon=False)
ax.text(.02,.04,'Intervals are narrower than the plotting resolution.',
        transform=ax.transAxes,color='#587080',fontsize=8)
save('07_tinc_samples.png')
print('Generated 7 scientific figures')
