#!/usr/bin/env python3
"""Draw domain-specific scientific figures exclusively from executed paceval CSV results."""
from pathlib import Path
import csv, json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
root=Path(__file__).resolve().parents[1];R=root/'results';D=root/'figures';D.mkdir(exist_ok=True)

def rows(name):return list(csv.DictReader(open(R/name)))
S=rows('vle_samples.csv'); C=rows('column_configurations.csv'); B=rows('isobaric_equilibrium_curves.csv')
def vsets(rows):return {v:[r for r in rows if int(r['version'])==v] for v in (1,2)}
s=vsets(S);c=vsets(C);b=vsets(B)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.grid':True,'grid.alpha':.22,'savefig.facecolor':'white'})
COL={1:'#0C747C',2:'#D25D30'}
def nums(rows,k):return np.array([float(r[k]) for r in rows])
def save(fig,name):
 fig.savefig(D/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.20)
 fig.savefig(D/(name+'.pdf'),bbox_inches='tight',pad_inches=.20)
 plt.close(fig)
def plot_lines(name,yname,ylab,title):
 fig,ax=plt.subplots(figsize=(8,4.6))
 for v in (1,2):ax.plot(nums(b[v],'x'),nums(b[v],yname),lw=2.2,label=f'Model v{v}',color=COL[v]);
 ax.set(title=title,xlabel='Liquid benzene mole fraction x',ylabel=ylab);ax.legend();save(fig,name)
plot_lines('01_isobaric_vle','vapor_y','Vapor benzene mole fraction y','Isobaric VLE at 0.6 bar')
plot_lines('02_bubble_temperature','bubble_temperature_K','Bubble temperature [K]','Antoine-based isobaric bubble-temperature profile')
fig,ax=plt.subplots(figsize=(8,4.6));
for v in (1,2):ax.scatter(nums(s[v],'T_K')[::2],nums(s[v],'alpha_eff')[::2],s=2,alpha=.2,color=COL[v],label=f'v{v}')
ax.set(xlabel='Sample temperature [K]',ylabel='Effective relative volatility',title='Relative volatility: fixed vs. temperature/composition dependent');ax.legend(markerscale=4);save(fig,'03_relative_volatility')
fig=plt.figure(figsize=(8.3,5.5));ax=fig.add_subplot(111,projection='3d');A=s[2][::5];ax.plot_trisurf(nums(A,'x'),nums(A,'T_K'),nums(A,'y'),cmap='viridis',linewidth=0,alpha=.9)
ax.set(xlabel='Liquid benzene x',ylabel='Temperature [K]',zlabel='Vapor benzene y',title='Model v2: evaluated VLE surface');ax.view_init(elev=25,azim=-55);save(fig,'04_vle_surface')
fig,ax=plt.subplots(figsize=(8,4.6))
for v in (1,2):
  indices=np.argsort(nums(s[v],'x'));x=nums(s[v],'x')[indices];dy=nums(s[v],'dy_dx')[indices];ax.scatter(x[::4],dy[::4],s=5,alpha=.3,color=COL[v],label=f'v{v}')
ax.set(xlabel='Liquid composition x',ylabel='d(vapor y)/dx',title='Analytic composition sensitivity');ax.legend();save(fig,'05_vle_composition_sensitivity')
fig,ax=plt.subplots(figsize=(8,4.6))
for v in (1,2):ax.scatter(nums(s[v],'x')[::3],(nums(s[v],'y')-nums(s[v],'x'))[::3],s=5,alpha=.25,color=COL[v],label=f'v{v}')
ax.set(xlabel='Liquid mole fraction x',ylabel='Vapor enrichment y - x',title='Single-contact vapor enrichment');ax.legend();save(fig,'06_vapor_enrichment')
fig,ax=plt.subplots(figsize=(8,4.6))
for v in (1,2):ax.scatter(nums(c[v],'reflux')[::2],nums(c[v],'reboiler_kW')[::2],s=10,alpha=.4,color=COL[v],label=f'v{v}')
ax.set(xlabel='Reflux ratio R',ylabel='Reboiler heat-duty proxy [kW]',title='Heat-duty response across synthetic column configurations');ax.legend();save(fig,'07_heat_duty_reflux')
fig,ax=plt.subplots(figsize=(8,4.6));bins=np.arange(0,38,2)
for v in (1,2):ax.hist(nums(c[v],'stage_count'),bins=bins,histtype='step',lw=2,color=COL[v],label=f'v{v}')
ax.set(xlabel='Idealized stage count (negative = infeasible)',ylabel='Column scenarios',title='McCabe-Thiele-style stagewise screening');ax.legend();save(fig,'08_stage_count_distribution')
fig,ax=plt.subplots(figsize=(8,4.6))
for v in (1,2):ax.scatter(nums(c[v],'reflux')[::2],nums(c[v],'stage_count')[::2],s=12,alpha=.4,color=COL[v],label=f'v{v}')
ax.set(xlabel='Reflux ratio R',ylabel='Calculated stage count',title='Stage count dependence on reflux and composition');ax.legend();save(fig,'09_stage_count_reflux')
fig,ax=plt.subplots(figsize=(8,4.6));
for v in (1,2):ax.hist(nums(s[v],'heat_margin_kW'),bins=40,alpha=.45,label=f'v{v}',color=COL[v]);
ax.axvline(0,ls='--',color='gray');ax.set(xlabel='Heat capacity margin [kW]',ylabel='Evaluated rows',title='Heat-duty feasibility margin');ax.legend();save(fig,'10_heat_margin')
fig,ax=plt.subplots(figsize=(7.5,4.6));v=[1,2];counts=[int((nums(s[j],'vle_quality_indicator')>0.5).sum()) for j in v];ax.bar([f'v{j}' for j in v],counts,color=[COL[j] for j in v]);ax.set(ylabel='Accepted sample records',title='Combined synthetic mathematical quality decision');save(fig,'11_guard_decisions')
fig,ax=plt.subplots(figsize=(8,4.6))
for v in (1,2):ax.scatter(nums(c[v],'distillate_kmol_h'),nums(c[v],'bottoms_kmol_h'),s=9,alpha=.25,color=COL[v],label=f'v{v}')
ax.plot([32,66],[68,34],ls='--',color='gray',lw=1);ax.set(xlabel='Distillate D [kmol/h]',ylabel='Bottoms B [kmol/h]',title='Mass-balanced stream split at F = 100 kmol/h');ax.legend();save(fig,'12_mass_balance')
print('Created',len(list(D.glob('*.pdf'))),'quantitative figures from executed paceval files')
