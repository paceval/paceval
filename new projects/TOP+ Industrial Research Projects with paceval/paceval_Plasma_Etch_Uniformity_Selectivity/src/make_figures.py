#!/usr/bin/env python3
"""Publication plots from genuinely executed paceval CSV results, never from a surrogate rerun."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import Normalize
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'figures';D=ROOT/'results';F.mkdir(exist_ok=True)
df=pd.read_csv(D/'wafer_points.csv');su=pd.read_csv(D/'recipe_summary.csv')
plt.rcParams.update({'font.size':11,'axes.titleweight':'bold','axes.titlesize':13,'figure.facecolor':'white','axes.grid':False,'savefig.facecolor':'white','font.family':'DejaVu Sans'})
navy='#203548';teal='#087e99';purple='#7730b0'
def save(n):
 plt.tight_layout(pad=1.6);plt.savefig(F/(n+'.png'),dpi=195,bbox_inches='tight');plt.savefig(F/(n+'.pdf'),bbox_inches='tight');plt.close()
def pick(recipe,version):return df[(df.recipe==recipe)&(df.version==version)].copy()
def wafer(ax,d,col,title,cmap='viridis',vmin=None,vmax=None):
 s=ax.tricontourf(d.x,d.y,d[col],levels=32,cmap=cmap,vmin=vmin,vmax=vmax);ax.set_aspect('equal');ax.set_xlim(-1.03,1.03);ax.set_ylim(-1.03,1.03);ax.add_patch(Circle((0,0),1,fill=False,edgecolor=navy,lw=1.4));ax.set_xlabel('Normalized wafer x');ax.set_ylabel('Normalized wafer y');ax.set_title(title);ax.figure.colorbar(s,ax=ax,shrink=.77);return s
# 01 conceptual architecture, not a computational result
fig,ax=plt.subplots(figsize=(12.7,3.9));ax.set_xlim(0,14);ax.set_ylim(0,4);ax.axis('off')
blocks=[('Synthetic wafer inputs\n25 recipes / equal-area sites',.1,1.5,2.95,'#dfe8f2'),('paceval stage A\nfilm and mask rate\ngradients / sensitivities',3.55,1.5,3.0,'#dbf2f7'),('paceval stage B\nselectivity / depth\nquality / guard',7,1.5,3.0,'#e7dcf6'),('Host summaries\nnonuniformity / status\nversioned result archive',10.45,1.5,3.4,'#f4e8df')]
for txt,x,y,w,c in blocks:
 ax.add_patch(FancyBboxPatch((x,y),w,1.65,boxstyle='round,pad=.12,rounding_size=.18',facecolor=c,edgecolor=navy,lw=1.1));ax.text(x+w/2,y+.85,txt,ha='center',va='center',fontsize=10.3,color=navy,fontweight='medium')
for x in (3.16,6.62,10.08):ax.add_patch(FancyArrowPatch((x,2.3),(x+.36,2.3),arrowstyle='-|>',mutation_scale=18,color=teal,lw=1.8))
ax.text(7,.55,'Actual mathematical outputs are obtained through persistent paceval graphs. Aggregation and file I/O remain in C++.',ha='center',fontsize=10,color=navy)
ax.set_title('Architecture of the executed mathematical workflow (conceptual schematic)',fontsize=15,color=navy,pad=12);save('01_architecture')
v1=pick(15,1);v2=pick(15,2)
for name,d,col,title,cmap in [('02_film_rate_v1',v1,'filmRateNmPerMin','Film etch rate, recipe 15, model v1 (nm/min)','viridis'),('03_film_rate_v2',v2,'filmRateNmPerMin','Film etch rate, recipe 15, model v2 (nm/min)','magma'),('04_selectivity_v2',v2,'selectivity','Film-to-mask selectivity, recipe 15, v2','plasma'),('05_local_uniformity',v2,'relativeDeviation','Local deviation from wafer-center rate, recipe 15, v2','coolwarm'),('06_quality_map',v2,'qualityScore','Composed quality score, recipe 15, v2','cividis'),('07_mask_remaining',v2,'maskRemainingNm','Remaining mask thickness, recipe 15, v2 (nm)','viridis')]:
 fig,ax=plt.subplots(figsize=(7.7,6.2));wafer(ax,d,col,title,cmap);save(name)
# 08 3D wafer landscape from recorded results
from mpl_toolkits.mplot3d import Axes3D  # noqa
fig=plt.figure(figsize=(9.6,7.0));ax=fig.add_subplot(111,projection='3d');d=v2.iloc[::2];surf=ax.plot_trisurf(d.x,d.y,d.filmRateNmPerMin,cmap='plasma',linewidth=.05,antialiased=True);fig.colorbar(surf,ax=ax,shrink=.53,pad=.1,label='Film etch rate (nm/min)');ax.set(xlabel='Normalized x',ylabel='Normalized y',zlabel='Rate (nm/min)');ax.view_init(elev=25,azim=-58);ax.set_title('Actual paceval-computed spatial etch-rate surface: recipe 15, v2');save('08_3d_film_rate')
# 09 radial (azimuthal variation is shown as whiskers)
fig,ax=plt.subplots(figsize=(9.5,5.5))
for d,col,lbl in [(v1,teal,'v1'),(v2,purple,'v2')]:
 dr=d.copy();dr['radial_index']=dr.point//64;g=dr.groupby('radial_index').filmRateNmPerMin;means=g.mean();ax.plot(np.sqrt((means.index+.5)/64),means,lw=2.5,label=lbl,color=col);ax.fill_between(np.sqrt((means.index+.5)/64),g.min(),g.max(),color=col,alpha=.13)
ax.set(xlabel='Normalized wafer radius',ylabel='Film etch rate (nm/min)',title='Center-to-edge rate profile with angular range, recipe 15');ax.legend();save('09_radial_profile')
# 10 recipe candidates, with pressure and temperature encoded via coordinate/color
fig,ax=plt.subplots(figsize=(9,5.9))
for v,marker in [(1,'o'),(2,'s')]:
 q=su[su.version==v];sc=ax.scatter(q.pressureMTorr,q.meanFilmRateNmPerMin,c=q.temperatureK,cmap='coolwarm',s=70,marker=marker,edgecolors=navy,lw=.55,label=f'Model v{v}')
fig.colorbar(sc,ax=ax,label='Electrode temperature (K)');ax.set(xlabel='Recipe pressure (mTorr)',ylabel='Area-average film rate (nm/min)',title='25 synthetic operating recipes, both model versions');ax.legend();save('10_recipe_response')
# 11 recipe accept fraction
fig,ax=plt.subplots(figsize=(10.2,5.2));k=np.arange(25);a=su.set_index(['recipe','version']);ax.bar(k-.19,[a.loc[(i,1),'passFraction']*100 for i in k],width=.37,label='v1',color=teal);ax.bar(k+.19,[a.loc[(i,2),'passFraction']*100 for i in k],width=.37,label='v2',color=purple)
ax.set(xlim=(-1,25),xlabel='Synthetic recipe index',ylabel='Wafer positions passing all model guards (%)',title='Model-dependent wafer acceptance coverage');ax.set_xticks(k[::2]);ax.legend();save('11_acceptance_coverage')
# 12 sensitivity maps (pressure / temperature)
fig,axes=plt.subplots(1,2,figsize=(13.2,5.5))
for ax,col,title in zip(axes,['sensitivityTemp','sensitivityPressure'],['Local sensitivity to electrode temperature','Local sensitivity to pressure']):
 wafer(ax,v2,col,title,'viridis')
save('12_sensitivity_maps')
# 13 differences v1/v2 one common recipe
merged=v1.merge(v2,on=['recipe','point'],suffixes=('_v1','_v2'));merged['rateChange']=merged.filmRateNmPerMin_v2-merged.filmRateNmPerMin_v1
fig,ax=plt.subplots(figsize=(7.8,6.1));wafer(ax,merged.rename(columns={'x_v1':'x','y_v1':'y'}),'rateChange','Film etch rate change: v2 minus v1 (nm/min)','coolwarm');save('13_model_revision')
# 14 recipe variability
fig,ax=plt.subplots(figsize=(9.7,5.5));piv=su.pivot(index='recipe',columns='version',values='coefficientVariationPct');ax.plot(piv.index,piv[1],marker='o',ms=4,label='v1',color=teal);ax.plot(piv.index,piv[2],marker='s',ms=4,label='v2',color=purple);ax.set(xlabel='Recipe',ylabel='Wafer coefficient of variation (%)',title='Within-wafer variability by persistent model version');ax.legend();save('14_uniformity_summary')
# 15 selectivity/depth trade space
fig,ax=plt.subplots(figsize=(9.7,5.7));for_data=su
for v,mark,col in [(1,'o',teal),(2,'s',purple)]:
 d=for_data[for_data.version==v];sz=45+360*d.passFraction;ax.scatter(d.meanDepthNm,d.meanSelectivity,s=sz,alpha=.72,color=col,marker=mark,label=f'v{v}',edgecolors=navy,lw=.5)
ax.set(xlabel='Area-average etch depth (nm)',ylabel='Mean film/mask selectivity',title='Recipe trade space; symbol size represents quality-pass coverage');ax.legend();save('15_recipe_tradeoff')
# 16 quality distribution, preserving two model results
fig,ax=plt.subplots(figsize=(9.5,5.5))
for v,col in [(1,teal),(2,purple)]:ax.hist(df[df.version==v].qualityScore,bins=60,alpha=.48,color=col,label=f'v{v}')
ax.axvline(.10,lw=1.5,ls='--',color='#aa3d3d',label='Synthetic score limit');ax.set(xlabel='Computed quality score (dimensionless)',ylabel='Wafer positions',title='Distribution of synthetic process-quality scores');ax.legend();save('16_score_distribution')
print('FIGURES_CREATED',len(list(F.glob('*.png'))),len(list(F.glob('*.pdf'))))
