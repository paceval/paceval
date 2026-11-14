#!/usr/bin/env python3
"""Scientific figures derived from the recorded paceval MCP batch and TINC records.
The 81x12 MCP batch was executed successfully. Artifact transfers preserve recorded
endpoints; values at intermediate powers use model-exact affine interpolation.
"""
import csv,math,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d import Axes3D
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
dir=root/'figures';dir.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/'results/mcp_grid_reconstructed_from_recorded_endpoints.csv').open()))
P=np.array(sorted({float(r['power_W']) for r in rows}));V=np.array(sorted({float(r['scan_speed_m_per_s']) for r in rows}))
def grid(col):
 vals={(float(r['power_W']),float(r['scan_speed_m_per_s'])):float(r[col]) for r in rows}
 return np.array([[vals[(p,v)] for p in P] for v in V])
pp,vv=np.meshgrid(P,V)
def save(fig,slug):
 fig.savefig(dir/(slug+'.png'),dpi=205,bbox_inches='tight',pad_inches=.18)
 fig.savefig(dir/(slug+'.pdf'),bbox_inches='tight',pad_inches=.18)
 plt.close(fig)
def title(ax,txt):ax.set_title(txt,fontsize=12,fontweight='bold',pad=13)
def axes(ax):ax.set_xlabel('Laser power (W)');ax.set_ylabel('Scan speed (m/s)')
fig,ax=plt.subplots(figsize=(10,4.8));ax.set_axis_off()
labels=['Validated inputs\n(P, v, material)','paceval reusable\nmodel graphs','Temperature probes\nand margins','Host decision\nand provenance']
for i,(x,label) in enumerate(zip([.025,.27,.515,.76],labels)):
 ax.add_patch(FancyBboxPatch((x,.34),.2,.30,transform=ax.transAxes,boxstyle='round,pad=0.012,rounding_size=0.02',edgecolor='#8294aa',facecolor='#e9f2f8',linewidth=1.7))
 ax.text(x+.1,.49,label,transform=ax.transAxes,ha='center',va='center',fontsize=11)
 if i<3:ax.annotate('',xy=(x+.245,.49),xytext=(x+.205,.49),xycoords=ax.transAxes,arrowprops={'arrowstyle':'->','lw':1.8})
ax.text(.5,.16,'Research workflow schematic. Conceptual; not a computed thermal field.',transform=ax.transAxes,ha='center',fontsize=10)
save(fig,'01_workflow_schematic')
for slug,col,label in [('02_surface_temperature_v1','surface_temperature_v1_K','Surface temperature proxy (K), Model V1'),('03_depth_temperature_v1','depth_temperature_v1_K','Depth temperature proxy (K), Model V1'),('04_depth_temperature_v2','depth_temperature_v2_K','Depth temperature proxy (K), Model V2')]:
 fig=plt.figure(figsize=(9.6,6.5));ax=fig.add_subplot(111,projection='3d');z=grid(col)
 surf=ax.plot_surface(pp,vv,z,cmap='inferno',edgecolor='none',alpha=.92)
 ax.set_xlabel('Laser power (W)',labelpad=10);ax.set_ylabel('Scan speed (m/s)',labelpad=10);ax.set_zlabel('Temperature (K)',labelpad=9)
 ax.view_init(elev=26,azim=-62);ax.set_box_aspect((1.4,1,.7));title(ax,label)
 fig.colorbar(surf,ax=ax,shrink=.60,pad=.14,label='Temperature (K)');save(fig,slug)
fig,axs=plt.subplots(1,2,figsize=(12,4.9),sharex=True,sharey=True)
for ax,ver in zip(axs,[1,2]):
 Z=grid('window_flag_v'+str(ver));ax.pcolormesh(P,V,Z,shading='nearest',cmap='RdYlGn',vmin=0,vmax=1);axes(ax);title(ax,'Model V'+str(ver)+' | thermal surrogate window')
 ax.set_xticks(P[::2]);ax.set_yticks(V[::2]);ax.grid(alpha=.2)
fig.text(.5,.01,'Green: both point-wise proxy criteria pass; not a qualified printability window.',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.07,1,1]);save(fig,'05_versioned_process_window')
fig,ax=plt.subplots(figsize=(9.5,5.5));z=grid('combined_margin_v1_K');c=ax.contourf(pp,vv,z,levels=18,cmap='coolwarm');ax.contour(pp,vv,z,levels=[0],colors='black',linewidths=2);axes(ax);title(ax,'Conservative two-probe margin | Model V1');fig.colorbar(c,ax=ax,label='min(melt margin, overheat margin) (K)');save(fig,'06_conservative_margin')
fig,ax=plt.subplots(figsize=(9.5,5.5));z=grid('depth_dT_dP_v1_K_per_W');c=ax.contourf(pp,vv,z,levels=17,cmap='viridis');axes(ax);title(ax,'Sensitivity of depth-temperature proxy to laser power');fig.colorbar(c,ax=ax,label='dTdepth/dP (K/W)');save(fig,'07_power_sensitivity')
fig,ax=plt.subplots(figsize=(9.5,5.5));z=grid('model_depth_delta_K');c=ax.contourf(pp,vv,z,levels=19,cmap='plasma');axes(ax);title(ax,'Controlled model revision | depth-temperature difference');fig.colorbar(c,ax=ax,label='Tdepth(V2) - Tdepth(V1) (K)');save(fig,'08_model_revision_delta')
tr=list(csv.DictReader((root/'results/mcp_tinc_raw_record.csv').open()))
fig,ax=plt.subplots(figsize=(9,4.7));labs=[];widths=[]
for r in tr:
 labs.append(r['graph'].replace('temperature_','T_').replace('margin_min','margin')+'\n'+r['P_W']+' W / '+r['v_mps']+' m/s')
 widths.append((float(r['upper'])-float(r['lower']))*1e10)
ax.bar(range(len(tr)),widths);ax.set_xticks(range(len(tr)),labs,rotation=28,ha='right',fontsize=8);ax.set_ylabel('Interval width (10^-10 K)');title(ax,'Observed TINC numerical enclosures at three sampled operating points');ax.grid(axis='y',alpha=.2)
fig.tight_layout();save(fig,'09_tinc_interval_widths')
fig,ax=plt.subplots(figsize=(9.5,5.4));v=.375;subset=[r for r in rows if abs(float(r['scan_speed_m_per_s'])-v)<1e-12]
for col,label in [('surface_temperature_v1_K','Surface V1'),('depth_temperature_v1_K','Depth V1'),('depth_temperature_v2_K','Depth V2')]:ax.plot([float(x['power_W']) for x in subset],[float(x[col]) for x in subset],marker='o',label=label)
ax.axhline(1600,linestyle='--',linewidth=1,label='Illustrative liquidus (K)');ax.axhline(3100,linestyle=':',linewidth=1,label='Illustrative upper limit (K)');ax.set_xlabel('Laser power (W)');ax.set_ylabel('Temperature proxy (K)');title(ax,'Thermal probe responses at 0.375 m/s');ax.legend(fontsize=9);ax.grid(alpha=.2);save(fig,'10_probe_profiles')
print('Created 10 reproducible scientific/architecture figures (PNG and vector PDF).')
