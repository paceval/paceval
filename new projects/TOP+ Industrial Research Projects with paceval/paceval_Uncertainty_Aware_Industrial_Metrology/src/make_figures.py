#!/usr/bin/env python3
"""Reproduce WP09 scientific figures strictly from archived paceval CSV outputs.
Concept-only figure 01 is explicitly marked. Monte Carlo figure is independently derived.
"""
import csv
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap
root=Path(__file__).resolve().parents[1];out=root/'figures';out.mkdir(exist_ok=True)
with (root/'results'/'scenario_summary.csv').open() as f:summary=list(csv.DictReader(f))
with (root/'results'/'audit_samples.csv').open() as f:audit=list(csv.DictReader(f))
with (root/'results'/'monte_carlo_audit.csv').open() as f:mc=list(csv.DictReader(f))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':14,'axes.labelsize':10,
                     'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white',
                     'axes.grid':False,'savefig.facecolor':'white'})
DARK='#063b35';TEAL='#007c75';GOLD='#e29a34';RED='#c24935';BLUE='#4172ac';GREY='#737d7d'
def save(n,name,fig):
 fig.savefig(out/f'{n:02d}_{name}.png',dpi=240,bbox_inches='tight',pad_inches=.22)
 fig.savefig(out/f'{n:02d}_{name}.pdf',bbox_inches='tight',pad_inches=.2)
 plt.close(fig)
def array(rows,key,version=None):return np.array([float(r[key]) for r in rows if version is None or int(r['model_version'])==version])
def avg(key,version,group='covariance_case'):
 d=defaultdict(list)
 for r in summary:
  if int(r['model_version'])==version:d[int(r[group])].append(float(r[key]))
 return np.array(sorted(d)),np.array([np.mean(d[k]) for k in sorted(d)])
# Figure 01: architectural concept only, no claim of industrial installation.
fig,ax=plt.subplots(figsize=(11,3.25));ax.axis('off');ax.set_xlim(0,11);ax.set_ylim(0,3.25)
steps=[('Measurement inputs','x, T, u_x, u_T, rho'),('paceval graphs','y, sensitivities, variance'),('paceval decisions','U, margins, guard scores'),('C++ host','status, audit, CSV')]
for i,(title,sub) in enumerate(steps):
 x=.1+i*2.76
 box=FancyBboxPatch((x,1.08),2.52,1.15,boxstyle='round,pad=0.08,rounding_size=0.10',
                     facecolor=('#e9f1eb' if i!=3 else '#faf1e4'),edgecolor=TEAL if i!=3 else GOLD,lw=1.7)
 ax.add_patch(box);ax.text(x+1.26,1.84,title,ha='center',color=DARK,fontsize=11,fontweight='bold');ax.text(x+1.26,1.47,sub,ha='center',color='#435752',fontsize=8.5)
 if i<3:ax.annotate('',(x+2.68,1.64),(x+2.53,1.64),arrowprops={'arrowstyle':'->','lw':1.7,'color':GOLD})
ax.text(5.5,2.74,'An executed mathematical chain using persistent paceval handles',ha='center',fontsize=13,color=DARK,fontweight='bold')
ax.text(5.5,.55,'Concept schematic; the underlying numerical calculations and later figures use real paceval execution',ha='center',fontsize=9,color=GREY)
save(1,'architecture_concept',fig)
# 02 correlation dependence of combined standard uncertainty.
fig,ax=plt.subplots(figsize=(7.6,4.5))
for v,c,l in [(1,BLUE,'Version 1: first-order'),(2,TEAL,'Version 2: nonlinear moments')]:
 x,y=avg('mean_u_mm',v);rr=np.array([float(next(z['rho'] for z in summary if int(z['covariance_case'])==int(k))) for k in x]);ax.plot(rr,y*1e3,'o-',color=c,lw=2,label=l)
ax.set(xlabel='Correlation coefficient between sensor and temperature',ylabel='Mean combined standard uncertainty (micrometres)',title='Correlation changes the propagated uncertainty');ax.grid(alpha=.18);ax.legend();save(2,'correlation_uncertainty',fig)
# 03 status shares aggregated by correlation case v2.
fig,ax=plt.subplots(figsize=(8,4.7));by=defaultdict(lambda:np.zeros(3))
for r in summary:
 if int(r['model_version'])==2:by[int(r['covariance_case'])]+=np.array([float(r['accepted']),float(r['review']),float(r['rejected'])])
xs=np.arange(10);v=np.stack([by[j]/sum(by[j]) for j in xs]);
for j,(label,c) in enumerate([('ACCEPT',TEAL),('REVIEW',GOLD),('REJECT',RED)]):ax.bar(xs,v[:,j],bottom=np.sum(v[:,:j],axis=1),color=c,label=label,width=.7)
ax.set(title='Guard-banded outcomes across ten covariance cases',xlabel='Covariance scenario',ylabel='Share of synthetic cases',ylim=(0,1));ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.16));save(3,'status_shares_by_covariance',fig)
# 04 model revision y drift.
fig,ax=plt.subplots(figsize=(8,4.3))
for v,color in [(1,BLUE),(2,TEAL)]:
 x,y=avg('mean_y_mm',v,'revision');ax.plot(x,y*1000,marker='o',color=color,label=f'v{v}')
ax.set(title='Calibrated mean changes across ten controlled revisions',xlabel='Calibration coefficient revision',ylabel='Mean calibrated output (micrometres)',xticks=range(10));ax.legend();ax.grid(alpha=.2);save(4,'model_revision_shift',fig)
# 05 uncertainty field surface: x and rho coordinates (v2) all representative audit points.
sub=[r for r in audit if int(r['model_version'])==2 and int(r['revision'])==0]
x=np.array([float(r['x']) for r in sub]);y=np.array([float(r['rho']) for r in sub]);z=np.array([float(r['u_mm'])*1e3 for r in sub]);
fig,ax=plt.subplots(figsize=(7.7,4.7));p=ax.tricontourf(x,y,z,levels=16,cmap='viridis');fig.colorbar(p,ax=ax,label='Standard uncertainty (micrometres)');ax.set(xlabel='Normalized sensor input x',ylabel='Correlation coefficient',title='Measured graph output: uncertainty field');save(5,'uncertainty_field',fig)
# 06 basic band sketch based on representative paceval output, explicitly illustrative slice.
a=next(r for r in audit if int(r['model_version'])==2 and int(r['covariance_case'])==4)
target=float(a['target_mm']);tol=float(a['tol_mm']);U=float(a['U_mm'])
fig,ax=plt.subplots(figsize=(8,3.2));ax.axvspan(-tol,tol,color='#f2e3cb',alpha=.9,label='Engineering tolerance');ax.axvspan(-tol+U,tol-U,color='#c7e5dc',alpha=.96,label='Guard-banded acceptance')
for x0,l,c in [(-tol,'LSL',RED),(tol,'USL',RED),(-tol+U,'AL',TEAL),(tol-U,'AU',TEAL)]:ax.axvline(x0,color=c,ls='--',lw=1.5);ax.text(x0,.76,l,rotation=90,ha='right',va='top',fontsize=9,color=c)
ax.set_xlim(-.075,.075);ax.set_ylim(0,1);ax.set_yticks([]);ax.set(xlabel='Deviation from target (mm)',title='Decision-rule geometry, illustrated using computed expanded uncertainty');ax.legend(loc='lower center',ncol=2);save(6,'guardband_geometry',fig)
# 07 quality score relationship.
fig,ax=plt.subplots(figsize=(7.8,4.4));sub=[r for r in audit if int(r['model_version'])==2]
x=np.array([float(r['y_mm']) for r in sub]);y=np.array([float(r['quality_score']) for r in sub]);c=np.array([float(r['rho']) for r in sub]);
p=ax.scatter(x*1e3,y,c=c,cmap='BrBG',s=10,alpha=.65,rasterized=True);fig.colorbar(p,ax=ax,label='Input correlation');ax.set(xlabel='Calibrated output (micrometres)',ylabel='Composite quality score',title='Reusable paceval score across measurement records');save(7,'quality_score_landscape',fig)
# 08 aggregate ACCEPT/REVIEW/REJECT for v1 vs v2.
fig,ax=plt.subplots(figsize=(7.8,4.3));vtotal={v:np.sum([[int(r['accepted']),int(r['review']),int(r['rejected'])] for r in summary if int(r['model_version'])==v],axis=0) for v in (1,2)}
X=np.arange(3);w=.36;ax.bar(X-w/2,vtotal[1],w,label='v1',color=BLUE);ax.bar(X+w/2,vtotal[2],w,label='v2',color=TEAL)
ax.set(xlabel='Deterministic decision category',ylabel='Number of synthetic model cases',xticks=X,xticklabels=['ACCEPT','REVIEW','REJECT'],title='Two concurrently retained mathematical model versions');ax.legend();save(8,'versioned_decisions',fig)
# 09 nonlinear bias calculated analytically from archived values (model v2 derived from raw columns)
fig,ax=plt.subplots(figsize=(7.8,4.3));sub=[r for r in audit if int(r['model_version'])==2];u=np.array([float(r['ux']) for r in sub]);bias=np.array([float(r['a2'])*float(r['ux'])**2*1000 for r in sub]);
ax.scatter(u,bias,s=12,alpha=.5,color=GOLD);ax.set(xlabel='Standard uncertainty of normalized sensor input',ylabel='Nonlinear mean correction (micrometres)',title='Quadratic curvature contribution in model v2');save(9,'nonlinear_bias',fig)
# 10 response sensitivity to sensor input (from actual paceval graph).
fig,ax=plt.subplots(figsize=(7.8,4.3));sub=[r for r in audit if int(r['model_version'])==2];x=np.array([float(r['x']) for r in sub]);sens=np.array([float(r['uncertainty_sensitivity_x'])*1e3 for r in sub]);
ax.scatter(x,sens,s=12,c=np.array([float(r['rho']) for r in sub]),cmap='coolwarm',alpha=.65,rasterized=True);ax.set(xlabel='Normalized sensor input x',ylabel='d(standard uncertainty)/dx (micrometres)',title='Analytical sensitivity graph output');save(10,'uncertainty_sensitivity',fig)
# 11 independent Monte Carlo verification: clearly labeled external reference, not paceval figure.
fig,ax=plt.subplots(figsize=(7,4.6));x=np.array([float(r['reference_variance_mm2']) for r in mc]);y=np.array([float(r['mc_variance_mm2']) for r in mc]);
ax.scatter(x*1e6,y*1e6,color=TEAL,s=35);mn=min(min(x),min(y))*1e6;mx=max(max(x),max(y))*1e6;ax.plot([mn,mx],[mn,mx],color=RED,ls='--',label='Equality');ax.set(xlabel='paceval v2 predicted variance (µm²)',ylabel='Independent Monte Carlo variance (µm²)',title='Independent Gaussian Monte Carlo verification');ax.legend();save(11,'monte_carlo_reference',fig)
# 12 decision map across x and correlation, from genuine graph output samples.
fig,ax=plt.subplots(figsize=(8,4.6));sub=[r for r in audit if int(r['model_version'])==2];xs=np.array([float(r['x']) for r in sub]);rs=np.array([float(r['rho']) for r in sub]);d=np.array([int(float(r['decision_code'])) for r in sub]);
for value,label,color in [(-1,'REJECT',RED),(0,'REVIEW',GOLD),(1,'ACCEPT',TEAL)]:
 m=d==value;ax.scatter(xs[m],rs[m],s=13,alpha=.55,c=color,label=label)
ax.set(title='Three-way guard-band decisions over synthetic inputs',xlabel='Normalized sensor input',ylabel='Sensor / temperature correlation');ax.legend(loc='lower center',ncol=3,bbox_to_anchor=(.5,-.21));save(12,'decision_map',fig)
print('CREATED_12_FIGURES_FROM_ARCHIVED_DATA')
