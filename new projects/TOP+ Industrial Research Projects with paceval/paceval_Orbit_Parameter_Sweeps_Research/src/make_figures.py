#!/usr/bin/env python3
"""Rebuild every scientific figure from the actual C++/paceval output CSVs.
The title artwork is a separate, explicitly conceptual illustration.
Dependencies: numpy, matplotlib. Figures are not fabricated by image generation.
"""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'examples';OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
C='#142a42';BLUE='#087ead';ORANGE='#e87e38';GREEN='#16a389';PURPLE='#8458a0'
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'font.family':'DejaVu Sans',
 'figure.facecolor':'white','savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
def load(name):
 with open(DATA/name,newline='') as f:return list(csv.DictReader(f))
def nums(rows,key):return np.array([float(r[key]) for r in rows])
def save(fig,name):
 for ext in ('png','pdf'):
  fig.savefig(OUT/(name+'.'+ext),dpi=180,bbox_inches='tight',pad_inches=.18)
 plt.close(fig)
S={name:load('orbit_'+name+'.csv') for name in ['two_body','half_J2','nominal_J2','high_J2','drag_only','J2_drag','J2_drag_x10','J2_drag_x100','gravity_low','gravity_high']}
SU=load('scenario_summary.csv');SW=load('parameter_surface.csv')
# 1. System boundary: architecture graphic, mathematical rather than simulation output.
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(11.4,2.75));ax.set_xlim(0,12);ax.set_ylim(0,2);ax.axis('off')
boxes=[('Frozen physical\nparameters',0.1),('3 reusable paceval\nacceleration graphs',2.55),('Host RK4\nstate integration',5.0),('Independent native\n& analytical checks',7.45),('CSV trajectory\n& scientific figures',9.9)]
for i,(label,x) in enumerate(boxes):
 ax.add_patch(FancyBboxPatch((x,.8),1.9,.78,boxstyle='round,pad=.10,rounding_size=.13',facecolor='#e9f4f7',edgecolor=BLUE,lw=1.7));ax.text(x+.95,1.18,label,ha='center',va='center',fontsize=8.8,color=C,fontweight='bold')
 if i<4:ax.annotate('',xy=(x+2.36,1.2),xytext=(x+1.98,1.2),arrowprops=dict(arrowstyle='-|>',color=ORANGE,lw=1.7))
ax.text(6,.35,'Host handles integration, coordinate units and data checks; paceval evaluates persistent expressions.',ha='center',fontsize=9,color='#586b7d')
save(fig,'01_execution_architecture')
# 2. True spatial paths
fig=plt.figure(figsize=(10.5,6.2));ax=fig.add_subplot(111,projection='3d')
for name,label,col in [('two_body','Point mass',BLUE),('nominal_J2','J2 gravity',ORANGE),('J2_drag_x100','J2 + illustrative drag ×100',GREEN)]:
 rows=S[name];ax.plot(nums(rows,'x_km'),nums(rows,'y_km'),nums(rows,'z_km'),color=col,lw=1.65,label=label)
u=np.linspace(0,2*np.pi,38);v=np.linspace(0,np.pi,22)
x=6378.137*np.outer(np.cos(u),np.sin(v));y=6378.137*np.outer(np.sin(u),np.sin(v));z=6378.137*np.outer(np.ones_like(u),np.cos(v))
ax.plot_surface(x,y,z,color='#abc5d2',alpha=.22,linewidth=0,shade=True)
ax.set(xlabel='ECI x (km)',ylabel='ECI y (km)',zlabel='ECI z (km)',title='Computed inclined orbits: actual paceval force evaluations');ax.set_box_aspect((1,1,.85));ax.view_init(24,-52);ax.legend(loc='upper left',fontsize=8);save(fig,'02_3d_orbits')
# 3 RAAN node precession
fig,ax=plt.subplots(figsize=(10.4,4.8))
for name,label,col in [('two_body','Two-body',BLUE),('half_J2','J2 × 0.5',GREEN),('nominal_J2','J2 nominal',ORANGE),('high_J2','J2 × 1.5',PURPLE)]:
 rows=S[name];ax.plot(nums(rows,'time_s')/3600,nums(rows,'raan_deg'),label=label,color=col)
ax.set(xlabel='Elapsed propagation time (hours)',ylabel='Osculating RAAN (degrees)',title='J2 perturbation changes the orbital plane');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'03_j2_node_evolution')
# 4 alt timeline
fig,ax=plt.subplots(figsize=(10.4,4.8))
for name,label,col in [('two_body','Two-body',BLUE),('nominal_J2','J2',ORANGE),('J2_drag_x10','J2 + density ×10',GREEN),('J2_drag_x100','J2 + density ×100',PURPLE)]:
 rows=S[name];ax.plot(nums(rows,'time_s')/3600,nums(rows,'altitude_km'),label=label,color=col)
ax.set(xlabel='Elapsed time (hours)',ylabel='Geocentric altitude r − Re (km)',title='Osculating altitude under selected force variants');ax.legend(fontsize=9,frameon=False);ax.grid(alpha=.2);save(fig,'04_altitude_history')
# 5 parameter surface fixed short horizon
j2=sorted(set(float(r['j2_scale']) for r in SW));drag=sorted(set(float(r['drag_scale']) for r in SW))
Z=np.empty((len(j2),len(drag)));N=np.empty_like(Z)
for r in SW:
 i=j2.index(float(r['j2_scale']));k=drag.index(float(r['drag_scale']));Z[i,k]=float(r['final_altitude_km']);N[i,k]=float(r['final_raan_deg'])
X,Y=np.meshgrid(drag,j2)
fig=plt.figure(figsize=(10.4,5.9));ax=fig.add_subplot(projection='3d');surf=ax.plot_surface(X,Y,Z,cmap='viridis',edgecolor='#213d57',linewidth=.18)
fig.colorbar(surf,ax=ax,shrink=.68,label='Final altitude (km)',pad=.12);ax.set(xlabel='Density scale (illustrative)',ylabel='J2 scale',zlabel='Altitude (km)',title='49 paceval-propagated parameter cases at 1 hour');ax.view_init(26,-53);save(fig,'05_parameter_surface')
# 6 node parameter map
fig,ax=plt.subplots(figsize=(9.7,5.1));im=ax.imshow(N,origin='lower',aspect='auto',cmap='coolwarm',extent=(min(drag),max(drag),min(j2),max(j2)));fig.colorbar(im,ax=ax,label='RAAN (deg)');ax.set(xlabel='Density scale',ylabel='J2 multiplier',title='Computed RAAN response, 49-scenario sweep');save(fig,'06_parameter_raan_map')
# 7 conservative specific energy drift
fig,ax=plt.subplots(figsize=(10.4,4.7))
for name,label,col in [('two_body','Two-body',BLUE),('nominal_J2','Conservative J2',ORANGE),('J2_drag_x100','J2 + density ×100',GREEN)]:
 rows=S[name];energy=nums(rows,'specific_energy_km2_s2');ax.plot(nums(rows,'time_s')/3600,energy-energy[0],label=label,color=col)
ax.set(xlabel='Time (h)',ylabel='Specific energy change (km²/s²)',title='Conservative invariants and dissipative drag cases');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'07_energy_audit')
# 8 numerical independent comparisons
fig,ax=plt.subplots(figsize=(10.4,4.7));values=[];labels=[]
for name in ['two_body','nominal_J2','J2_drag','J2_drag_x100']:
 vals=nums(S[name],'position_difference_km');values.append(np.maximum(vals,1e-17));labels.append(name)
for i,(vals,label) in enumerate(zip(values,labels)):ax.plot(np.arange(len(vals))/60,vals,label=label,lw=1.4)
ax.set(yscale='log',xlabel='Time (h)',ylabel='|paceval path − independent native path| (km)',title='Full RK4 trajectory agreement, separate acceleration implementation');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'08_position_difference')
# 9 sensitivity summary
fig,ax=plt.subplots(figsize=(10.5,4.6));ids=[x['scenario'] for x in SU];node=[float(x['final_raan_deg']) for x in SU];colors=[ORANGE if 'J2' in x else BLUE for x in ids]
ax.barh(ids,node,color=colors);ax.invert_yaxis();ax.set(xlabel='Final osculating RAAN (degrees)',title='Six-hour analytical-kernel scenario sweep');ax.grid(axis='x',alpha=.2);save(fig,'09_scenario_node_comparison')
print('Generated 9 PNG and 9 vector PDF graphics from paceval CSV outputs.')
