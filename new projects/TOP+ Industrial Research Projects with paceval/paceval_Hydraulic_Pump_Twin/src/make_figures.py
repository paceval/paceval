#!/usr/bin/env python3
"""All numbered science plots derive from persisted original-SDK paceval output CSVs."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'figures';F.mkdir(exist_ok=True)
s=pd.read_csv(ROOT/'examples/paceval_operating_sweep.csv')
a=pd.read_csv(ROOT/'examples/paceval_operating_surface.csv')
t=pd.read_csv(ROOT/'examples/paceval_operating_trace.csv')
v=pd.read_csv(ROOT/'examples/paceval_formula_version_profile.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.titlesize':12,'axes.labelsize':10,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(fig,name):
 fig.savefig(F/(name+'.png'),dpi=190,bbox_inches='tight',facecolor='white')
 fig.savefig(F/(name+'.pdf'),bbox_inches='tight',facecolor='white')
 plt.close(fig)
# 1 actual pump and system head values for sampled Q,n
fig,ax=plt.subplots(figsize=(9,5));sc=ax.scatter(s.q_m3s,s.head_pump_m,c=s.speed_ratio,s=6,cmap='viridis',alpha=.67,rasterized=True);ax.scatter(s.q_m3s,s.head_system_m,s=4,c='orangered',alpha=.22,rasterized=True,label='System head, sampled scenarios');ax.set(xlabel='Flow Q (m³/s)',ylabel='Head (m)',title='Pump-head values and network system head — paceval sweep');fig.colorbar(sc,ax=ax,label='Pump speed ratio n');ax.legend(loc='upper left');ax.grid(alpha=.16);save(fig,'01_pump_and_system_head_sweep')
# 2 efficiency q n scatter
fig,ax=plt.subplots(figsize=(9,5));p=ax.scatter(s.q_m3s,s.efficiency_base,c=s.speed_ratio,s=7,cmap='plasma',alpha=.72,rasterized=True);ax.set(xlabel='Pump flow Q (m³/s)',ylabel='Hydraulic efficiency η',title='Actual paceval synthetic efficiency over sampled flow and speed');fig.colorbar(p,ax=ax,label='Speed ratio');ax.grid(alpha=.18);save(fig,'02_efficiency_scatter')
# 2D grid
sp=np.sort(a.speed_ratio.unique());hs=np.sort(a.static_head_m.unique());S=len(sp);T=len(hs)
def matrix(key):return a.pivot(index='static_head_m',columns='speed_ratio',values=key).loc[hs,sp].values
X,Y=np.meshgrid(sp,hs)
# 3 3D surface Q
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(projection='3d');obj=ax.plot_surface(X,Y,matrix('q_operating_m3s'),cmap='viridis',edgecolor='none',antialiased=True);ax.set(xlabel='Speed ratio n',ylabel='Static head (m)',zlabel='Operating Q (m³/s)',title='Operating flow from pump–network head balance');ax.view_init(elev=25,azim=-125);fig.colorbar(obj,ax=ax,shrink=.60,pad=.12);save(fig,'03_operating_flow_3d')
# 4 3D power
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(projection='3d');obj=ax.plot_surface(X,Y,matrix('electric_kW'),cmap='plasma',edgecolor='none',antialiased=True);ax.set(xlabel='Speed ratio n',ylabel='Static head (m)',zlabel='Electrical power (kW)',title='Pump input power from actual paceval operating points');ax.view_init(elev=24,azim=-123);fig.colorbar(obj,ax=ax,shrink=.62,pad=.13);save(fig,'04_electric_power_surface_3d')
# 5 synthetic water quality
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(projection='3d');obj=ax.plot_surface(X,Y,matrix('c_out_mgL'),cmap='cividis',edgecolor='none');ax.set(xlabel='Speed ratio n',ylabel='Static head (m)',zlabel='Surrogate concentration (mg/L)',title='Steady concentration surrogate: mixed outlet');ax.view_init(elev=25,azim=-130);fig.colorbar(obj,ax=ax,shrink=.62,pad=.13);save(fig,'05_mixed_tracer_surface_3d')
# 6 residual logheat
fig,axs=plt.subplots(1,2,figsize=(10,4.9));slice_a=a[np.isclose(a.static_head_m,hs[np.argmin(np.abs(hs-15))])].sort_values('speed_ratio');axs[0].plot(slice_a.speed_ratio,slice_a.pump_head_m,label='Pump head (paceval)',lw=2.4);axs[0].plot(slice_a.speed_ratio,slice_a.system_head_m,'--',label='System head (paceval)',lw=1.9);axs[0].set(xlabel='Speed ratio n',ylabel='Head at operating point (m)',title='Independent head expressions');axs[0].legend();axs[1].scatter(a.speed_ratio,np.abs(a.hydraulic_residual_m),c=a.static_head_m,s=6,cmap='viridis',alpha=.55,rasterized=True);axs[1].set(xlabel='Speed ratio n',ylabel='Absolute head residual (m)',title='Head-balance residual across all points');axs[1].ticklabel_format(axis='y',style='sci',scilimits=(0,0));[a.grid(alpha=.16) for a in axs];fig.suptitle('Operating-point consistency: pump and network heads coincide');fig.tight_layout();save(fig,'06_operating_residual_map')
# 7 parallel branch flows
subset=a[np.isclose(a.static_head_m,hs[np.argmin(np.abs(hs-15))])].sort_values('speed_ratio');fig,ax=plt.subplots(figsize=(9,5));ax.plot(subset.speed_ratio,subset.q_operating_m3s,label='Total network flow',lw=2.2);ax.plot(subset.speed_ratio,subset.branch_a_m3s,label='Branch A (actual paceval output)',lw=1.7);ax.plot(subset.speed_ratio,subset.branch_b_m3s,label='Branch B (actual paceval output)',lw=1.7);ax.set(xlabel='Pump speed ratio',ylabel='Flow (m³/s)',title='Actual paceval output: parallel-pipe flow allocation at fixed static head');ax.grid(alpha=.18);ax.legend();save(fig,'07_branch_flow_time_trace')
# 8 energy profile
fig,ax=plt.subplots(figsize=(9,5));ax.plot(t.hour,t.elec_base_kW,lw=2.2,label='Baseline electrical power');ax.plot(t.hour,t.elec_version_1_kW,lw=1.2,label='Version 1',alpha=.8);ax.plot(t.hour,t.elec_version_20_kW,lw=1.2,label='Version 20',alpha=.8);ax.set(xlabel='Synthetic hour',ylabel='Input power (kW)',title='Electric power with three versioned mathematical formulas');ax.legend();ax.grid(alpha=.2);save(fig,'08_power_versions_time_trace')
# 9 48h energy and price
fig,ax=plt.subplots(figsize=(9,5));ax.plot(t.hour,t.cumulative_base_energy_kWh,label='Baseline',lw=2);ax.plot(t.hour,t.cumulative_version1_energy_kWh,label='Version 1',lw=1.6);ax.plot(t.hour,t.cumulative_version20_energy_kWh,label='Version 20',lw=1.6);ax.set(xlabel='Synthetic schedule hour',ylabel='Accumulated energy (kWh)',title='Accumulated electrical energy from actual paceval power curves');ax.legend();ax.grid(alpha=.17);save(fig,'09_cumulative_energy_versions')
# 10 version profile
fig,axs=plt.subplots(1,2,figsize=(10,4.6));axs[0].plot(v.version,v.efficiency,'o-',lw=1.8);axs[0].set(xlabel='Formula version',ylabel='Hydraulic efficiency',title='Twenty persistent efficiency graphs');axs[1].plot(v.version,v.power_kW,'o-',lw=1.8);axs[1].set(xlabel='Formula version',ylabel='Electrical power (kW)',title='Power for the same operating point');[a.grid(alpha=.15) for a in axs];fig.suptitle('Versioned expressions evaluated by paceval (identical operating point)');fig.tight_layout();save(fig,'10_versioned_efficiency_power')
# 11 hydraulic residual across sampled off-operating points
fig,ax=plt.subplots(figsize=(9,5));sc=ax.scatter(s.q_m3s,s.residual_m,c=s.speed_ratio,cmap='coolwarm',s=7,alpha=.8,rasterized=True);ax.axhline(0,color='black',lw=1,ls='--');ax.set(xlabel='Sampled flow (m³/s)',ylabel='Pump minus system head (m)',title='Off-equilibrium residual screening with paceval');fig.colorbar(sc,ax=ax,label='Speed ratio n');ax.grid(alpha=.15);save(fig,'11_sweep_residuals')
# 12 mixed quality vs power tradeoff actual pts
fig,ax=plt.subplots(figsize=(9,5));sc=ax.scatter(a.electric_kW,a.c_out_mgL,c=a.speed_ratio,cmap='viridis',alpha=.75,s=6,rasterized=True);ax.set(xlabel='Power input (kW)',ylabel='Surrogate outlet tracer (mg/L)',title='Synthetic steady attenuation versus electrical demand');fig.colorbar(sc,ax=ax,label='Speed ratio n');ax.grid(alpha=.13);save(fig,'12_quality_vs_power')
print('Created',len(list(F.glob('*.pdf'))),'computed PNG/PDF chart pairs')
