#!/usr/bin/env python3
"""Scientific plots sourced exclusively from executed original paceval CSV output."""
import csv
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
P=Path(__file__).resolve().parents[1];F=P/'figures';F.mkdir(exist_ok=True)
S=pd.read_csv(P/'results'/'screening.csv');T=pd.read_csv(P/'results'/'cure_profiles.csv')
C=pd.read_csv(P/'results'/'model_comparison.csv')
plt.rcParams.update({'figure.dpi':130,'savefig.dpi':180,'font.size':10,'axes.labelsize':11,'axes.titlesize':13,'figure.constrained_layout.use':True})
def save(fig,name):
 fig.savefig(F/(name+'.png'),bbox_inches='tight');fig.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
 print('FIG',name)
rec='R032'
# 01 - Temperature evolution: three in-component layers and air schedule.
fig,ax=plt.subplots(figsize=(9,4.8))
d=T[(T.recipe_id==rec)&(T.model=='V2')]
for node in [0,5,9]:
 u=d[d.node==node];ax.plot(u.time_min,u.part_C,label=f'Layer {node+1}')
u=d[d.node==0];ax.plot(u.time_min,u.air_C,ls='--',lw=1.5,label='Autoclave air')
ax.set(title='Autoclave cycle and through-thickness thermal lag',xlabel='Cycle time (min)',ylabel='Temperature (°C)');ax.grid(alpha=.25);ax.legend(ncol=4);save(fig,'fig01_temperature_cycle')
# 02 - Cure progression comparison.
fig,ax=plt.subplots(figsize=(9,4.8))
for version in ['V1','V2']:
 u=T[(T.recipe_id==rec)&(T.model==version)&(T.node==5)]
 ax.plot(u.time_min,u.alpha,label=f'{version}, centre layer')
ax.axhline(.88,ls='--',color='gray',label='Illustrative conversion requirement')
ax.set(title='Centre-layer degree of cure and diffusion-limited kinetics',xlabel='Cycle time (min)',ylabel='Degree of cure (-)',ylim=(0,1.03));ax.grid(alpha=.25);ax.legend();save(fig,'fig02_cure_evolution')
# 03 - heat release in different models
fig,ax=plt.subplots(figsize=(9,4.8))
for version in ['V1','V2']:
 u=T[(T.recipe_id==rec)&(T.model==version)&(T.node==5)]
 ax.plot(u.time_min,u.heat_source_W_m3/1000,label=version)
ax.set(title='Chemical heat-release rate at the laminate centre',xlabel='Cycle time (min)',ylabel='Volumetric heat release (kW/m³)');ax.grid(alpha=.25);ax.legend();save(fig,'fig03_reaction_heat')
# 04 - final cure against process temperature, by kinetic model
fig,ax=plt.subplots(figsize=(9,4.8))
for v in ['V1','V2']:
 d=S[(S.model==v)&(S.thickness_mm==14)];x=d.groupby('hold_C').alpha_min.mean();ax.plot(x.index,x.values,'o-',label=v)
ax.axhline(.88,ls='--',color='gray')
ax.set(title='Cure completion versus dwell temperature at 14 mm',xlabel='Dwell temperature (°C)',ylabel='Minimum final degree of cure (-)');ax.grid(alpha=.25);ax.legend();save(fig,'fig04_cure_vs_hold_temperature')
# 05 - temperature peak versus thickness
fig,ax=plt.subplots(figsize=(9,4.8))
for v in ['V1','V2']:
 d=S[S.model==v].groupby('thickness_mm').peak_T_C.agg(['mean','min','max'])
 ax.errorbar(d.index,d['mean'],yerr=np.stack([d['mean']-d['min'],d['max']-d['mean']]),capsize=4,marker='o',label=v)
ax.axhline(196,ls='--',color='gray',label='Illustrative peak limit')
ax.set(title='Peak laminate temperature across thickness classes',xlabel='Laminate thickness (mm)',ylabel='Peak temperature (°C)');ax.grid(alpha=.25);ax.legend();save(fig,'fig05_peak_temperature_by_thickness')
# 06 process feasible 2-panel group
fig,ax=plt.subplots(figsize=(9,4.8))
for v in ['V1','V2']:
 d=S[S.model==v].groupby('hold_C').screening_guard.mean()
 ax.plot(d.index,100*d.values,'o-',label=v)
ax.set(title='Feasible operating-window fraction in synthetic study',xlabel='Dwell temperature (°C)',ylabel='Fraction passing all defined limits (%)',ylim=(-2,102));ax.grid(alpha=.25);ax.legend();save(fig,'fig06_feasibility_windows')
# 07 Tg development versus local temperature of model V2
fig,ax=plt.subplots(figsize=(9,4.8))
u=T[(T.recipe_id==rec)&(T.model=='V2')&(T.node==5)]
ax.plot(u.time_min,u.part_C,label='Laminate centre temperature');ax.plot(u.time_min,u.glass_transition_C,label='Estimated glass transition Tg')
ax.set(title='Vitrification tendency: increasing glass transition',xlabel='Cycle time (min)',ylabel='Temperature (°C)');ax.grid(alpha=.25);ax.legend();save(fig,'fig07_vitrification_transition')
# 08 gradient scatter peak vs final cure
fig,ax=plt.subplots(figsize=(9,4.8))
for v in ['V1','V2']:
 d=S[S.model==v];ax.scatter(d.alpha_min,d.peak_through_thickness_gradient_K,label=v,s=45,alpha=.73)
ax.axvline(.88,ls='--',color='gray');ax.axhline(32,ls=':',color='gray');ax.set(title='Cure-temperature uniformity relationship',xlabel='Minimum final degree of cure',ylabel='Maximum through-thickness ΔT (K)');ax.grid(alpha=.25);ax.legend();save(fig,'fig08_cure_gradient_tradeoff')
# 09 version-difference sensitivity versus hold
fig,ax=plt.subplots(figsize=(9,4.8))
d=C.merge(S[S.model=='V1'][['recipe_id','hold_C','thickness_mm']],on='recipe_id')
for th in sorted(d.thickness_mm.unique()):
 g=d[d.thickness_mm==th].groupby('hold_C').delta_alpha.mean()
 ax.plot(g.index,g.values,'o-',label=f'{th:.0f} mm')
ax.axhline(0,color='gray',lw=1);ax.set(title='Diffusion limitation effect on final conversion',xlabel='Dwell temperature (°C)',ylabel='V2 minus V1, minimum cure (-)');ax.grid(alpha=.25);ax.legend(title='Thickness');save(fig,'fig09_model_difference')
# 10 3D scientific operating surface from actual data
from mpl_toolkits.mplot3d import Axes3D  # noqa
fig=plt.figure(figsize=(9,5.6));ax=fig.add_subplot(111,projection='3d')
d=S[(S.model=='V2')&(S.thickness_mm==14)].groupby(['ramp_C_min','hold_C']).alpha_min.mean().reset_index();xx=d.ramp_C_min.unique();yy=d.hold_C.unique();X,Y=np.meshgrid(xx,yy,indexing='ij');Z=np.array([[float(d[(d.ramp_C_min==x)&(d.hold_C==y)].alpha_min.iloc[0]) for y in yy]for x in xx]);ax.plot_surface(X,Y,Z,cmap='viridis',edgecolor='#333333',linewidth=.25,alpha=.92);ax.set(xlabel='Ramp (°C/min)',ylabel='Dwell (°C)',zlabel='Final min cure (-)',title='V2 process operating surface, 14 mm');ax.view_init(elev=26,azim=-62);save(fig,'fig10_3d_process_surface')
