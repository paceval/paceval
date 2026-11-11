#!/usr/bin/env python3
"""Rebuild all scientific PNG figures from checked synthetic datasets.
No benchmark timings or unmeasured acceleration claims are plotted.
"""
import argparse,ast,csv,collections,math,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib import rcParams
rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'white','savefig.facecolor':'white'})
BLUE='#1677bd';DARK='#103451';GREEN='#168f78';ORANGE='#d48e3b';RED='#b54d52'
p=argparse.ArgumentParser();p.add_argument('--root',default='..');args=p.parse_args();root=pathlib.Path(args.root);figdir=root/'figures';figdir.mkdir(exist_ok=True)
with (root/'examples'/'evaluation.csv').open() as f:evaluations=list(csv.DictReader(f))
with (root/'examples'/'expressions.csv').open() as f:cases=list(csv.DictReader(f))
with (root/'examples'/'tinc_samples.csv').open() as f:tinc=list(csv.DictReader(f))

def save(name):
 plt.savefig(figdir/name,dpi=180,bbox_inches='tight',pad_inches=.15)
 plt.close()

# Clear architectural separation including model-proposal boundary.
fig,ax=plt.subplots(figsize=(11.5,3.2));ax.set_xlim(0,12);ax.set_ylim(0,3.7);ax.axis('off')
steps=[('Untrusted formula','synthetic LLM-like text'),('C++ validation','allowlist + bounded AST'),('paceval graph','create once / reuse'),('Independent audit','native + 110-digit')]
for i,(a,b) in enumerate(steps):
 x=i*3.02+.1;color=GREEN if i==2 else DARK
 patch=FancyBboxPatch((x,.8), (2.7),1.9,boxstyle='round,pad=.17',facecolor='#eaf7f5' if i==2 else '#edf4fa',edgecolor=color,linewidth=2)
 ax.add_patch(patch);ax.text(x+1.35,1.97,a,ha='center',va='center',color=DARK,weight='bold',fontsize=11)
 ax.text(x+1.35,1.45,b,ha='center',va='center',fontsize=8.8,color=DARK)
 if i<3:ax.add_patch(FancyArrowPatch((x+2.88,1.7),(x+3.01,1.7),arrowstyle='-|>',mutation_scale=18,linewidth=1.8,color=BLUE))
ax.set_title('Offline expression-validation boundary',color=DARK,fontsize=15,weight='bold',pad=15)
ax.text(6,.28,'The C++ host validates inputs and checks semantics; paceval evaluates prepared mathematical graphs.',ha='center',fontsize=9,color=DARK)
save('01_execution_architecture.png')

# Actual acceptance by category
counts=collections.Counter(x['expected_status'] for x in cases)
order=['OK','DOMAIN_ERROR','SYNTAX_ERROR','UNAPPROVED_FUNCTION','UNKNOWN_VARIABLE','RESOURCE_LIMIT','UNSAFE_CHARACTER']
fig,ax=plt.subplots(figsize=(10,4.2));ax.barh(range(len(order)),[counts[k] for k in order],color=[GREEN]+[BLUE]*6)
ax.set_yticks(range(len(order)),[x.replace('_',' ').title() for x in order]);ax.invert_yaxis()
for i,k in enumerate(order):ax.text(counts[k]+1,i,str(counts[k]),va='center',fontsize=10)
ax.set_xlim(0,178);ax.set_xlabel('Number of test expressions');ax.set_title('200 deterministic synthetic expression cases',weight='bold',color=DARK)
ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
save('02_acceptance_and_rejection.png')

# Representative formula across 16 test inputs
one=[r for r in evaluations if r['case_id']=='E001' and r['status']=='OK']
fig,ax=plt.subplots(figsize=(9.8,3.9));x=list(range(len(one)))
y=[float(r['paceval_result']) for r in one];ref=[float(r['independent_cpp_reference']) for r in one]
ax.plot(x,y,marker='o',color=BLUE,label='paceval (16 input samples)',linewidth=2)
ax.plot(x,ref,linestyle='--',color=ORANGE,label='independent C++ tree interpreter',linewidth=1.5)
ax.set_xlabel('Sample index');ax.set_ylabel('f(x,y,t,k,w,c)');ax.set_title('Illustrative damped sinusoid: reused execution graph',weight='bold',color=DARK)
ax.grid(alpha=.18);ax.legend(loc='upper left');save('03_formula_evaluation.png')

# max error is ~4e-16 vs independent high precision. Load JSON audit.
import json
with (root/'examples'/'validation_summary.json').open() as f:audit=json.load(f)
fig,ax=plt.subplots(figsize=(9.8,3.6));fig.subplots_adjust(left=.15)
labels=['Independent C++ vs paceval','110-digit reference vs paceval']
errors=[max((float(r['absolute_error']) for r in evaluations if r['status']=='OK'),default=0),float(audit['max_absolute_error'])]
ax.barh(labels,[max(e,1e-18) for e in errors],color=[BLUE,GREEN],height=.38)
ax.set_xscale('log');ax.set_xlim(1e-19,1e-10);ax.invert_yaxis();ax.set_xlabel('Maximum absolute difference (log scale)')
ax.set_title('Numerical validation of 2,560 accepted evaluations',weight='bold',color=DARK)
ax.grid(axis='x',alpha=.2)
for yv,e in enumerate(errors):ax.text(max(e,1e-18)*1.8,yv,('0 to printed precision' if e==0 else f'{e:.2e}'),va='center')
save('04_numerical_reference.png')

# TINC width, all 30 independently audited. Emphasize no global guarantee.
widths=[float(r['upper'])-float(r['lower']) for r in tinc]
fig,ax=plt.subplots(figsize=(10,3.9));xx=np.arange(len(widths))
ax.scatter(xx,[max(w,1e-17) for w in widths],color=GREEN,s=34)
ax.set_yscale('log');ax.set_ylim(5e-18,1e-10);ax.grid(alpha=.2);ax.set_xlabel('TINC sample index (10 formulas × 3 input samples)');ax.set_ylabel('Reported interval width')
ax.set_title('TINC pointwise audit: 30/30 references enclosed',weight='bold',color=DARK)
ax.text(.02,.06,'Finite sampled inclusion, not a universal interval guarantee',transform=ax.transAxes,color=DARK,fontsize=9)
save('05_tinc_interval_audit.png')

# Explicit separation: vendor engine capability vs application policy.
# The values on the right are *host choices* for this 200-case corpus, not
# properties of the paceval library.
fig,ax=plt.subplots(figsize=(12.7,5.5));ax.set_xlim(0,13);ax.set_ylim(0,5.5);ax.axis('off')
for x,title,color,sub,lines in [
  (.35,'paceval mathematical engine',GREEN,'No fixed engine-imposed caps',[
    'Expression length: resource-dependent',
    'Variable count: resource-dependent',
    'Reusable execution graphs',
    'Actual capability: supported syntax and hardware']),
  (6.9,'Untrusted LLM input policy',BLUE,'Restricts only the host validator',[
    '180 input characters; 80 AST nodes',
    '16 parser nesting levels',
    'Six approved input variables',
    '512 samples per host batch'])]:
  ax.add_patch(FancyBboxPatch((x,.95),5.8,3.8,boxstyle='round,pad=.17',facecolor='#eaf7f5' if x<1 else '#edf4fb',edgecolor=color,linewidth=2))
  ax.text(x+.22,4.33,title,color=DARK,weight='bold',fontsize=14,va='center')
  ax.text(x+.22,3.90,sub,color=color,fontsize=10.5,weight='bold')
  for j,text in enumerate(lines):ax.text(x+.28,3.33-j*.55,'• '+text,color=DARK,fontsize=10.3)
ax.text(6.5,.45,'Reviewed test path: 1,313-character expression / 48 variables / 16 independently checked samples',
        ha='center',color=DARK,weight='bold',fontsize=10.9)
ax.set_title('Engine capability vs application-controlled validation policy',weight='bold',fontsize=17,color=DARK,pad=18)
save('06_validation_policy.png')

# Actual 48-variable extended-expression reference results (not timing data).
with (root/'examples'/'approved_large_model_results.csv').open() as f: reviewed=list(csv.DictReader(f))
fig,ax=plt.subplots(figsize=(10.4,4.3))
xx=[int(r['sample']) for r in reviewed]
yy=[float(r['paceval_result']) for r in reviewed]
rr=[float(r['independent_cpp_reference']) for r in reviewed]
ax.plot(xx,yy,'o-',label='paceval (48-variable graph)',color=BLUE,linewidth=2)
ax.plot(xx,rr,'--',label='independent C++ reference',color=ORANGE,linewidth=1.5)
ax.set_title('Owner-approved model: 48 variables, 1,313 expression characters',weight='bold',color=DARK)
ax.set_xlabel('Input sample');ax.set_ylabel('Weighted-feature model output')
ax.grid(alpha=.18);ax.legend(loc='upper left')
save('08_approved_large_model.png')
print('Created 8 scientific figures under',figdir)
