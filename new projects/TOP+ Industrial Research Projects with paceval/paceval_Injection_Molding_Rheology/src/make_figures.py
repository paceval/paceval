#!/usr/bin/env python3
"""Produce scientific charts only from actually observed paceval MCP decimal outputs.
Do not substitute independently calculated values for reported paceval values.
"""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from mpl_toolkits.mplot3d import Axes3D # noqa: F401
R=Path(__file__).resolve().parents[1];OUT=R/'figures'
navy='#1c2b43';steel='#5e7791';teal='#0b8b96';pink='#c33b75';orange='#d58943';light='#f4f7fa'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':14,'axes.labelsize':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':navy,'text.color':navy,'axes.titleweight':'bold','axes.edgecolor':'#8a9bac','figure.facecolor':'white','savefig.facecolor':'white','grid.alpha':.16})
def rows(n):return list(csv.DictReader((R/'results'/n).open()))
a=rows('mcp_grid_observed.csv');d=rows('mcp_rheology_diagnostics.csv')
q=np.array(sorted({float(z['Q_m3s']) for z in a}));ts=np.array(sorted({float(z['T_K']) for z in a}));
def matrix(key):return np.array([[float(next(z[key] for z in a if float(z['Q_m3s'])==u and float(z['T_K'])==t)) for u in q] for t in ts])
p1=matrix('pressure_v1_Pa')/1e6;p2=matrix('pressure_v2_Pa')/1e6;g1=matrix('guard_v1');g2=matrix('guard_v2');score=matrix('score_v2')
def save(fig,filename):fig.savefig(OUT/(filename+'.png'),dpi=190,bbox_inches='tight',pad_inches=.16);fig.savefig(OUT/(filename+'.pdf'),bbox_inches='tight',pad_inches=.16);plt.close(fig)
# 01 actual two model pressures at three temperatures
fig,ax=plt.subplots(figsize=(10.1,5.3))
for j,t in [(1,482),(3,506),(5,530)]:
 ax.plot(q*1e6,p1[j],':',color=[teal,steel,orange][(j-1)//2],lw=1.6,marker='o',ms=4,label=f'Apparent proxy, {t} K')
 ax.plot(q*1e6,p2[j],'-',color=[teal,steel,orange][(j-1)//2],lw=2.4,marker='s',ms=4,label=f'Power-law corrected, {t} K')
ax.set(xlabel='Volumetric flow (mL/s)',ylabel='Two-segment pressure drop (MPa)',title='Two physically distinct pressure kernels at fixed melt temperature')
ax.grid(True);ax.legend(ncol=2,fontsize=8,loc='upper left');save(fig,'01_pressure_models_actual_mcp')
# 02 show acceptance shift
fig,axes=plt.subplots(1,2,figsize=(11.1,5.3),sharex=True,sharey=True)
cm=ListedColormap(['#f6c4b9','#addcd5']);norm=BoundaryNorm([-.5,.5,1.5],cm.N)
for ax,z,title in [(axes[0],g1,'v1 · Apparent-viscosity proxy'),(axes[1],g2,'v2 · Analytical power-law correction')]:
 ax.imshow(z,origin='lower',aspect='auto',cmap=cm,norm=norm,extent=[q[0]*1e6-2.5,q[-1]*1e6+2.5,ts[0]-6,ts[-1]+6])
 ax.set_title(title);ax.set_xlabel('Flow (mL/s)');ax.set_xticks(q*1e6);ax.set_yticks(ts);ax.grid(False)
axes[0].set_ylabel('Melt temperature (K)')
fig.suptitle('Synthetic operating-window flags · actual paceval logical graphs',fontsize=14,fontweight='bold',color=navy)
fig.text(.5,.035,'Mint = mathematically admissible; coral = at least one constraint exceeded',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.055,1,.93]);save(fig,'02_operating_window_actual_mcp')
# 03 deviation field
fig,ax=plt.subplots(figsize=(9.3,5.5));im=ax.imshow((p2-p1)*1000,origin='lower',aspect='auto',cmap='magma',extent=[q[0]*1e6-2.5,q[-1]*1e6+2.5,ts[0]-6,ts[-1]+6])
ax.set(title='Added pressure from the power-law wall-shear correction',xlabel='Flow (mL/s)',ylabel='Melt temperature (K)');ax.set_xticks(q*1e6);ax.set_yticks(ts);cb=fig.colorbar(im,ax=ax);cb.set_label('v2 − v1 pressure (kPa)');save(fig,'03_pressure_model_difference_actual_mcp')
# 04 3D mathematical score surface
Q,T=np.meshgrid(q*1e6,ts);fig=plt.figure(figsize=(10,6.5));ax=fig.add_subplot(projection='3d');ax.plot_surface(Q,T,score,cmap='coolwarm',edgecolor='#f4f7fa',linewidth=.45,alpha=.98)
ax.set(xlabel='Flow (mL/s)',ylabel='Temperature (K)',zlabel='Dimensionless signed score',title='Version 2 · full compound mathematical process-window score');ax.view_init(elev=27,azim=-128);fig.tight_layout();save(fig,'04_score_surface_actual_mcp')
# 05 actual rheology diagnostic at fixed temperature
gamma=np.array([float(z['gammaA_s-1']) for z in d]);ep=np.array([float(z['etaPowerA_Pas']) for z in d]);ec=np.array([float(z['etaCrossA_Pas']) for z in d]);
fig,ax=plt.subplots(figsize=(9.8,5.25));ax.plot(gamma,ep,'o-',c=teal,lw=2.4,label='Power-law apparent viscosity');ax.plot(gamma,ec,'s-',c=pink,lw=2.4,label='Regularized Cross-Arrhenius diagnostic');ax.set(xlabel='Nominal wall shear rate, segment A (1/s)',ylabel='Apparent viscosity (Pa s)',title='Rheological kernel alternatives at 506 K');ax.grid(True);ax.legend(loc='best');fig.text(.1,.015,'Synthetic non-calibrated coefficients: comparing functional forms only',fontsize=8,color=steel);save(fig,'05_rheology_models_actual_mcp')
# 06 sensitivity from *executed* analytical graphs
sQ=np.array([float(z['dP_dQ_v2_Pas_m3']) for z in d]);sT=np.array([float(z['dP_dT_v2_PaK']) for z in d]);
fig,ax=plt.subplots(figsize=(9.5,5.3));ax.plot(q*1e6,sQ*1e-9,'o-',c=teal,lw=2.3,label='d(pressure)/dQ');ax.set(xlabel='Flow (mL/s)',ylabel='dP/dQ (GPa per m³/s)',title='Actual paceval analytical sensitivity graphs · 506 K');ax2=ax.twinx();ax2.plot(q*1e6,sT/1000,'s--',c=pink,lw=2.0,label='d(pressure)/dT');ax2.set_ylabel('dP/dT (kPa/K)');ax.grid(True);save(fig,'06_pressure_sensitivities_actual_mcp')
# 07 TINC widths only and center values from actual interface
xx=json.loads((R/'results/tinc_point_samples.json').read_text())['scenarios'];labels=[x['case'] for x in xx];widths=[float(x['pressure_v2']['hi'])-float(x['pressure_v2']['lo']) for x in xx];
fig,ax=plt.subplots(figsize=(9.3,4.5));ax.bar(labels,[x*1e9 for x in widths],color=teal);ax.set(title='Pointwise TINC returned pressure interval widths',xlabel='Synthetic point test',ylabel='Printed width × 10⁹ (Pa)',ylim=(0,max(widths)*1e9*1.3));ax.grid(True,axis='y');fig.text(.12,.02,'These are point-rounding intervals, NOT measurement or material-property uncertainty bands.',fontsize=8,color=steel);save(fig,'07_tinc_point_widths_actual_mcp')
print('Created 7 scientific figures in PNG and vector PDF from archived actual MCP values')
