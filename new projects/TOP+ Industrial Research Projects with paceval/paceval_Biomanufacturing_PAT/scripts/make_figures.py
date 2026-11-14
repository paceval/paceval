#!/usr/bin/env python3
"""Generate charts exclusively from recorded paceval MCP results; 01 is a schematic."""
from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D
root=Path(__file__).resolve().parents[1]
out=root/'figures';out.mkdir(exist_ok=True)
r=pd.read_csv(root/'results'/'mcp_timeseries_24graphs_excerpt.csv')
e=pd.read_csv(root/'results'/'mcp_extended_sensitivity_replay.csv')
g=pd.read_csv(root/'results'/'mcp_grid_scores_81.csv')
t=pd.read_csv(root/'results'/'mcp_tinc_18_checks.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
navy='#18324b';teal='#0c8b83';orange='#cb6e35';violet='#7660a7';red='#b54250'
def save(fig,name):
 fig.savefig(out/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.18)
 fig.savefig(out/(name+'.pdf'),bbox_inches='tight',pad_inches=.18)
 plt.close(fig)
def fmt(ax):ax.grid(alpha=.17);ax.tick_params(colors='#394d5f');ax.title.set_color(navy)
h=r['hour'].to_numpy()
# 01 - abstract architecture diagram, NOT numeric research result.
fig,ax=plt.subplots(figsize=(11,3.5));ax.set_xlim(0,11);ax.set_ylim(0,3.3);ax.axis('off')
steps=[('Bioreactor\nmeasurements','DO · substrate · biomass'),('Validated\nCSV snapshots','units · bounds · phases'),('paceval graphs\nv1 + v2','growth · OUR · OTR · margins'),('Independent\naudit','mpmath · native C++'),('PAT monitoring\noutput','REVIEW · investigation')]
for i,(s,caption) in enumerate(steps):
 x=.15+i*2.2
 ax.add_patch(FancyBboxPatch((x,.7),2.0,1.55,boxstyle='round,pad=0.08,rounding_size=.12',facecolor=['#e9f7f2','#eef3f8','#e4f7f6','#efeaf7','#fff0e6'][i],edgecolor='#c5d5d9',lw=1))
 ax.text(x+1,1.62,s,ha='center',va='center',fontsize=10,fontweight='bold',color=navy)
 ax.text(x+1,1.04,caption,ha='center',va='center',fontsize=7.9,color='#4b6069')
 if i<4:ax.add_patch(FancyArrowPatch((x+2.05,1.45),(x+2.18,1.45),arrowstyle='-|>',mutation_scale=10,color=teal,lw=1.2))
ax.set_title('Figure 1  |  Industrial PAT computation architecture (conceptual)',pad=9,color=navy)
save(fig,'01_PAT_architecture_schematic')
# 02 model version growth
fig,ax=plt.subplots(figsize=(8.5,4.4));ax.plot(h,r.mu1,'o-',color=teal,label='Monod with oxygen limitation (v1)');ax.plot(h,r.mu2,'s-',color=violet,label='Substrate-inhibition extension (v2)');ax.set(xlabel='Synthetic replay index / h',ylabel='Specific growth rate (1/h)',title='Figure 2  |  Reusable paceval growth-model versions');ax.legend(frameon=False,fontsize=9);fmt(ax);save(fig,'02_growth_model_versions')
# 03 oxygen rates
fig,ax=plt.subplots(figsize=(8.5,4.4));ax.plot(h,r.OTR,'o-',color=teal,label='OTR, transfer to broth');ax.plot(h,r.OUR1,'--',color=violet,label='OUR v1');ax.plot(h,r.OUR2,'s-',color=orange,label='OUR v2');ax.set(xlabel='Synthetic replay index / h',ylabel='Oxygen rate (g O2 / L / h)',title='Figure 3  |  Oxygen transfer and metabolic uptake');ax.legend(frameon=False,fontsize=9);fmt(ax);save(fig,'03_oxygen_transfer_uptake')
# 04 margin
fig,ax=plt.subplots(figsize=(8.5,4.4));ax.plot(h,r.margin1,color=violet,marker='o',label='OTR - OUR v1');ax.plot(h,r.margin2,color=teal,marker='s',label='OTR - OUR v2');ax.axhline(0,color=red,lw=1,ls='--');ax.set(xlabel='Synthetic replay index / h',ylabel='Oxygen balance margin (g O2 / L / h)',title='Figure 4  |  Transfer adequacy versus concentration adequacy');ax.legend(frameon=False,fontsize=9);fmt(ax);save(fig,'04_oxygen_balance_margin')
# 05 boolean vs DO
fig,ax=plt.subplots(figsize=(8.5,4.4));ax.plot(h,r.DO*1000,color=teal,marker='o',label='Dissolved O2');ax.axhline(1.5,color=red,linestyle='--',label='Illustrative DO minimum');ax.set(xlabel='Synthetic replay index / h',ylabel='Dissolved O2 (mg / L)',title='Figure 5  |  Concentration limit and paceval discrete guard');fmt(ax)
bx=ax.twinx();bx.step(h,r.flag2,where='mid',color=violet,lw=1.6,label='paceval v2 guard');bx.set_ylim(-.15,1.4);bx.set_ylabel('Guard (0 or 1)');lines,labels=ax.get_legend_handles_labels();l2,lbl2=bx.get_legend_handles_labels();ax.legend(lines+l2,labels+lbl2,loc='upper right',frameon=False,fontsize=9);save(fig,'05_DO_limit_guard')
# 06 grid margin 2d
D=np.sort(g.DO_gO2_per_L.unique());X=np.sort(g.X_gDW_per_L.unique());grid=g.pivot(index='DO_gO2_per_L',columns='X_gDW_per_L',values='oxygen_margin_v2_gO2_per_L_per_h').to_numpy()
fig,ax=plt.subplots(figsize=(8.5,4.8));im=ax.pcolormesh(X,D*1000,grid,shading='auto',cmap='BrBG',vmin=-.4,vmax=.4);ax.contour(X,D*1000,grid,levels=[0],colors=[navy],linewidths=2);ax.axhline(1.5,color=red,linestyle='--',lw=1);ax.set(xlabel='Biomass X (g dry mass / L)',ylabel='Dissolved O2 (mg / L)',title='Figure 6  |  Recorded paceval oxygen-transfer margins (v2)');fig.colorbar(im,ax=ax,label='OTR - OUR (g O2 / L / h)');save(fig,'06_oxygen_margin_parameter_map')
# 07 3d score
sc=g.pivot(index='DO_gO2_per_L',columns='X_gDW_per_L',values='score_v2_gO2_per_L').to_numpy()*1000
GX,GD=np.meshgrid(X,D*1000);fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(GX,GD,sc,cmap='viridis',edgecolor='white',lw=.28,rstride=1,cstride=1,antialiased=True);ax.set_xlabel('Biomass X (gDW / L)',labelpad=10);ax.set_ylabel('DO (mg / L)',labelpad=10);ax.set_zlabel('Guard score (mg O2 / L)',labelpad=10);ax.view_init(elev=25,azim=-125);ax.set_title('Figure 7  |  paceval composite score surface (v2)',pad=16,color=navy);fig.subplots_adjust(left=0,right=.98,bottom=.05,top=.91);save(fig,'07_score_surface_3d')
# 08 actual kLa vs kLaReq
fig,ax=plt.subplots(figsize=(8.5,4.4));ax.plot(h,r.kLa,color=teal,marker='o',label='Configured kLa');ax.plot(h,r.kLaReq,color=orange,marker='s',label='Required from paceval v2');ax.set(xlabel='Synthetic replay index / h',ylabel='Volumetric oxygen-transfer coefficient (1/h)',title='Figure 8  |  Configured and model-required oxygen transfer');ax.legend(frameon=False,fontsize=9);fmt(ax);save(fig,'08_required_kla')
# 09 sensitivity and version delta
fig,ax=plt.subplots(figsize=(8.5,4.4));ax.plot(e.hour,e.sensitivity_mu_S_v2,marker='o',color=violet,label='d(mu v2)/dS');ax.axhline(0,color=red,lw=.7);ax.set(xlabel='Synthetic replay index / h',ylabel='Growth response to substrate (L / gS / h)',title='Figure 9  |  paceval analytical substrate sensitivity');fmt(ax);ax.legend(frameon=False,fontsize=9);save(fig,'09_growth_sensitivity')
# 10 TINC interval availability: report exact returned interval widths, no blanket guarantee.
fig,ax=plt.subplots(figsize=(8.5,4.4));view=t[t.function_id=='v2_oxygen_margin'].copy();j=np.arange(len(view));width=(view.paceval_tinc_upper-view.paceval_tinc_lower).to_numpy();ax.bar(j,width*1e12,color=teal);ax.set_xticks(j,[f'Case {z+1}' for z in j]);ax.set(xlabel='Six independently specified test cases',ylabel='Returned interval width (10^-12 g O2 / L / h)',title='Figure 10  |  Recorded TINC bounds for oxygen margin');fmt(ax);save(fig,'10_tinc_margin_width')
print('Generated PNG/PDF figures:',len(list(out.glob('[0-9][0-9]_*.png'))))
