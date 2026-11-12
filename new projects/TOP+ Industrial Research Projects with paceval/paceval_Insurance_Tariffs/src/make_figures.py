#!/usr/bin/env python3
"""Rebuild publication plots from the actual exported synthetic CSV files.

This script never invents measurements.  It reads the C++ example files and
uses Matplotlib in noninteractive mode; both PNG and SVG are reproducible.
"""
import csv, math
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
EX=ROOT/'examples'; OUT=ROOT/'figures'; OUT.mkdir(exist_ok=True)
def rows(name):
    with (EX/name).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))
MODELS=rows('models.csv');PREMIUMS=rows('premiums.csv');POLICIES=rows('policies.csv')
STATS=rows('model_summary.csv');UPDATES=rows('model_update.csv');TINC=rows('tinc_samples.csv')

def save(i,name):
    plt.tight_layout(pad=1.6)
    for suffix in ('png','svg'):
        plt.savefig(OUT/f'{i:02d}_{name}.{suffix}',dpi=160,bbox_inches='tight')
    plt.close()

def title(t,sub=''):
    plt.title(t,fontsize=14,weight='bold',pad=12)
    if sub:plt.gca().text(0,-0.16,sub,transform=plt.gca().transAxes,fontsize=8,color='#555555')

# 1: fixed workflow, faithfully identifies execution boundaries.
fig,ax=plt.subplots(figsize=(11.2,3.2));ax.set(xlim=(0,12),ylim=(0,3));ax.axis('off')
boxes=[(0.4,'Synthetic policy\nrecords'),(3.2,'Input checks +\nmodel versioning'),(6.0,'paceval\nexecution graphs'),(8.8,'Native / 100-digit\nnumerical audit')]
for x,label in boxes:
    rect=plt.Rectangle((x,1.12),2.55,1.24,fill=False,lw=1.8);ax.add_patch(rect)
    ax.text(x+1.275,1.74,label,ha='center',va='center',fontsize=10,weight='semibold')
for x in (2.95,5.75,8.55):ax.annotate('',xy=(x+.23,1.74),xytext=(x-.08,1.74),arrowprops={'arrowstyle':'->','lw':2})
ax.text(6.0,.38,'The C++ host manages records and audit controls; paceval evaluates mathematical premium expressions.',ha='center',fontsize=9)
ax.text(6,2.8,'REPRODUCIBLE RESEARCH ARCHITECTURE',ha='center',fontsize=15,weight='bold')
save(1,'research_workflow')

# 2: exact synthetic model family structures shown as curves vs asset age.
fig,ax=plt.subplots(figsize=(9.5,4.5))
models={int(m['family']):m for m in MODELS if int(m['model_id'])<4}
ages=np.arange(0,26)
def mval(m,age):
    b,a,c,d,g,h,f=(float(m[k]) for k in ('base','a','c','m','g','h','f'))
    cl,km,cv,exc=1,12,2,0.5;family=int(m['family'])
    if family==0:return b*(1+a*age)*(1+c*cl)
    if family==1:return b*(1+a*age)*(1+c*cl)*(1+d*(km-12)/12)*(1+g*(cv-1))
    if family==2:return b*(1+a*age)*(1+c*cl)*(1+g*(cv-1))*math.exp(d*(km-12)/12)/(1+h*exc)
    return b*(1+a*age+c*cl+d*km/12+g*(cv-1)+f*age*cl)/(1+h*exc)
for family,m in sorted(models.items()):ax.plot(ages,[mval(m,a) for a in ages],label=f'Family {family+1} (model {m["model_id"]})',lw=1.8)
ax.set(xlabel='Insured asset age (years)',ylabel='Illustrative premium (EUR)');ax.grid(alpha=.25);ax.legend(fontsize=9)
title('Four explicitly programmed synthetic tariff families')
save(2,'mathematical_families')

# 3: one actual model's histogram, without fabricated ratings or real claims.
vals=[float(r['premium_eur']) for r in PREMIUMS if r['model_id']=='1']
fig,ax=plt.subplots(figsize=(9.4,4.3));ax.hist(vals,bins=32,edgecolor='white',linewidth=.7)
ax.set(xlabel='Illustrative annual premium (EUR)',ylabel='Number of synthetic policy records')
ax.grid(alpha=.2,axis='y');title('Actual premium distribution: formula version 1 (model 1)')
save(3,'premium_distribution')

# 4: true absolute differences; the native reference is algebraically matched.
err=np.array([float(r['abs_difference']) for r in PREMIUMS]);fig,ax=plt.subplots(figsize=(9.4,3.8))
ax.bar(['Within tolerance','Outside tolerance'],[int((err<=2e-10).sum()),int((err>2e-10).sum())])
ax.set(ylabel='Number of evaluated premiums');ax.grid(alpha=.25,axis='y')
ax.text(0,len(err)*.52,f'Observed max native difference:\n{err.max():.3g} EUR',ha='center',fontsize=11)
title('Direct independent C++ comparison, all 100 formula versions')
save(4,'native_validation')

# 5: version update from exported record.
fig,ax=plt.subplots(figsize=(9.4,4.2))
x=np.arange(len(UPDATES));old=np.array([float(z['old_premium']) for z in UPDATES]);new=np.array([float(z['new_premium']) for z in UPDATES]);
ax.plot(x,old,label='Model 17 / v1',linewidth=1.5);ax.plot(x,new,label='Model 17 / v2',linewidth=1.5)
ax.set(xlabel='Synthetic policy ID',ylabel='Annual premium (EUR)');ax.grid(alpha=.25);ax.legend()
title('Controlled update: only model 17 is recreated',"Illustrative change to its base tariff; no other computation handles are replaced")
save(5,'version_change')

# 6: direct paired counterfactual on a variable excluded from all formulas.
fig,ax=plt.subplots(figsize=(9.4,4.2));x=[int(r['model_id']) for r in STATS]
y=[float(r['max_tag_pair_difference']) for r in STATS];ax.plot(x,y,'o',markersize=3)
ax.set(xlabel='Tariff model ID',ylabel='Maximum absolute difference (EUR)',ylim=(-0.2,1));ax.grid(alpha=.25)
title('Non-rating tag invariance for all 100 synthetic tariff models',"Each of 512 rating vectors appears with tag 0 and tag 1; this is not a complete fairness assessment")
save(6,'paired_tag_invariance')

# 7: tariff versions across four model families, actual mean values.
fig,ax=plt.subplots(figsize=(9.4,4.4));names=['Family 1','Family 2','Family 3','Family 4'];means=defaultdict(list)
for r in STATS:means[int(r['model_id'])%4].append(float(r['mean_premium_eur']))
ax.boxplot([means[i] for i in range(4)],tick_labels=names)
ax.set(ylabel='Average premium over 1,024 synthetic records (EUR)');ax.grid(alpha=.25,axis='y')
title('Model-level mean premiums for four rule families')
save(7,'model_family_comparison')

# 8: TINC point intervals; identity smooth integer-valued diagnostic test.
fig,ax=plt.subplots(figsize=(9.6,4.2));ids=np.arange(len(TINC));observed=[float(r['point_value']) for r in TINC]
low=np.array([float(r['raw_min']) for r in TINC]);high=np.array([float(r['raw_max']) for r in TINC]);
reference=np.array([float(r['asset_age_years'])**2+float(r['claims'])**2 for r in TINC]);
ax.scatter(ids,observed,marker='o',facecolors='none',edgecolors='C0',s=65,label='paceval TINC point values')
ax.scatter(ids,reference,marker='.',label='Independent exact reference');
ax.vlines(ids,low,high,lw=2,label='Raw TINC intervals')
ax.set(xlabel='Deterministic sample index',ylabel='Value of age² + claims²');ax.grid(alpha=.25);ax.legend(fontsize=8)
title('Sample-wise TINC inclusion for a smooth audit expression',"This control polynomial is not an insurance tariff; finite-sample inclusion is not a universal guarantee")
save(8,'tinc_sample_audit')
print('Generated eight PNG and SVG scientific figures')
