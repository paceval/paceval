#!/usr/bin/env python3
"""Reproduce research plots from recorded ORIGINAL paceval output CSV files.
The architecture schematic is conceptual; every other numbered plot reads archived paceval outputs.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
root=Path(__file__).resolve().parent.parent
r=root/'results';out=root/'figures';out.mkdir(exist_ok=True)
summary=pd.read_csv(r/'hazard_window_summary.csv');aud=pd.read_csv(r/'audit_samples.csv')
rel=pd.read_csv(r/'reliability_bins.csv');surf=pd.read_csv(r/'paceval_probability_surfaces.csv');compound=pd.read_csv(r/'compound_bounds_samples.csv')
HAZ=['HEAVY_RAIN_P24','EXTREME_GUST_G06','AIR_FROST_F12']
NAME={'HEAVY_RAIN_P24':'24-hour heavy rain','EXTREME_GUST_G06':'6-hour extreme gust','AIR_FROST_F12':'Overnight air frost'}
COL={'v1':'#098b95','v2':'#7645b7'}
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#20334b','text.color':'#152a43','axes.edgecolor':'#637789','grid.alpha':.18,'figure.facecolor':'white','savefig.facecolor':'white','axes.facecolor':'#fcfdfe'})
def save(num,slug,fig):
    fig.savefig(out/f'{num:02d}_{slug}.png',dpi=220,bbox_inches='tight',pad_inches=.16)
    fig.savefig(out/f'{num:02d}_{slug}.pdf',bbox_inches='tight',pad_inches=.16)
    plt.close(fig)

def pivot(metric):
    a=summary.groupby(['hazard','version'])[metric].mean().unstack()
    return a.reindex(HAZ)
# 01: Only schematic, no measured result attributed to it.
fig,ax=plt.subplots(figsize=(11.4,3.5));ax.set_axis_off()
items=[('Prepared ensemble features','Member counts + metadata'),('paceval calibration graphs','Logit + probability + sensitivity'),('paceval decision graphs','Brier + action-value + bounds'),('Host policy & archive','Status, versions, CSV, audit')]
for j,(h,sub) in enumerate(items):
    x=.015+j*.25
    ax.add_patch(FancyBboxPatch((x,.24),.218,.52,boxstyle='round,pad=0.018,rounding_size=.025',facecolor=['#e9f4f7','#daf1ed','#ece7f8','#fff0df'][j],edgecolor='#7a94a8',lw=1.1,transform=ax.transAxes))
    ax.text(x+.109,.57,h,ha='center',va='center',fontsize=10,weight='bold',transform=ax.transAxes)
    ax.text(x+.109,.39,sub,ha='center',va='center',fontsize=8,transform=ax.transAxes)
    if j<3:ax.annotate('',xy=(x+.24,.49),xytext=(x+.217,.49),arrowprops=dict(arrowstyle='->',color='#31546b',lw=1.6),xycoords='axes fraction')
ax.text(.5,.96,'Research architecture (concept only)',ha='center',fontsize=14,weight='bold',transform=ax.transAxes)
ax.text(.5,.04,'GRIB ingestion, station matching and operational alerting are deliberately excluded.',ha='center',fontsize=9,transform=ax.transAxes)
save(1,'concept_architecture',fig)
# 02 probabilities by hazard and version
fig,ax=plt.subplots(figsize=(9.2,4.7));x=np.arange(3);w=.34
for j,v in enumerate(['v1','v2']):ax.bar(x+(j-.5)*w,pivot('model_probability_mean')[v].to_numpy(),width=w,label=v,color=COL[v])
ax.set_xticks(x);ax.set_xticklabels([NAME[h] for h in HAZ]);ax.set_ylabel('Mean model probability');ax.set_ylim(0,.65);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_title('Site-level model outputs across three defined event types');ax.legend(frameon=False);ax.grid(axis='y');save(2,'event_probabilities',fig)
#03 forecast lead-window trend
fig,ax=plt.subplots(figsize=(9.2,4.6));
for h in HAZ:
    for v in ['v1','v2']:
        t=summary[(summary.hazard==h)&(summary.version==v)].sort_values('window')
        ax.plot([24,48,72,96],t.model_probability_mean,marker='o',ls='-' if v=='v1' else '--',lw=2,label=f'{NAME[h]}  {v}')
ax.set(xlabel='Nominal forecast lead (hours)',ylabel='Mean model probability',title='Sensitivity to forecast lead and hazard definition');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(fontsize=8,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.19),frameon=False);ax.grid();fig.subplots_adjust(bottom=.26);save(3,'lead_probability',fig)
#04 synthetic brier
fig,ax=plt.subplots(figsize=(9.2,4.8));x=np.arange(3);w=.25
vals=pivot('brier_score');raw=summary.groupby('hazard').raw_brier_score.mean().reindex(HAZ)
ax.bar(x-w,raw,width=w,color='#a6b1bd',label='Raw member exceedance')
for j,v in enumerate(['v1','v2']):ax.bar(x+j*w,vals[v],width=w,label=v,color=COL[v])
ax.set_xticks(x);ax.set_xticklabels([NAME[h] for h in HAZ]);ax.set_ylabel('Mean synthetic Brier loss (lower is better)');ax.set_title('Synthetic-label verification only, not real weather skill');ax.legend(fontsize=8,frameon=False);ax.grid(axis='y');save(4,'synthetic_brier',fig)
#05 action classes by hazard model
fig,ax=plt.subplots(figsize=(9.2,4.6));g=summary.groupby(['hazard','version'])[['action_candidate','review','no_action']].sum();keys=[(h,v) for h in HAZ for v in ['v1','v2']]
labels=[f'{NAME[h]}\n{v}' for h,v in keys];x=np.arange(len(keys));bottom=np.zeros(len(keys))
for c,color in [('action_candidate','#00a49c'),('review','#f0b14c'),('no_action','#687f9b')]:
 y=np.array([g.loc[k,c] for k in keys]);ax.bar(x,y,bottom=bottom,color=color,label=c.replace('_',' ').title());bottom+=y
ax.set_xticks(x);ax.set_xticklabels(['Rain v1','Rain v2','Gust v1','Gust v2','Frost v1','Frost v2'],fontsize=9);ax.set_ylabel('Synthetic site × lead-window cases');ax.set_title('Interpretation of paceval action margins by host policy');ax.legend(ncol=3,fontsize=8,frameon=False);ax.grid(axis='y');save(5,'action_categories',fig)
#06 expected net margin vs lead
fig,ax=plt.subplots(figsize=(9.3,4.6))
for h in HAZ:
 for v in ['v1','v2']:
  t=summary[(summary.hazard==h)&(summary.version==v)].sort_values('window')
  ax.plot([24,48,72,96],t.mean_action_margin,marker='o',ls='-' if v=='v1' else '--',label=f'{NAME[h]}, {v}')
ax.axhline(0,color='#51566b',lw=1);ax.set(xlabel='Nominal forecast lead (hours)',ylabel='Mean synthetic net benefit (arbitrary units)',title='Net benefit depends on explicit asset loss and mitigation assumptions');ax.legend(fontsize=8,ncol=2,frameon=False);ax.grid();save(6,'action_margins',fig)
#07 reliability v1/v2 for each hazard, avoid labeling operational skill
fig,axes=plt.subplots(1,3,figsize=(11,3.9),sharex=True,sharey=True)
for ax,h in zip(axes,HAZ):
 for v in ['v1','v2']:
  t=rel[(rel.hazard==h)&(rel.version==v)&(rel.cases>=50)].sort_values('mean_probability')
  ax.plot(t.mean_probability,t.synthetic_event_frequency,marker='o',ms=4,label=v,color=COL[v])
 ax.plot([0,1],[0,1],color='#8e979f',ls=':',lw=1)
 ax.set(title=NAME[h],xlabel='Mean model probability',xlim=(0,1),ylim=(0,1));ax.grid(alpha=.18)
axes[0].set_ylabel('Synthetic event frequency');axes[2].legend(frameon=False,fontsize=8);fig.suptitle('Illustrative reliability bins with synthetic outcomes only',fontweight='bold',y=1.02);save(7,'synthetic_reliability',fig)
#08,09 3D surfaces from paceval
for num,v in [(8,'v1'),(9,'v2')]:
 t=surf[(surf.hazard==HAZ[0])&(surf.version==v)]
 x=sorted(t.ensemble_exceedance_fraction.unique());y=sorted(t.standardized_mean_anomaly.unique())
 p=t.pivot(index='standardized_mean_anomaly',columns='ensemble_exceedance_fraction',values='probability').loc[y,x]
 xx,yy=np.meshgrid(x,y)
 fig=plt.figure(figsize=(8.6,5.5));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(xx,yy,p.values,cmap='viridis',rstride=1,cstride=1,linewidth=0,antialiased=True)
 ax.set(xlabel='Member exceedance fraction',ylabel='Mean anomaly / scale',zlabel='Event probability',zlim=(0,1),title=f'paceval probability surface: 24-hour rain, {v}')
 ax.view_init(25,235);save(num,f'probability_surface_{v}',fig)
#10 Sensitivity to oriented mean: model v2, actually calculated by paceval
x=sorted(surf[surf.hazard==HAZ[1]].ensemble_exceedance_fraction.unique())
y=sorted(surf[surf.hazard==HAZ[1]].standardized_mean_anomaly.unique())
t=surf[(surf.hazard==HAZ[1])&(surf.version=='v2')]
mat=t.pivot(index='standardized_mean_anomaly',columns='ensemble_exceedance_fraction',values='probability_sensitivity_mean').loc[y,x]
fig,ax=plt.subplots(figsize=(8.7,5.0));c=ax.contourf(x,y,mat.values,levels=23,cmap='magma');fig.colorbar(c,ax=ax,label='dP / d(oriented mean), per m/s')
ax.set(xlabel='Member exceedance fraction',ylabel='Mean anomaly / scale',title='Analytic paceval sensitivity: extreme-gust event, model v2');save(10,'sensitivity_surface',fig)
#11 sample distribution decision margin
fig,ax=plt.subplots(figsize=(9.2,4.7))
for v in [1,2]:
 t=aud[(aud.version==v)&(aud.hazard==0)]
 ax.scatter(t.prob,t.action_margin,s=11,alpha=.42,label=f'v{v}',color=COL[f'v{v}'])
ax.axhline(0,color='#8a939e',lw=1,ls='--');ax.set(xlabel='paceval model probability',ylabel='Synthetic net benefit (arbitrary units)',title='An identical probability can imply different asset-level action margins');ax.legend(frameon=False);ax.grid();save(11,'asset_action_scatter',fig)
#12 Frechet interval scatter
fig,ax=plt.subplots(figsize=(9.2,4.8))
t=compound[(compound.version==2)&(compound.hazard_a==0)&(compound.hazard_b==1)]
ax.scatter(t.p_a,t.frechet_upper,s=8,alpha=.45,color='#6756a7',label='Upper bound')
ax.scatter(t.p_a,t.frechet_lower,s=8,alpha=.40,color='#00a89c',label='Lower bound')
ax.set(xlabel='Heavy rain model probability',ylabel='Joint rain + gust probability bound',title='Fréchet bounds: no independence assumption');ax.set_ylim(0,1);ax.legend(frameon=False);ax.grid();save(12,'compound_frechet_bounds',fig)
#13 calibration adjustment vs raw
fig,axes=plt.subplots(1,3,figsize=(11,3.9),sharey=True)
for ax,h in zip(axes,range(3)):
 for v in [1,2]:
  t=aud[(aud.hazard==h)&(aud.version==v)]
  ax.scatter(t.raw,t.prob,s=7,alpha=.35,label=f'v{v}',color=COL[f'v{v}'])
 ax.plot([0,1],[0,1],ls=':',color='#94a0ae');ax.set(xlabel='Raw ensemble exceedance',title=NAME[HAZ[h]],xlim=(0,1),ylim=(0,1));ax.grid()
axes[0].set_ylabel('Versioned paceval probability');axes[2].legend(frameon=False);fig.suptitle('Math-function versioning without refitting or forecast-skill claims',fontweight='bold',y=1.02);save(13,'model_version_calibration',fig)
#14 Margins and Brier per issue lead (heatmap)
fig,axes=plt.subplots(1,2,figsize=(11.2,4.7),gridspec_kw={'wspace':.78})
for ax,metric,title in [(axes[0],'model_probability_mean','Average event probability'),(axes[1],'brier_score','Synthetic Brier loss')]:
 t=summary[summary.version=='v2'].pivot(index='hazard',columns='window',values=metric).loc[HAZ]
 im=ax.imshow(t.values,aspect='auto',cmap='YlGnBu' if metric=='model_probability_mean' else 'YlOrRd')
 ax.set_xticks(range(4));ax.set_xticklabels([24,48,72,96]);ax.set_yticks(range(3));ax.set_yticklabels([NAME[h] for h in HAZ]);ax.set_xlabel('Nominal forecast lead (hours)');ax.set_title(title);fig.colorbar(im,ax=ax,shrink=.7,pad=.04)
fig.subplots_adjust(left=.17,right=.96,top=.84,bottom=.14,wspace=.78)
fig.suptitle('Model v2: hazard and forecast-lead stratification',fontweight='bold',y=1.02);save(14,'stratified_metrics',fig)
print('FIGURES CREATED:',len(list(out.glob('[0-9][0-9]_*.png'))),'technical and scientific figures')
