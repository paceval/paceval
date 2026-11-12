#!/usr/bin/env python3
"""Generate scientific illustrations exclusively from packaged reproducible data."""
from pathlib import Path
import csv
import math
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from collections import Counter

root=Path(__file__).resolve().parents[1]
ex=root/'examples'; dest=root/'figures';dest.mkdir(exist_ok=True)
blue='#164d7a'; teal='#009fa7'; orange='#df9122'; green='#17846c'; charcoal='#203341'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})

def rows(name):
    with (ex/name).open(newline='') as f:return list(csv.DictReader(f))

def save(fig,name):
    fig.savefig(dest/(name+'.png'),dpi=180,bbox_inches='tight',pad_inches=.18)
    fig.savefig(dest/(name+'.svg'),bbox_inches='tight',pad_inches=.18)
    plt.close(fig)

# 1. Architecture: actual source/host/API separation rather than a false hardware claim.
fig,ax=plt.subplots(figsize=(11,3.6)); ax.set_xlim(0,12);ax.set_ylim(0,4);ax.axis('off')
boxes=[(0.1,'Versioned\nformula catalog'),(3.1,'C++ host\nvalidation and lifecycle'),(6.1,'paceval\nexecution graphs'),(9.1,'Native reference +\n100-digit audit')]
for j,(x,label) in enumerate(boxes):
    fc='#e7f0f7' if j!=2 else '#d6f3f0'
    ax.add_patch(FancyBboxPatch((x,1.35),2.8,1.45,boxstyle='round,pad=0.12',edgecolor=teal if j==2 else blue,facecolor=fc,linewidth=1.7))
    ax.text(x+1.4,2.07,label,ha='center',va='center',fontsize=10.2,color=charcoal,weight='bold')
    if j<3: ax.annotate('',xy=(x+3.07,2.07),xytext=(x+2.8,2.07),arrowprops={'arrowstyle':'->','lw':2,'color':teal})
ax.text(6.0,0.65,'Input bounds, formula approval, model updates and output reporting are host responsibilities',ha='center',fontsize=9,color=charcoal)
ax.set_title('A reproducible on-device mathematical execution component',fontsize=13,color=charcoal,pad=8)
save(fig,'01_reusable_runtime_architecture')

# 2. Repeated evaluation of one model per mathematical family.
evaluations=rows('evaluations.csv')
fig,ax=plt.subplots(figsize=(9.5,4.6))
names=['Damped wave','Rational + cosine','Polynomial + decay','Tanh + sine','Logarithm + root']
for family,name in enumerate(names):
    selected=[r for r in evaluations if int(r['model_id'])==family]
    ax.plot([float(r['x']) for r in selected],[float(r['paceval_value']) for r in selected],lw=2,label=name)
ax.set_title('Five formula families evaluated with reusable paceval graphs',color=charcoal)
ax.set_xlabel('Bounded input x (dimensionless)');ax.set_ylabel('Expression value (dimensionless)')
ax.legend(ncols=2,fontsize=8,loc='upper left');ax.grid(alpha=.18)
save(fig,'02_mathematical_families')

# 3. Model catalog: actual 1,000 distinct graphs; no latency claims.
models=rows('models.csv'); counts=Counter(int(r['family']) for r in models)
fig,ax=plt.subplots(figsize=(8.4,4.2));bars=ax.bar(names,[counts[i] for i in range(5)],color=[blue,teal,green,orange,'#6f86ae'])
ax.bar_label(bars,padding=3,fontsize=9);ax.set_ylim(0,240)
ax.set_ylabel('Number of approved formula versions');ax.set_title('Actual versioned catalog used in the full run',color=charcoal)
ax.tick_params(axis='x',labelrotation=12);ax.grid(axis='y',alpha=.2)
save(fig,'03_formula_catalog')

# 4. Independent precision audit with its own arbitrary-precision implementation.
audit=rows('high_precision_audit_samples.csv')
fig,ax=plt.subplots(figsize=(9.2,4.6))
for fam in range(5):
    rr=[r for r in audit if int(r['family'])==fam]
    ax.scatter([int(r['model_id']) for r in rr],[max(float(r['absolute_error']),1e-20) for r in rr],s=12,label=names[fam],alpha=.75)
ax.set_yscale('log');ax.set_xlabel('Model ID');ax.set_ylabel('Absolute error vs independent 100-digit oracle')
ax.set_title('High-precision check of selected published values',color=charcoal)
ax.grid(alpha=.17);ax.legend(ncols=2,fontsize=8)
save(fig,'04_high_precision_audit')

# 5. One version's controlled update. Both scores are validated by the C++ implementation.
updates=rows('model_update.csv')
fig,ax=plt.subplots(figsize=(9,4.3));samples=[int(r['sample']) for r in updates]
ax.plot(samples,[float(r['previous_score']) for r in updates],label='Version 1',lw=2,color=blue)
ax.plot(samples,[float(r['updated_score']) for r in updates],label='Version 2',lw=2,color=green)
ax.set_xlabel('Input sample');ax.set_ylabel('Mathematical result')
ax.set_title('An approved model update affects only the selected version',color=charcoal)
ax.legend();ax.grid(alpha=.2)
save(fig,'05_formula_version_update')

# 6. Measured interval widths. Inclusion is verified by independent Python check.
tinc=rows('tinc_samples.csv')
fig,ax=plt.subplots(figsize=(9,4.3));ss=[int(r['sample']) for r in tinc];widths=[float(r['upper'])-float(r['lower']) for r in tinc]
ax.plot(ss,widths,'o-',lw=1.5,color=teal)
ax.set_xlabel('Audit sample');ax.set_ylabel('Reported TINC width')
ax.set_title('Pointwise TINC interval widths (24 sampled inputs)',color=charcoal)
ax.grid(alpha=.2)
save(fig,'06_tinc_sample_widths')

# 7. Same graph, multiple bounded inputs: distinct from new formula creation.
fig,ax=plt.subplots(figsize=(9.5,3.7));xx=[float(r['x']) for r in evaluations if r['model_id']=='0']
ax.plot(range(len(xx)),xx,'o-',color=blue,label='Input x')
ax.set_ylabel('Value of x');ax.set_xlabel('Evaluation index');ax.set_title('Reusing an existing computation object across input values',color=charcoal)
ax.grid(alpha=.2)
save(fig,'07_repeated_input_sweep')
print('Generated 7 figures (PNG + SVG)')
