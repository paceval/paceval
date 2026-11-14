#!/usr/bin/env python3
"""Reproducible WP10 scientific figures from REAL C++/paceval CSV outputs.
Scientific figures are never generated from independent reference model curves.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D # noqa: F401
R=Path(__file__).resolve().parents[1]
D=R/'results';O=R/'figures';O.mkdir(exist_ok=True)
s=pd.read_csv(D/'screening.csv');e=pd.read_csv(D/'torque_speed_envelope.csv');r=pd.read_csv(D/'efficiency_recommended.csv');c=pd.read_csv(D/'model_comparison.csv')
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.titleweight':'semibold','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(name):
    plt.tight_layout(pad=1.5)
    plt.savefig(O/(name+'.png'),dpi=185,bbox_inches='tight')
    plt.savefig(O/(name+'.pdf'),bbox_inches='tight')
    plt.close()

def sel(frame,v=2,t=110):return frame[(frame.model==v)&(frame.temperature_C==t)].copy()
# 01: torque-speed envelope on actual finite current grid.
fig,ax=plt.subplots(figsize=(8.6,5.2))
for version in [1,2]:
 for temp in [25,110]:
  x=sel(e,version,temp).sort_values('speed_rpm');ax.plot(x.speed_rpm,x.max_feasible_torque_Nm,marker='o',ms=3.5,label=f'V{version}, {temp}°C')
ax.set(xlabel='Mechanical speed (rpm)',ylabel='Maximum feasible electromagnetic torque (N m)',title='Finite-grid torque–speed envelopes');ax.legend(ncol=2,fontsize=9);ax.grid(alpha=.22)
save('fig01_torque_speed_envelope')
# 02 field weakening current shift in hot V2.
fig,ax=plt.subplots(figsize=(8.6,5.2))
for temp in [25,110]:
 z=sel(e,2,temp).sort_values('speed_rpm');ax.plot(z.speed_rpm,z.id_Apeak,marker='s',ms=3,label=f'V2, {temp}°C')
ax.set(xlabel='Mechanical speed (rpm)',ylabel='Selected d-axis peak current (A)',title='Negative d-axis current in the voltage-constrained region');ax.legend();ax.grid(alpha=.22)
save('fig02_field_weakening_current')
# 03 finite torque/speed bin efficiency, max observed among sampled currents, not interpolation.
x=sel(s,2,110);x=x[(x.feasible_guard>0.5)&(x.shaft_power_W>0)]
bins=np.linspace(0,240,25);x=x.copy();x['torque_bin']=pd.cut(x.torque_Nm,bins,labels=False,include_lowest=True)
mat=np.full((24,len(np.sort(x.speed_rpm.unique()))),np.nan);speeds=np.sort(x.speed_rpm.unique());mapping={v:i for i,v in enumerate(speeds)}
for (sp,b),group in x.groupby(['speed_rpm','torque_bin']):
 if pd.notna(b):mat[int(b),mapping[sp]]=group.efficiency.max()*100
fig,ax=plt.subplots(figsize=(8.6,5.2));m=ax.imshow(mat,origin='lower',aspect='auto',extent=[speeds[0]-250,speeds[-1]+250,bins[0],bins[-1]],vmin=70,vmax=100,cmap='viridis');fig.colorbar(m,ax=ax,label='Maximum sampled shaft efficiency (%)')
ax.set(xlabel='Mechanical speed (rpm)',ylabel='Electromagnetic torque bin (N m)',title='V2 at 110°C: observed efficiency over the torque–speed plane')
save('fig03_efficiency_map')
# 04 current and voltage geometry current plane from actual feasibility mask.
fig,axes=plt.subplots(1,2,figsize=(10,4.8),sharex=True,sharey=True)
for ax,rpm in zip(axes,[3000,9000]):
 x=sel(s,2,110);x=x[x.speed_rpm==rpm];idx=np.sort(x.id_Apeak.unique());q=np.sort(x.iq_Apeak.unique());z=x.pivot(index='iq_Apeak',columns='id_Apeak',values='feasible_guard').reindex(index=q,columns=idx).values
 ax.imshow(z,origin='lower',extent=[idx[0]-6,idx[-1]+6,q[0]-6,q[-1]+6],aspect='auto',vmin=0,vmax=1,cmap='viridis');ax.set(title=f'{rpm:,} rpm',xlabel='d-axis current (A peak)');ax.grid(alpha=.1)
axes[0].set_ylabel('q-axis current (A peak)');fig.suptitle('V2 at 110°C: feasible current vectors under both physical limits',y=1.02)
save('fig04_current_plane_feasibility')
# 05 loss contributions on feasible torque maximizing trajectory, all from paceval.
fr=sel(e,2,110).sort_values('speed_rpm');full=sel(s,2,110)
joined=fr.merge(full,on=['speed_rpm','id_Apeak','iq_Apeak','temperature_C','model'],suffixes=('_env',''))
fig,ax=plt.subplots(figsize=(8.6,5.2))
for field,label in [('copper_loss_W','Copper'),('iron_loss_W','Iron proxy'),('mechanical_loss_W','Mechanical proxy')]:ax.plot(joined.speed_rpm,joined[field]/1000,marker='.',label=label)
ax.set(title='V2 at 110°C: loss composition at maximum feasible torque',xlabel='Mechanical speed (rpm)',ylabel='Modeled loss (kW)');ax.legend();ax.grid(alpha=.22)
save('fig05_loss_decomposition')
# 06 voltage utilization along envelope.
fig,ax=plt.subplots(figsize=(8.6,5.2))
for v in [1,2]:
 z=sel(e,v,110).sort_values('speed_rpm');ax.plot(z.speed_rpm,z.voltage_V/(600/np.sqrt(3)),marker='o',ms=3,label=f'V{v} at 110°C')
ax.axhline(1,linestyle='--',label='Nominal inverter voltage limit')
ax.set(title='Voltage-constraint proximity along selected torque envelope',xlabel='Mechanical speed (rpm)',ylabel='Voltage utilization ratio');ax.legend();ax.grid(alpha=.22)
save('fig06_voltage_limit_utilization')
# 07 temperature-aware torque differences versus speed at the same current pair.
fig,ax=plt.subplots(figsize=(8.6,5.2))
for temp in [25,110]:
 z=c[(c.temperature_C==temp)&(c.case_id.isin(s[(s.id_Apeak==-120)&(s.iq_Apeak==180)&(s.temperature_C==temp)].case_id))].sort_values('speed_rpm')
 ax.plot(z.speed_rpm,z.delta_torque_Nm,marker='o',ms=3,label=f'{temp}°C')
ax.set(title='At fixed currents: V2 minus V1 electromagnetic torque',xlabel='Mechanical speed (rpm)',ylabel='Torque difference (N m)');ax.legend();ax.grid(alpha=.22)
save('fig07_temperature_model_delta')
# 08 power and torque for hot version (electromagnetic envelope is not shaft power).
fig,ax=plt.subplots(figsize=(8.6,5.2));z=sel(e,2,110).sort_values('speed_rpm')
ax.plot(z.speed_rpm,z.max_feasible_torque_Nm,label='Electromagnetic torque (N m)')
ax2=ax.twinx();power=joined.sort_values('speed_rpm')['em_power_W'].to_numpy()/1000
ax2.plot(z.speed_rpm,power,linestyle='--',label='Electromagnetic power (kW)')
ax.set(title='V2 at 110°C: torque envelope and electromagnetic power',xlabel='Mechanical speed (rpm)',ylabel='Torque (N m)');ax2.set_ylabel('Electromagnetic power (kW)');ax.grid(alpha=.22)
lines=ax.get_lines()+ax2.get_lines();ax.legend(lines,[l.get_label() for l in lines],loc='best')
save('fig08_envelope_torque_and_power')
# 09 optimal feasible shaft efficiency at fixed torque target.
fig,ax=plt.subplots(figsize=(8.6,5.2))
for v in [1,2]:
 z=sel(r,v,110).sort_values('speed_rpm');ax.plot(z.speed_rpm,z.best_efficiency*100,marker='o',ms=4,label=f'V{v} at 110°C')
ax.set(title='Best sampled shaft efficiency while delivering ≥120 N m',xlabel='Mechanical speed (rpm)',ylabel='Efficiency (%)');ax.legend();ax.grid(alpha=.22)
save('fig09_target_torque_optimal_efficiency')
# 10 verified 3D torque function from paceval along current plane.
z=sel(s,2,110);z=z[z.speed_rpm==4000];piv=z.pivot(index='iq_Apeak',columns='id_Apeak',values='torque_Nm');ids=piv.columns.to_numpy();iqs=piv.index.to_numpy();X,Y=np.meshgrid(ids,iqs);Z=piv.to_numpy()
fig=plt.figure(figsize=(8.6,6.0));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(X,Y,Z,cmap='viridis',linewidth=0,antialiased=True,alpha=.9)
ax.set(xlabel='d current (A peak)',ylabel='q current (A peak)',zlabel='Torque (N m)',title='V2, 110°C, 4,000 rpm: computed electromagnetic torque surface');ax.view_init(elev=26,azim=-62)
fig.colorbar(surf,ax=ax,shrink=.55,pad=.08,label='Torque (N m)');save('fig10_3d_torque_current_surface')
# 11 Analytic d-axis torque sensitivity on selected envelope.
fig,ax=plt.subplots(figsize=(8.6,5.2));z=joined.sort_values('speed_rpm');ax.plot(z.speed_rpm,z.dtorque_did_Nm_perA,marker='o',ms=3,label='dTe/dId')
ax.plot(z.speed_rpm,z.dtorque_diq_Nm_perA,marker='s',ms=3,label='dTe/dIq');ax.set(title='V2 at 110°C: paceval analytical torque sensitivities',xlabel='Mechanical speed (rpm)',ylabel='Torque sensitivity (N m/A)');ax.legend();ax.grid(alpha=.22)
save('fig11_torque_sensitivities')
print('GENERATED:',len(list(O.glob('fig*.png'))),'scientific PNGs and vector PDFs from original paceval CSV outputs')
