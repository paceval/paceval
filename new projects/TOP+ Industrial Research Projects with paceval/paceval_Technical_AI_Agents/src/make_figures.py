#!/usr/bin/env python3
"""Generate publication figures from included synthetic, audited casebook data."""
from __future__ import annotations
import csv
from collections import Counter,defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import mpmath as mp
import numpy as np

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'figures'
DATA=BASE/'examples'
NAVY='#122642'; BLUE='#167ac5'; CYAN='#13afcf'; GREEN='#159779'; RED='#c9504c'
plt.rcParams.update({'font.size':11,'font.family':'DejaVu Sans','axes.titlesize':17,'axes.labelcolor':NAVY,'axes.titlecolor':NAVY,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
results=list(csv.DictReader((DATA/'agent_results.csv').open()))
tinc=list(csv.DictReader((DATA/'tinc_samples.csv').open()))

def save(fig,name):fig.savefig(OUT/name,dpi=185,bbox_inches='tight',facecolor='white');plt.close(fig)

# FIG 1: Research integration boundary
fig,ax=plt.subplots(figsize=(12,3.4));ax.set_xlim(0,12);ax.set_ylim(0,3.4);ax.axis('off')
boxes=[(.18,'Agent-proposed\nstructured request',NAVY),(2.68,'Validated model ID\n+ unit dimensions',BLUE),(5.18,'Reusable paceval\nexecution graph',GREEN),(7.68,'Independent\nnumerical oracle',BLUE),(10.18,'Structured\nresult / status',NAVY)]
for x,txt,col in boxes:
    ax.add_patch(patches.FancyBboxPatch((x,.96),1.66,1.06,boxstyle='round,pad=0.12',facecolor=col,edgecolor='none'))
    ax.text(x+.83,1.49,txt,color='white',ha='center',va='center',fontsize=10,fontweight='bold')
for x in [1.92,4.42,6.92,9.42]:ax.annotate('',xy=(x+.63,1.49),xytext=(x,1.49),arrowprops=dict(arrowstyle='->',lw=2,color=CYAN))
ax.text(6,2.7,'OFFLINE engineering mathematics: explicit responsibility boundary',ha='center',fontsize=15,color=NAVY,fontweight='bold')
ax.text(6,.43,'LLM / MCP orchestration is external. The C++ host rejects invalid inputs before invoking the actual paceval runtime.',ha='center',fontsize=10,color='#4d6278')
save(fig,'01_verified_architecture.png')

# FIG 2: Request audit distribution
counts=Counter(r['status'] for r in results)
fig,ax=plt.subplots(figsize=(10,4.3));bars=[100,30,20]
rect=ax.barh(['Original valid requests','Exact repeated requests','Intentionally invalid requests'],bars,color=[BLUE,CYAN,RED],height=.63)
for b,v in zip(rect,bars):ax.text(v+2,b.get_y()+b.get_height()/2,str(v),va='center',fontweight='bold',color=NAVY)
ax.invert_yaxis();ax.set_xlim(0,125);ax.set_xlabel('Number of structured requests');ax.set_title('Casebook scope: 150 evaluated requests',loc='left',fontweight='bold')
ax.text(0,-.52,'The 20 invalid requests are safely rejected, not passed to an execution graph.',fontsize=10,color='#547088')
fig.tight_layout();save(fig,'02_casebook_coverage.png')

# FIG 3: Absolute error - user-facing output units vary, so use scaled error
accepted=[r for r in results if r['status']=='OK']
errors=[abs(float(r['result'])-float(r['native_reference']))/(1+abs(float(r['native_reference']))) for r in accepted]
fig,ax=plt.subplots(figsize=(11,4.1))
ax.plot(range(1,len(errors)+1),[max(x,1e-18) for x in errors],'.',ms=5,color=BLUE)
ax.set_yscale('log');ax.set_ylim(1e-19,1e-10);ax.axhline(6e-12,color=RED,ls='--',lw=1.5,label='Conservative acceptance tolerance')
ax.set_xlabel('Accepted request, including replayed requests');ax.set_ylabel('|paceval - native C++| / (1 + |native|)')
ax.set_title('Numerical agreement of actual evaluated values',loc='left',fontweight='bold');ax.legend(frameon=False,loc='upper right');ax.grid(alpha=.17)
ax.text(.01,.09,'Values plotted at 10⁻¹⁸ where the difference is exactly zero',transform=ax.transAxes,fontsize=9,color='#5d7184')
fig.tight_layout();save(fig,'03_numerical_agreement.png')

# FIG 4: Error classifications
bad=Counter(r['status'] for r in results if r['status']!='OK')
keys=sorted(bad,key=lambda x:(bad[x],x))
fig,ax=plt.subplots(figsize=(10,4))
ax.barh(keys,[bad[k] for k in keys],color=RED,height=.65)
for j,k in enumerate(keys):ax.text(bad[k]+.13,j,str(bad[k]),va='center',color=NAVY)
ax.set_xlim(0,max(bad.values())+1.6);ax.set_xlabel('Rejected test inputs');ax.set_title('Fail-closed contract: tested rejection categories',loc='left',fontweight='bold')
fig.tight_layout();save(fig,'04_invalid_requests.png')

# FIG 5: Correctly frame TINC inclusion, not claim universal guarantee
mp.mp.dps=110
from high_precision_reference import evaluate
labels=[];pass_counts=[];fail_counts=[];by=defaultdict(list)
for r in tinc:
    x=[mp.mpf(float(r[f'x{i}'])) for i in range(6)]
    y=evaluate(r['model_id'],x)
    ok=mp.mpf(float(r['lower_si']))<=y<=mp.mpf(float(r['upper_si']))
    by[r['model_id']].append(ok)
for key in by:labels.append(key.replace('_',' '));pass_counts.append(sum(by[key]));fail_counts.append(len(by[key])-sum(by[key]))
fig,ax=plt.subplots(figsize=(10.5,5.5));yy=np.arange(len(labels))
ax.barh(yy,pass_counts,label='Reference contained',color=GREEN,height=.6)
ax.barh(yy,fail_counts,left=pass_counts,label='Reference outside interval',color=RED,height=.6)
ax.set_yticks(yy,labels);ax.invert_yaxis();ax.set_xticks([0,1,2,3]);ax.set_xlim(0,3.55);ax.set_xlabel('Audited TINC samples per formula');ax.legend(loc='lower right',frameon=False)
ax.set_title('TINC audit versus independent 110-digit reference',loc='left',fontweight='bold')
ax.text(.03,.03,'Finite pointwise test; 20/24 contained, four extremely narrow exclusions. Not a rigorous guarantee.',transform=ax.transAxes,fontsize=9,color='#52657b')
fig.tight_layout();save(fig,'05_tinc_reference_audit.png')

# FIG 6: Unit normalization worked example
fig,ax=plt.subplots(figsize=(11,3.5));ax.set_xlim(0,11);ax.set_ylim(0,3.5);ax.axis('off')
entries=[(.15,'Tool request','F = 10 kN\nA = 2 cm²',NAVY),(3.02,'Host normalization','F = 10,000 N\nA = 0.0002 m²',BLUE),(5.88,'paceval result','σ = F / A\n= 50,000,000 Pa',GREEN),(8.7,'Typed response','50 MPa\nstatus = OK',NAVY)]
for x,heading,detail,col in entries:
    ax.add_patch(patches.FancyBboxPatch((x,.7),2.12,1.9,boxstyle='round,pad=.12',fc='#f0f6fa',ec='#b7cfdd',lw=1))
    ax.add_patch(patches.FancyBboxPatch((x,2.08),2.12,.52,boxstyle='round,pad=.08',fc=col,ec='none'))
    ax.text(x+1.06,2.34,heading,color='white',ha='center',va='center',fontweight='bold',fontsize=10)
    ax.text(x+1.06,1.38,detail,color=NAVY,ha='center',va='center',fontsize=11)
for x in [2.44,5.31,8.16]:ax.annotate('',xy=(x+.48,1.65),xytext=(x,1.65),arrowprops=dict(arrowstyle='->',color=CYAN,lw=2))
ax.text(5.5,3.08,'Reproducible dimensional conversion: axial stress',color=NAVY,ha='center',fontweight='bold',fontsize=16)
fig.tight_layout();save(fig,'06_unit_checked_tool_call.png')
print('Generated 6 figures in',OUT)
