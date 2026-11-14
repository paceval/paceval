#!/usr/bin/env python3
"""Render figures solely from real paceval execution CSV results. No synthetic chart values."""
from pathlib import Path
import csv
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits.mplot3d import Axes3D
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';OUT=ROOT/'figures'
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'figure.facecolor':'white','savefig.facecolor':'white','font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
NAVY='#163447';TEAL='#097c8d';ORANGE='#db813f'
def get(file):
 with (R/file).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def save(fig,name):
 fig.savefig(OUT/f'{name}.png',dpi=200,bbox_inches='tight',pad_inches=.22)
 fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight',pad_inches=.22)
 plt.close(fig)
profile=get('thermal_profile.csv');p1=[r for r in profile if r['model']=='1'];p2=[r for r in profile if r['model']=='2']
T=np.array([float(r['T_K'])-273.15 for r in p1]);
# 01 signed curvature vs temperature
fig,ax=plt.subplots(figsize=(8.6,4.55))
for pp,label,col in [(p1,'V1: thermal-only',TEAL),(p2,'V2: cure shrinkage + modulus',ORANGE)]:ax.plot(T,[float(r['curvature_inv_m']) for r in pp],label=label,color=col,lw=2.2)
ax.axhline(0,color='#91a3a9',lw=.8);ax.set(xlabel='Package temperature (°C)',ylabel='Signed laminate curvature (1/m)',title='Thermal response differs between model versions');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'fig01_curvature_temperature')
# 02 warpage
fig,ax=plt.subplots(figsize=(8.6,4.5))
for pp,label,col in [(p1,'V1',TEAL),(p2,'V2',ORANGE)]:ax.plot(T,np.array([float(r['center_edge_warp_m']) for r in pp])*1e6,label=label,color=col,lw=2.1)
ax.axhline(100,color='#9b5864',ls='--',lw=.9);ax.axhline(-100,color='#9b5864',ls='--',lw=.9,label='Illustrative ±100 µm bound');ax.set(xlabel='Temperature (°C)',ylabel='Signed center-to-edge warpage (µm)',title='Predicted small-slope edge deflection');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'fig02_warpage_temperature')
# 03 peak interface stress
fig,ax=plt.subplots(figsize=(8.6,4.5))
for pp,label,col in [(p1,'V1',TEAL),(p2,'V2',ORANGE)]:ax.plot(T,np.array([float(r['peak_endpoint_stress_Pa']) for r in pp])/1e6,color=col,label=label,lw=2)
ax.axhline(150,color='#9b5864',ls='--',lw=1,label='Illustrative 150 MPa threshold');ax.set(xlabel='Temperature (°C)',ylabel='Maximum sampled endpoint stress (MPa)',title='Elastic stress screening, not a fracture criterion');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'fig03_stress_temperature')
# 04 across whole scenario set, same-case pair (do not imply measurements)
comps=get('model_comparison.csv');x=np.array([float(r['V1_warp_m'])*1e6 for r in comps]);y=np.array([float(r['V2_warp_m'])*1e6 for r in comps]);fig,ax=plt.subplots(figsize=(7.8,5.2))
col=np.array([float(r['T_K'])-273.15 for r in comps]);sc=ax.scatter(x,y,c=col,s=13,alpha=.48,cmap='viridis',rasterized=True);mn=min(min(x),min(y));mx=max(max(x),max(y));ax.plot([mn,mx],[mn,mx],color=NAVY,ls=':',lw=1);fig.colorbar(sc,ax=ax,label='Temperature (°C)');ax.set(xlabel='V1 signed edge deflection (µm)',ylabel='V2 signed edge deflection (µm)',title='Matched synthetic scenarios: impact of cure model');ax.grid(alpha=.15);save(fig,'fig04_matched_model_scenarios')
# 05 option-specific geometry-mismatch plane for exact selected sampled settings
screen=get('screening.csv');subset=[r for r in screen if r['model']=='2' and abs(float(r['T_K'])-298)<.1 and abs(float(r['W_m'])-.02)<1e-9 and abs(float(r['C3_invK'])-20e-6)<1e-10];h=sorted(set(float(r['H3_m']) for r in subset));b=sorted(set(float(r['beta']) for r in subset));z=np.full((len(b),len(h)),np.nan)
for r in subset:z[b.index(float(r['beta'])),h.index(float(r['H3_m']))]=abs(float(r['signed_center_edge_warpage_m']))*1e6
assert np.isfinite(z).all() and z.size==16
fig,ax=plt.subplots(figsize=(7.7,4.7));im=ax.imshow(z,origin='lower',aspect='auto',cmap='YlOrBr');ax.set_xticks(range(len(h)),[f'{v*1e6:.0f}' for v in h]);ax.set_yticks(range(len(b)),[f'{v*1e3:.1f}' for v in b]);ax.set(xlabel='Encapsulant thickness (µm)',ylabel='Post-gel shrinkage coefficient (‰)',title='V2: cure shrinkage and thickness design map');fig.colorbar(im,ax=ax,label='Absolute edge deflection (µm)');
for i in range(len(b)):
 for j in range(len(h)):ax.text(j,i,f'{z[i,j]:.0f}',ha='center',va='center',fontsize=9,color='black')
save(fig,'fig05_cure_design_map')
# 06 process cure trajectory
cure=get('cure_profile.csv');tm=np.array([float(r['time_s'])/3600 for r in cure]);fig,ax=plt.subplots(figsize=(8.6,4.4));ax.plot(tm,[float(r['degree_of_cure']) for r in cure],color=TEAL,lw=2.2);ax.set(xlabel='Process time (h)',ylabel='Degree of cure (fraction)',title='Stateful cure process with paceval-evaluated kinetics');ax.set_ylim(.4,1.01);ax.grid(alpha=.2);save(fig,'fig06_cure_degree_profile')
# 07 process temperature vs warpage (single plotted result, note temperature program in caption)
fig,ax=plt.subplots(figsize=(8.6,4.5));ax.plot(tm,[float(r['center_edge_warp_m'])*1e6 for r in cure],color=ORANGE,lw=2.2);ax.set(xlabel='Process time (h)',ylabel='V2 signed edge deflection (µm)',title='Illustrative dwell-and-cooling history');ax.grid(alpha=.2);save(fig,'fig07_time_resolved_warpage')
# 08 fixed scenario 3D deflection = graph evaluated on 41x41 coordinate array
shape=get('deflection_surface.csv');fig=plt.figure(figsize=(8.2,6));ax=fig.add_subplot(111,projection='3d')
for v,cmap,alpha in [('2','coolwarm',.9)]:
 rr=[r for r in shape if r['model']==v];n=41;X=np.array([float(r['x_m'])*1e3 for r in rr]).reshape(n,n);Y=np.array([float(r['y_m'])*1e3 for r in rr]).reshape(n,n);Z=np.array([float(r['deflection_m'])*1e6 for r in rr]).reshape(n,n);ax.plot_surface(X,Y,Z,cmap=cmap,alpha=alpha,rstride=2,cstride=2,edgecolor='none',antialiased=True)
ax.set(xlabel='x (mm)',ylabel='y (mm)',zlabel='Deflection (µm)',title='V2: idealized two-dimensional small-slope surface');ax.view_init(elev=24,azim=-58);save(fig,'fig08_warpage_surface_3d')
# 09 signed sensitivity plot actual graph
fig,ax=plt.subplots(figsize=(8.6,4.6));ax.plot(T,[float(r['dcurvature_dT_inv_mK']) for r in p1],label='V1',color=TEAL,lw=2);ax.plot(T,[float(r['dcurvature_dT_inv_mK']) for r in p2],label='V2',color=ORANGE,lw=2);ax.set(xlabel='Temperature (°C)',ylabel='Partial curvature / partial T [1/(m K)]',title='Analytic fixed-cure temperature sensitivity');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'fig09_temperature_sensitivity')
# 10 guard outcomes statistics from actual 1280 scenario grid
v1=[r for r in screen if r['model']=='1'];v2=[r for r in screen if r['model']=='2'];count=[sum(float(r['screen_guard'])>0.5 for r in rr) for rr in (v1,v2)];fig,ax=plt.subplots(figsize=(6.4,4.4));bars=ax.bar(['V1 thermal-only','V2 thermal + cure'],count,color=[TEAL,ORANGE],width=.55);ax.set(xlabel='Mathematical model',ylabel='Scenarios meeting illustrative bounds',title='Guard evaluation over identical input grid');ax.set_ylim(0,1280);ax.bar_label(bars,padding=5,fontsize=11);ax.grid(axis='y',alpha=.15);save(fig,'fig10_screen_guard_counts')
print('Generated 10 figures as PNG and vector PDF from actual paceval result CSV.')
