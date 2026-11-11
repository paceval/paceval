#!/usr/bin/env python3
"""Create publication graphics from the included study CSV files, never timing plots."""
import csv
import math
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
NAVY='#14344C'; BLUE='#146A8A'; CYAN='#05AAB8'; AMBER='#F0A437'; GREEN='#158B73'; GREY='#647887'; RED='#C6514A'
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.titlesize':13,'axes.titleweight':'bold','axes.labelcolor':NAVY,'text.color':NAVY,'axes.edgecolor':'#B7CCD7','grid.color':'#E0E9EF','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})

def save(name):
    plt.tight_layout(pad=1.5)
    plt.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight')
    plt.savefig(OUT/(name+'.svg'),bbox_inches='tight')
    plt.close()

def load(fn):
    return list(csv.DictReader(open(ROOT/'examples'/fn,newline='')))

# 01 - host and computation-engine responsibilities
fig,ax=plt.subplots(figsize=(11,4.1));ax.set_xlim(0,12);ax.set_ylim(0,4);ax.axis('off')
boxes=[('Vibration windows','Host: import and feature extraction',0.15,BLUE),
       ('Versioned formulas','50 approved mathematical models',3.18,BLUE),
       ('paceval execution','Prepared graphs, repeated batch calls',6.21,CYAN),
       ('Model audit','Asset split, thresholds, independent check',9.24,GREEN)]
for name,sub,x,color in boxes:
  rect=FancyBboxPatch((x,1.48), (2.65 if x<9 else 2.65),1.4,boxstyle='round,pad=0.13,rounding_size=0.18',fc=color,ec=color)
  ax.add_patch(rect);ax.text(x+1.32,2.42,name,ha='center',color='white',fontweight='bold',fontsize=11)
  ax.text(x+1.32,1.94,sub,ha='center',color='white',fontsize=7.4,wrap=True)
for x in (2.9,5.92,8.95):ax.annotate('',xy=(x+0.22,2.16),xytext=(x,2.16),arrowprops={'arrowstyle':'-|>','lw':2,'color':NAVY})
ax.text(6,3.62,'Separation of responsibilities in the demonstrator',ha='center',fontweight='bold',fontsize=15)
ax.text(6,0.63,'Synthetic, offline research only | No bearing-failure predictor or field instrumentation is claimed',ha='center',fontsize=10,color=GREY)
save('01_execution_architecture')

# Read raw vibration for a healthy and a synthetic fault example
raw=load('raw_vibration.csv')
series=defaultdict(list)
for row in raw:
  key=(int(row['asset_id']),int(row['window_id']))
  if key in ((1,0),(0,0)):
    series[key].append(float(row['accel_g']))
fig,ax=plt.subplots(figsize=(10,4.1))
for key, color,name in [((1,0),BLUE,'Healthy synthetic window'),((0,0),RED,'Fault-like synthetic window')]:
  x=series[key];ax.plot(range(len(x)),x,color=color,lw=1.15,label=name,alpha=.85)
ax.set_title('Raw acceleration windows: example signatures')
ax.set_xlabel('Sample index');ax.set_ylabel('Acceleration (g, synthetic)');ax.grid(alpha=.6);ax.legend(loc='upper right',frameon=False)
save('02_vibration_windows')

features=load('features.csv')
fig,ax=plt.subplots(figsize=(9.5,4.5))
for label,name,color in [(0,'Healthy',BLUE),(1,'Synthetic fault',RED)]:
  x=[float(r['kurtosis']) for r in features if int(r['label'])==label]
  ax.hist(x,bins=np.linspace(min(float(y['kurtosis']) for y in features),max(float(y['kurtosis']) for y in features),26),alpha=.65,label=name,color=color)
ax.set_title('Pearson kurtosis distribution across recorded windows')
ax.set_xlabel('Kurtosis (dimensionless)');ax.set_ylabel('Windows');ax.legend(frameon=False);ax.grid(axis='y',alpha=.4)
save('03_kurtosis_distribution')

metrics=load('model_metrics.csv');sel=next(r for r in metrics if int(r['selected']))
chosen=int(sel['model_id']);all_scores=load('evaluation.csv')
model_rows=[r for r in all_scores if int(r['model_id'])==chosen and r['split']=='test']
fig,ax=plt.subplots(figsize=(10,4.6))
for label,name,color in [(0,'Healthy held-out',BLUE),(1,'Synthetic fault held-out',RED)]:
  data=[float(r['score']) for r in model_rows if int(r['label'])==label]
  ax.hist(data,bins=24,alpha=.65,color=color,label=name)
ax.axvline(.55,color=GREEN,ls='--',lw=2,label='Fixed threshold 0.55')
ax.set_title('Held-out condition-score distribution: selected model '+str(chosen))
ax.set_xlabel('Mathematical score (not a calibrated probability)');ax.set_ylabel('Windows')
ax.legend(frameon=False);ax.grid(axis='y',alpha=.4)
save('04_holdout_scores')

fig,ax=plt.subplots(figsize=(7.1,5.2))
TP=int(sel['test_TP']);TN=int(sel['test_TN']);FP=int(sel['test_FP']);FN=int(sel['test_FN'])
matrix=np.array([[TN,FP],[FN,TP]])
ax.imshow(matrix,cmap='Blues',vmin=0,vmax=max(1,matrix.max()))
for row in range(2):
  for col in range(2):ax.text(col,row,str(matrix[row,col]),ha='center',va='center',fontsize=22,fontweight='bold',color='white' if matrix[row,col]>40 else NAVY)
ax.set_xticks([0,1],['No alert','Alert']);ax.set_yticks([0,1],['Healthy','Fault-like'])
ax.set_xlabel('Decision');ax.set_ylabel('Synthetic reference label')
ax.set_title('Held-out confusion matrix (asset-disjoint)')
save('05_heldout_confusion')

fig,ax=plt.subplots(figsize=(10,4.2))
xs=list(range(50));v=[float(x['validation_f1']) for x in metrics];t=[float(x['test_f1']) for x in metrics]
ax.plot(xs,v,marker='.',ms=5,color=BLUE,lw=1.3,label='Validation F1')
ax.plot(xs,t,marker='.',ms=5,color=AMBER,lw=1,label='Test F1 (reported only after selection)')
ax.scatter([chosen],[float(sel['validation_f1'])],marker='*',s=200,color=GREEN,zorder=5,label='Frozen selected model')
ax.set_title('Reproducible candidate-model evaluation');ax.set_xlabel('Formula version ID');ax.set_ylabel('Window-level F1 score')
ax.grid(alpha=.5);ax.set_ylim(0,1.08);ax.legend(loc='lower right',frameon=False,fontsize=9)
save('06_model_versions')

samples=load('tinc_samples.csv')
center=np.array([(float(x['upper'])+float(x['lower']))/2 for x in samples]);low=np.array([float(x['lower']) for x in samples]);hi=np.array([float(x['upper']) for x in samples]);ref=np.array([float(x['reference']) for x in samples]);idx=np.arange(len(samples))
fig,ax=plt.subplots(figsize=(10,4.25))
ax.plot(idx, (hi-low)*1e15,'o-',label='TINC interval width',color=BLUE)
ax.plot(idx,np.abs(ref-center)*1e15,'s-',label='Reference to interval midpoint',color=GREEN,markersize=4)
ax.set_title('Numerical interval check, 24 sampled windows')
ax.set_xlabel('TINC sample index');ax.set_ylabel('Magnitude (× 10⁻¹⁵ score units)')
ax.grid(alpha=.5);ax.legend(frameon=False)
save('07_tinc_sample_audit')

fig,ax=plt.subplots(figsize=(8.5,5.1))
R=np.linspace(0,2.2,100);K=np.linspace(-.6,3.5,100);rr,kk=np.meshgrid(R,K)
# score family 1, selected model (5): parameter coefficients recreated
m=chosen;a=.35+.045*(m%11);b=.18+.05*(m%7);c=.12+.04*(m%9);d=-1.4+.065*(m%13)
z=a*rr+b*kk+c*0+d
if m%4==1:z+=.035*rr*kk
if m%4==2:z+=.03*rr*rr
if m%4==3:z+=.045*np.tanh(kk)
v=1/(1+np.exp(-z));co=ax.contourf(rr,kk,v,levels=np.linspace(0,1,21),cmap='viridis')
fig.colorbar(co,ax=ax,label='Mathematical score')
ax.contour(rr,kk,v,levels=[.55],colors='white',linewidths=2)
ax.set_title('Selected score surface with temperature fixed at 60 °C')
ax.set_xlabel('Normalized RMS R');ax.set_ylabel('Normalized kurtosis K')
save('08_mathematical_score_surface')
print('wrote 8 PNG and 8 SVG plots to',OUT)
