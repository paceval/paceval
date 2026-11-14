#!/usr/bin/env python3
"""Reconstruct WP11 technical and scientific diagrams from archived real paceval output CSVs."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap

ap=argparse.ArgumentParser();ap.add_argument('--results',default=str(Path(__file__).resolve().parents[1]/'results'));ap.add_argument('--figures',default=str(Path(__file__).resolve().parents[1]/'figures'));args=ap.parse_args()
R=Path(args.results);O=Path(args.figures);O.mkdir(parents=True,exist_ok=True)
s=pd.read_csv(R/'scenario_results.csv');h=pd.read_csv(R/'hosting_capacity.csv');b=pd.read_csv(R/'branch_samples.csv');net=pd.read_csv(R/'network_branches.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','axes.titlesize':12,'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':8,'figure.facecolor':'white','savefig.facecolor':'white','axes.grid':True,'grid.alpha':.20,'axes.spines.top':False,'axes.spines.right':False})
C=['#0B6B70','#D79E38','#943C84','#4376B5','#6C8A42','#BB604A']; modes={0:'Unity power factor',1:'Reactive absorption'}
def save(fig,name):
 fig.tight_layout(pad=1.7);fig.savefig(O/(name+'.png'),dpi=200,bbox_inches='tight');fig.savefig(O/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def figax(title,projection=None):
 fig=plt.figure(figsize=(9.7,5.5));ax=fig.add_subplot(111,projection=projection);ax.set_title(title,pad=14,weight='bold');return fig,ax
# 01 - conceptual architecture, expressly not a numerical result.
fig,ax=plt.subplots(figsize=(10.7,4.1));ax.set_xlim(0,10);ax.set_ylim(0,3.2);ax.axis('off');ax.set_title('WP11 execution architecture (concept diagram)',weight='bold',pad=9)
boxes=[(.1,'DER setpoints +\nsynthetic feeder'),(2.55,'C++ radial AC\npower-flow control'),(5.05,'paceval persistent\nconstraint graphs'),(7.65,'Feasibility +\nhosting summary')]
for x,t in boxes:
 ax.add_patch(FancyBboxPatch((x,1.07),2.15,1.13,boxstyle='round,pad=.14',facecolor='#EAF3F2',edgecolor=C[0],linewidth=1.7));ax.text(x+1.075,1.635,t,ha='center',va='center',fontsize=9,fontweight='bold')
for x in [2.33,4.79,7.28]:ax.add_patch(FancyArrowPatch((x,1.63),(x+.26,1.63),arrowstyle='-|>',mutation_scale=16,color='#2C5960'))
ax.text(5.95,.35,'Power flow: iterative topology traversal; every supported scalar kernel: actual paceval API',ha='center',fontsize=9)
save(fig,'01_execution_architecture')
# 02 network schematic from original synthetic branch CSV.
fig,ax=figax('Synthetic radial feeder: 12 buses, 11 rated branches')
coords={0:(0,0)}
for i in range(1,10):coords[i]=(i,0)
coords[10]=(8,1.1);coords[11]=(7,-1.1)
for _,row in net.iterrows():
 i=int(row.bus);j=int(row.parent);p=coords[j];q=coords[i];ax.plot([p[0],q[0]],[p[1],q[1]],c=C[0],lw=2.6)
for i,(x,y) in coords.items():ax.scatter([x],[y],s=(160 if i==0 else 90),c=(C[1] if i in range(4,12) else C[0]),edgecolors='white',zorder=4);ax.text(x,y+.18,str(i),ha='center',fontsize=8)
ax.text(.0,-.45,'Slack bus',fontsize=9);ax.text(6,1.6,'Candidate PV buses: 4–11',fontsize=9,ha='center');ax.set_xlim(-.6,10);ax.set_ylim(-1.7,2);ax.set_xlabel('Feeder topology (schematic position)');ax.set_yticks([]);save(fig,'02_feeder_topology')
# 03 hosting by site and control mode
fig,ax=figax('Largest feasible sampled DER injection by connection bus')
for mode in [0,1]:
 sub=h[h.control_mode==mode].sort_values('candidate_bus');ax.plot(sub.candidate_bus,sub.highest_feasible_der_pu,marker='o',lw=2.4,label=modes[mode],color=C[mode])
ax.set_xlabel('Connection bus');ax.set_ylabel('Feasible injection (pu)');ax.set_xticks(range(4,12));ax.legend();save(fig,'03_discrete_hosting_by_site')
# 04 feasibility maps
for mode in [0,1]:
 piv=s[s.control_mode==mode].pivot(index='candidate_bus',columns='penetration_step',values='feasible').sort_index()
 fig,ax=figax('Feasibility map: '+modes[mode]);im=ax.imshow(piv.values,origin='lower',aspect='auto',extent=[0,2.5,3.5,11.5],cmap=ListedColormap(['#C55F53','#3F9884']),interpolation='nearest',vmin=0,vmax=1)
 ax.set_xlabel('DER active injection (pu)');ax.set_ylabel('Connection bus');ax.set_yticks(range(4,12));ax.text(1.05,11.1,'Green = feasible; terracotta = limit violated',fontsize=8,bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'});save(fig,'04_feasibility_unity' if mode==0 else '05_feasibility_reactive')
# 06 voltage
fig,ax=figax('Maximum feeder voltage versus DER export: bus 7')
for mode in [0,1]:
 sub=s[(s.candidate_bus==7)&(s.control_mode==mode)].sort_values('der_pu');ax.plot(sub.der_pu,sub.max_voltage_pu,label=modes[mode],lw=2.2,color=C[mode])
ax.axhline(1.05,color=C[2],ls='--',label='Voltage limit 1.05 pu');ax.set_xlabel('DER injection (pu)');ax.set_ylabel('Maximum bus voltage (pu)');ax.legend();save(fig,'06_maximum_bus_voltage')
# 07 thermal margin
fig,ax=figax('Minimum branch-current margin versus DER export: bus 9')
for mode in [0,1]:
 sub=s[(s.candidate_bus==9)&(s.control_mode==mode)].sort_values('der_pu');ax.plot(sub.der_pu,sub.min_current_margin_pu,label=modes[mode],lw=2.2,color=C[mode])
ax.axhline(0,color=C[2],ls='--');ax.set_xlabel('DER injection (pu)');ax.set_ylabel('Minimum current margin (pu)');ax.legend();save(fig,'07_thermal_margin_vs_export')
# 08 losses
fig,ax=figax('Aggregate resistive feeder losses: connection bus 6')
for mode in [0,1]:
 sub=s[(s.candidate_bus==6)&(s.control_mode==mode)].sort_values('der_pu');ax.plot(sub.der_pu,sub.total_line_loss_pu,label=modes[mode],lw=2.2,color=C[mode])
ax.set_xlabel('DER injection (pu)');ax.set_ylabel('Sum of branch I²R loss (pu)');ax.legend();save(fig,'08_grid_losses_vs_der')
# 09 surface
p=s[s.control_mode==0].pivot(index='candidate_bus',columns='penetration_step',values='max_voltage_pu')
X,Y=np.meshgrid(np.linspace(0,2.5,p.shape[1]),p.index.to_numpy())
fig,ax=figax('3D maximum-voltage surface across DER siting',projection='3d')
surface=ax.plot_surface(X,Y,p.to_numpy(),cmap='viridis',linewidth=0,antialiased=True,alpha=.97);ax.set_xlabel('DER injection (pu)',labelpad=8);ax.set_ylabel('Connection bus',labelpad=8);ax.set_zlabel('Vmax (pu)',labelpad=7);ax.view_init(elev=27,azim=-62);fig.colorbar(surface,ax=ax,pad=.09,shrink=.70);save(fig,'09_three_dimensional_voltage_surface')
# 10 quality penalties
fig,ax=figax('Two versioned paceval penalty functions: bus 6, unity PF')
sub=s[(s.candidate_bus==6)&(s.control_mode==0)].sort_values('der_pu');ax.plot(sub.der_pu,sub.penalty_v1,color=C[0],lw=2.2,label='Penalty formula v1');ax.plot(sub.der_pu,sub.penalty_v2,color=C[2],lw=2.2,label='Penalty formula v2');ax.set_xlabel('DER injection (pu)');ax.set_ylabel('Sum of dimensionless violation penalties');ax.legend();save(fig,'10_versioned_penalty_functions')
# 11 voltage profile on sample
fig,ax=figax('Computed bus-voltage profile at three injection levels: bus 8')
ss=b[(b.candidate_bus==8)&(b.control_mode==0)]
for step in [0,24,48]:
 rows=ss[ss.penetration_step==step].sort_values('bus');
 if len(rows):ax.plot(rows.bus,rows.voltage_pu,label=f'{float(rows.der_pu.iloc[0]):.2f} pu DER',marker='o',lw=1.8)
for threshold in [.95,1.05]:ax.axhline(threshold,ls='--',color='#999999')
ax.set_xlabel('Bus index');ax.set_ylabel('Bus voltage (pu)');ax.set_xticks(range(1,12));ax.legend();save(fig,'11_bus_voltage_profile')
# 12 current utilization
fig,ax=figax('Branch-current utilization along the feeder: bus 7 PV')
ss=b[(b.candidate_bus==7)&(b.control_mode==0)]
for step in [0,20,44]:
 rows=ss[ss.penetration_step==step].sort_values('bus');
 if len(rows):ax.plot(rows.bus,rows.current_utilization_ratio,marker='s',lw=1.7,label=f'{rows.der_pu.iloc[0]:.2f} pu DER')
ax.axhline(1,ls='--',color=C[2],label='Rated-current boundary');ax.set_xlabel('Branch downstream bus');ax.set_ylabel('Current / rating');ax.legend();save(fig,'12_branch_current_utilization')
# 13 feasibility histogram
fig,ax=figax('Share of feasible penetration scenarios by connection bus')
by=s.groupby(['candidate_bus','control_mode']).feasible.mean().unstack();u=by.index.to_numpy();ax.bar(u-.2,by[0].to_numpy(),width=.39,color=C[0],label=modes[0]);ax.bar(u+.2,by[1].to_numpy(),width=.39,color=C[1],label=modes[1]);ax.set_xlabel('Connection bus');ax.set_ylabel('Share feasible (discrete sweep)');ax.set_xticks(u);ax.set_ylim(0,1);ax.legend();save(fig,'13_feasible_share_by_bus')
# 14 controlled reactive impact
fig,ax=figax('Reactive-control effect on the largest feasible injection')
a=h.pivot(index='candidate_bus',columns='control_mode',values='highest_feasible_der_pu');difference=a[1]-a[0];ax.bar(difference.index,difference,color=[C[1] if v>=0 else C[2] for v in difference]);ax.axhline(0,ls='-',color='gray');ax.set_xlabel('Connection bus');ax.set_ylabel('Reactive minus unity hosting (pu)');ax.set_xticks(range(4,12));save(fig,'14_reactive_control_impact')
# 15 cumulative branches violated
fig,ax=figax('Number of violated branches across the DER sweep: bus 9')
for mode in [0,1]:
 sub=s[(s.candidate_bus==9)&(s.control_mode==mode)].sort_values('der_pu');ax.step(sub.der_pu,sub.violated_branches,where='mid',lw=2.2,color=C[mode],label=modes[mode])
ax.set_xlabel('DER injection (pu)');ax.set_ylabel('Violating branch-end evaluations');ax.legend();save(fig,'15_constraint_violation_count')
print('Generated',len(list(O.glob('*.png'))),'PNG figures including the independently generated title image')
