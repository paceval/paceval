#!/usr/bin/env python3
"""Produce research graphics from saved paceval MCP numerical results.
The first diagram is explicitly conceptual; the other nine use only recorded
paceval outputs, not independent Python predictions.
"""
from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
root=Path(__file__).resolve().parents[1];out=root/'figures';out.mkdir(exist_ok=True)
G=pd.read_csv(root/'results/mcp_corner_grid_recorded_81.csv')
S=pd.read_csv(root/'results/mcp_path_snapshots_recorded_16.csv')
T=pd.read_csv(root/'results/mcp_tinc_recorded_24.csv')
input_snap=pd.read_csv(root/'data/synthetic_path_snapshots_16.csv')
navy='#12304a';cyan='#158b9b';green='#2a9a76';violet='#6b62ae';amber='#c77c2f';red='#b64f57'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'axes.spines.right':False,'axes.spines.top':False,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(fig,name):
 fig.savefig(out/(name+'.png'),dpi=240,bbox_inches='tight',pad_inches=.17)
 fig.savefig(out/(name+'.pdf'),bbox_inches='tight',pad_inches=.17)
 plt.close(fig)
def dress(ax):ax.grid(alpha=.17);ax.tick_params(colors='#3d5362');ax.title.set_color(navy)
volts=np.sort(G.V.unique());temps=np.sort(G['T'].unique());XV,YT=np.meshgrid(volts,temps)
def field(key):return G.pivot(index='T',columns='V',values=key).to_numpy()
# 01. Architecture schematic is NOT a paceval result.
fig,ax=plt.subplots(figsize=(11,3.25));ax.axis('off');ax.set_xlim(0,11);ax.set_ylim(0,3)
steps=[('PVT inputs','V, T, load, slew'),('Validation +\nversions','bounded CSV inputs'),('paceval graphs','delay / leakage / score'),('Independent checks','native + high precision'),('EDA screening','review corners in STA')]
for i,(name,note) in enumerate(steps):
 x=.08+i*2.2;box=FancyBboxPatch((x,.8),2.05,1.25,boxstyle='round,pad=0.09,rounding_size=.14',edgecolor='#b9d7df',facecolor=['#e8f5f8','#eef1f8','#e6f5f2','#eeeafa','#fff2e8'][i],lw=1)
 ax.add_patch(box);ax.text(x+1.025,1.68,name,ha='center',va='center',fontweight='bold',color=navy,fontsize=10)
 ax.text(x+1.025,1.12,note,ha='center',va='center',color='#486574',fontsize=7.9)
 if i<4:ax.add_patch(FancyArrowPatch((x+2.07,1.44),(x+2.18,1.44),arrowstyle='-|>',color=cyan,mutation_scale=12,lw=1.15))
ax.set_title('Figure 1 | Model screening architecture (concept illustration)',color=navy,pad=10)
save(fig,'01_architecture_schematic')
# 02. True remote results of two delay versions on 16 snapshots.
fig,ax=plt.subplots(figsize=(9.6,4.5));idx=np.arange(len(S));ax.plot(idx,S.delay_v1_ps,'o-',label='v1 baseline cell delay',color=cyan);ax.plot(idx,S.delay_v2_ps,'s-',label='v2 coupled cell delay',color=violet);ax.set(xlabel='Synthetic scenario index',ylabel='Cell delay (ps)',title='Figure 2 | Versioned cell-delay predictions');ax.legend(frameon=False,loc='upper left');dress(ax);save(fig,'02_delay_model_snapshots')
# 03. 2D voltage-temperature delay v2.
fig,ax=plt.subplots(figsize=(9,5.1));z=field('delay_v2_ps');im=ax.contourf(XV,YT,z,levels=14,cmap='viridis');ax.contour(XV,YT,z,colors='white',levels=7,linewidths=.7,alpha=.7);fig.colorbar(im,ax=ax,label='Cell delay v2 (ps)');ax.set(xlabel='Supply voltage (V)',ylabel='Temperature (°C)',title='Figure 3 | paceval cell-delay corner surface');save(fig,'03_delay_corner_map')
# 04. Leakage power v2 and threshold.
fig,ax=plt.subplots(figsize=(9,5.1));z=field('leak_power_v2_nW');im=ax.contourf(XV,YT,z,levels=17,cmap='plasma');ax.contour(XV,YT,z,levels=[120],colors='white',linewidths=2.1);fig.colorbar(im,ax=ax,label='Single-cell standby power v2 (nW)');ax.set(xlabel='Supply voltage (V)',ylabel='Temperature (°C)',title='Figure 4 | Standby leakage across evaluated PVT corners');ax.text(.71,111,'White contour: illustrative 120 nW budget',color='white',fontsize=8,fontweight='bold');save(fig,'04_leakage_power_map')
# 05. Composite score surface and score zero boundary.
fig,ax=plt.subplots(figsize=(9,5.1));z=field('composite_score_v2_ps');maxabs=max(abs(z.min()),abs(z.max()));im=ax.contourf(XV,YT,z,levels=np.linspace(-maxabs,maxabs,19),cmap='RdBu',extend='both');ax.contour(XV,YT,z,levels=[0],colors='black',linewidths=2.1);fig.colorbar(im,ax=ax,label='Composite margin, ps-equivalent');ax.set(xlabel='Supply voltage (V)',ylabel='Temperature (°C)',title='Figure 5 | Combined timing and leakage margin (v2)');save(fig,'05_composite_score_map')
# 06. Model-dependent discrete outcomes.
fig,axes=plt.subplots(1,2,figsize=(10.4,4.5),sharex=True,sharey=True)
for ax,key,name in zip(axes,['corner_guard_v1','corner_guard_v2'],['Model v1','Model v2']):
 z=field(key);ax.pcolormesh(XV,YT,z,cmap='RdYlGn',vmin=0,vmax=1,shading='nearest');ax.scatter(G.loc[G[key]==0,'V'],G.loc[G[key]==0,'T'],marker='x',c='#361f31',s=45,lw=1.7);ax.set(xlabel='Supply voltage (V)',title=name)
axes[0].set_ylabel('Temperature (°C)');fig.suptitle('Figure 6 | Synthetic accept/review masks returned by paceval',fontsize=13,color=navy);fig.text(.5,.03,'X = corner fails at least one modeled timing, leakage or domain rule',ha='center',color='#4a6373',fontsize=9);fig.tight_layout(rect=(0,.08,1,.93));save(fig,'06_model_guard_comparison')
# 07. Slack vs leakage power in synthetic snapshot series.
fig,ax=plt.subplots(figsize=(9.5,4.8));n=np.arange(16);ax.plot(n,S.slack_v1_ps,'--o',color=cyan,label='Path slack v1');ax.plot(n,S.slack_v2_ps,'-s',color=violet,label='Path slack v2');ax.axhline(0,color=red,ls=':',lw=1.4);ax.set(xlabel='Synthetic scenario index',ylabel='Illustrative path slack (ps)',title='Figure 7 | Same-path timing model revisions');ax.legend(frameon=False);dress(ax);save(fig,'07_slack_snapshot_comparison')
# 08. Model revision effect on leakage vs temperatures.
fig,ax=plt.subplots(figsize=(9.3,4.8));ax.plot(np.arange(16),S.leak_power_v1_nW,'o--',color=cyan,label='Leakage power v1');ax.plot(np.arange(16),S.leak_power_v2_nW,'s-',color=amber,label='Leakage power v2');ax.axhline(120,color=red,ls=':',label='Illustrative cell budget');ax.set(xlabel='Synthetic scenario index',ylabel='Single-cell standby power (nW)',title='Figure 8 | Versioned leakage models and per-cell limit');ax.legend(frameon=False);dress(ax);save(fig,'08_leakage_snapshots')
# 09. Voltage-temperature delta delay 3D (actually computed by paceval graph).
from mpl_toolkits.mplot3d import Axes3D
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');z=field('model_delta_delay_ps');ax.plot_surface(XV,YT,z,cmap='coolwarm',edgecolor='white',linewidth=.3,antialiased=True,rstride=1,cstride=1);ax.set(xlabel='Supply V (V)',ylabel='Temperature (°C)',zlabel='Delay v2 - v1 (ps)');ax.view_init(elev=24,azim=-124);ax.set_title('Figure 9 | paceval model-revision delay surface',pad=18,color=navy);fig.subplots_adjust(left=.0,right=.95,top=.93,bottom=.04);save(fig,'09_version_delta_3d')
# 10. TINC transmitted printed interval widths at 8 exact sample cases.
fig,ax=plt.subplots(figsize=(9.6,4.6));t=T[T.function_id=='leak_power_v2_nW'].copy();bars=(t.paceval_printed_upper-t.paceval_printed_lower)*1e12;ax.bar(range(len(t)),bars,color=green);ax.set_xticks(range(len(t)),t.scenario,rotation=0);ax.set(xlabel='TINC sample case',ylabel='Printed interval width (10^-12 nW)',title='Figure 10 | TINC result intervals for leakage power');dress(ax);save(fig,'10_tinc_leakage_intervals')
print('Rendered',len(list(out.glob('[0-9][0-9]_*.png'))),'PNG+PDF figure pairs')
