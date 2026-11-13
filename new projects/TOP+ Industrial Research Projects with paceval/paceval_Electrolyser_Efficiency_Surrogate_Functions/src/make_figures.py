#!/usr/bin/env python3
"""Regenerate the 10 paceval-result scientific figures and one workflow diagram.
All quantitative plots read the captured original SDK execution CSVs, not native values.
"""
from pathlib import Path
import csv,argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches

def make(root):
 figure=root/'figures';figure.mkdir(exist_ok=True,parents=True)
 with (root/'examples/trace_samples.csv').open() as f:tr=list(csv.DictReader(f))
 with (root/'results/scenario_summary.csv').open() as f:sm=list(csv.DictReader(f))
 with (root/'results/parameter_surface.csv').open() as f:surf=list(csv.DictReader(f))
 get=lambda row,key:float(row[key])
 def save(name):
  plt.tight_layout(pad=2);plt.savefig(figure/(name+'.png'),dpi=220,bbox_inches='tight',facecolor='white');plt.savefig(figure/(name+'.pdf'),bbox_inches='tight',facecolor='white');plt.close()
 def base(title,xlab,ylab):
  f,ax=plt.subplots(figsize=(8.8,5.6));ax.set_title(title,fontsize=14,fontweight='bold',pad=14);ax.set_xlabel(xlab);ax.set_ylabel(ylab);ax.grid(alpha=.18);return f,ax
 def subset(version=2,pressure=10):return [r for r in tr if int(r['version'])==version and float(r['pressure_bar'])==pressure]
 # Figure 1: explicitly conceptual, no numerical result assertion.
 fig,ax=plt.subplots(figsize=(11,3.4));ax.set_xlim(0,12);ax.set_ylim(0,3);ax.axis('off')
 titles=['Renewable load\n& operating inputs','Persistent paceval\nmodel graph v1/v2','C++ thermal state\n& program control','Reproducible\nmetrics & audit']
 for i,t in enumerate(titles):
  x=.2+i*3.03
  ax.add_patch(patches.FancyBboxPatch((x,.85),2.6,1.35,boxstyle='round,pad=0.12',facecolor='#eaf5f8',edgecolor='#427888',lw=1.3))
  ax.text(x+1.3,1.52,t,ha='center',va='center',fontsize=11,fontweight='bold')
  if i<3:ax.annotate('',xy=(x+3.0,1.52),xytext=(x+2.71,1.52),arrowprops={'arrowstyle':'->','lw':2})
 ax.text(6,.3,'Original paceval graphs evaluate the electrochemistry and domain scores; C++ retains simulation state.',ha='center',fontsize=10)
 save('01_workflow')
 # 02 scheduled current density, source is paceval trace alongside host command.
 _,ax=base('Three deterministic renewable-load scenarios','Time (h)','Current density (A/cm²)')
 names={0:'Step-load',1:'Renewable tracking',2:'High-variability'}
 for i in range(3):
  s=[r for r in subset() if int(r['profile'])==i]
  ax.step([get(r,'time_s')/3600 for r in s],[get(r,'current_density_A_cm2') for r in s],where='post',label=names[i])
 ax.legend();save('02_load_profiles')
 # 03 stack voltage and transport corrected v1/v2 at same pressure/current profile.
 _,ax=base('Polarization response across the two model versions','Time (h)','Cell voltage (V)')
 for ver in [1,2]:
  s=[r for r in subset(version=ver) if int(r['profile'])==1]
  ax.plot([get(r,'time_s')/3600 for r in s],[get(r,'cell_voltage_V') for r in s],label=('v1: activation + ohmic' if ver==1 else 'v2: + transport correction'),alpha=.85)
 ax.legend();save('03_voltage_response')
 # surface utility, actual original paceval batch samples
 x=np.unique([get(r,'current_density_A_cm2') for r in surf]);y=np.unique([get(r,'temperature_C') for r in surf]);nx=len(x);ny=len(y)
 def gridval(col):return np.array([get(r,col) for r in surf]).reshape(ny,nx)
 X,Y=np.meshgrid(x,y)
 fig=plt.figure(figsize=(9,6.3));ax=fig.add_subplot(111,projection='3d')
 mesh=ax.plot_surface(X,Y,gridval('efficiency_v2_LHV')*100,cmap='viridis',linewidth=0,antialiased=True)
 ax.set_title('System LHV efficiency under current and temperature changes',pad=18,fontsize=12,fontweight='bold');ax.set_xlabel('Current density (A/cm²)',labelpad=10);ax.set_ylabel('Stack temperature (°C)',labelpad=10);ax.set_zlabel('Efficiency (%, LHV)',labelpad=12);ax.view_init(elev=23,azim=-120)
 fig.colorbar(mesh,ax=ax,shrink=.60,pad=.15,label='Efficiency (%, LHV)')
 save('04_efficiency_surface_3d')
 # 05 stack efficiency heatmap, ideal for design exploration
 _,ax=base('Computed hydrogen output parameter map','Current density (A/cm²)','Stack temperature (°C)')
 m=ax.pcolormesh(X,Y,gridval('hydrogen_rate_kg_h'),shading='auto',cmap='viridis')
 plt.colorbar(m,ax=ax,label='Hydrogen production (kg/h)');save('05_hydrogen_rate_map')
 # 06 integrated efficiencies by cases v1/v2
 _,ax=base('Scenario-integrated system efficiency (LHV)','Scenario / nominal pressure','Integrated efficiency (%, LHV)')
 r1=[r for r in sm if int(r['version'])==1];r2=[r for r in sm if int(r['version'])==2]
 pos=np.arange(len(r1));ax.bar(pos-.2,[get(r,'integrated_system_efficiency_LHV')*100 for r in r1],width=.38,label='v1 baseline')
 ax.bar(pos+.2,[get(r,'integrated_system_efficiency_LHV')*100 for r in r2],width=.38,label='v2 transport corrected')
 ax.set_xticks(pos);ax.set_xticklabels([f"P{r['profile']} {float(r['pressure_bar']):.0f}bar" for r in r1],rotation=30,ha='right');ax.legend();save('06_integrated_efficiency')
 # 07 complete mass accumulation from paceval H2 rate stored at every 4th sample (true cumulative values)
 _,ax=base('Hydrogen accumulation under changing electricity supply','Time (h)','Cumulative H₂ (kg)')
 for profile in range(3):
  s=[r for r in subset() if int(r['profile'])==profile]
  ax.plot([get(r,'time_s')/3600 for r in s],[get(r,'cumulative_H2_kg') for r in s],label=names[profile])
 ax.legend();save('07_hydrogen_accumulation')
 # 08 thermal states, transport variant at same nominal p
 _,ax=base('Lumped stack-temperature trajectories','Time (h)','Stack temperature (°C)')
 for profile in range(3):
  s=[r for r in subset() if int(r['profile'])==profile]
  ax.plot([get(r,'time_s')/3600 for r in s],[get(r,'temperature_C') for r in s],label=names[profile])
 ax.legend();save('08_thermal_response')
 # 09 sensitivity from original paceval graph samples
 _,ax=base('Analytical system-efficiency sensitivity','Current density (A/cm²)','d efficiency / d current density (cm²/A)')
 for i,t in enumerate([35.,59.,83.]):
  mask=np.array([get(r,'temperature_C')==t for r in surf]);ss=[r for r,ok in zip(surf,mask) if ok]
  if ss:ax.plot([get(r,'current_density_A_cm2') for r in ss],[get(r,'d_efficiency_d_j_v2') for r in ss],label=f'{t:.0f} °C')
 ax.axhline(0,linestyle=':',linewidth=1);ax.legend();save('09_local_sensitivity')
 # 10 model revision: true paceval data difference, not native comparison
 _,ax=base('Controlled polarization-model change','Current density (A/cm²)','Additional v2 cell voltage (V)')
 z=gridval('version2_minus_version1_voltage_V')
 cf=ax.contourf(X,Y,z,levels=20,cmap='viridis');plt.colorbar(cf,ax=ax,label='v2 − v1 (V)');save('10_versioned_difference')
 # 11 domain-specific energy gap and thermoneutral heat distinction
 _,ax=base('Two distinct energy-related quantities','Current density (A/cm²)','Power (kW)')
 ss=[r for r in surf if get(r,'temperature_C')==59.]
 ax.plot(x,[get(r,'lhv_power_gap_v2_kW') for r in ss],label='System electricity minus hydrogen LHV rate')
 ax.plot(x,[get(r,'thermoneutral_heat_proxy_v2_kW') for r in ss],label='Stack thermoneutral heat proxy')
 ax.legend(fontsize=9);save('11_power_and_thermal_distinction')
 print('Scientific figures generated from original paceval CSVs:',len(list(figure.glob('*.png')))-1,'+ hero')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);make(p.parse_args().root)
