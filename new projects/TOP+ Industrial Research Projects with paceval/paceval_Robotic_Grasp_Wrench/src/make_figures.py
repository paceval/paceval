#!/usr/bin/env python3
"""Plots strictly from transcribed remote paceval MCP observations (except labeled geometry schematic)."""
from pathlib import Path
import csv,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
F=R/'figures';F.mkdir(exist_ok=True)
rows=list(csv.DictReader((R/'results/mcp_observed_main_selected.csv').open()))
inputs={x['case_id']:x for x in csv.DictReader((R/'examples/synthetic_contact_candidates.csv').open())}
assert len(rows)==len(inputs)==81
for r in rows:
 r['geom']=int(r['case_id'][1]);r['mu']=float(inputs[r['case_id']]['mu1']);r['Fn']=float(inputs[r['case_id']]['Fn1']);
 r['delta']=[-.25,0,.25][int(r['case_id'][-1])-1]
 for k in ['force_residual_v2_N','torque_residual_v2_Nm','friction_margin_min_N','cost_v2_N2','candidate_guard_v1','candidate_guard_v2','joint_margin_v2_N']:
  r[k]=float(r[k])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','savefig.dpi':180})
TEAL='#087c85';RUST='#b34a2b';MID='#526b82';PURPLE='#6750a4'
def store(name):
 plt.tight_layout(pad=2);plt.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');plt.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close()

def banner(ax):ax.text(.01,-.16,'Source: actually executed paceval MCP 4.26 · deterministic synthetic candidates',transform=ax.transAxes,fontsize=8,color='#667')
# 01 friction envelope, actual archived values.
fig,ax=plt.subplots(figsize=(8.2,4.6))
for fn,col in [(8,RUST),(11,MID),(14,TEAL)]:
 p=sorted([x for x in rows if x['geom']==1 and x['Fn']==fn and x['delta']==-.25],key=lambda x:x['mu'])
 ax.plot([x['mu'] for x in p],[x['friction_margin_min_N'] for x in p],'-o',lw=2.4,color=col,label=f'Normal force {fn} N / contact')
ax.axhline(0,color='black',lw=1,ls='--');ax.set(xlabel='Static friction coefficient, μ',ylabel='Minimum contact friction margin (N)',title='Friction cone feasibility across three normal loads');ax.legend(fontsize=9);ax.grid(alpha=.15);banner(ax);store('01_friction_cone_margin')
# 02 sampled force and torque residuals; shape denotes actually computed v2 status.
fig,ax=plt.subplots(figsize=(8.2,5.0))
for status,col,label in [(0,RUST,'Outside declared mathematical constraints'),(1,TEAL,'Within declared mathematical constraints')]:
 p=[x for x in rows if x['candidate_guard_v2']==status]
 ax.scatter([x['force_residual_v2_N'] for x in p],[x['torque_residual_v2_Nm'] for x in p],s=42,alpha=.85,c=col,label=f'{label}: {len(p)}')
ax.axvline(.2,color='#6a6a6a',ls='--',lw=1.2);ax.axhline(.06,color='#6a6a6a',ls='--',lw=1.2)
ax.set(xlabel='Force equilibrium residual (N)',ylabel='Torque equilibrium residual (N·m)',title='Task-wrench residuals for 81 contact-force candidates');ax.legend(fontsize=8,loc='upper left');ax.grid(alpha=.15);banner(ax);store('02_wrench_residual_scatter')
# 03 heatmap of v2 accepted counts by geometry and friction.
fig,ax=plt.subplots(figsize=(7.3,4.4));matrix=np.zeros((3,3))
for geom in [1,2,3]:
 for j,mu in enumerate([.25,.4,.6]):matrix[geom-1,j]=sum(x['candidate_guard_v2'] for x in rows if x['geom']==geom and x['mu']==mu)
im=ax.imshow(matrix,cmap='YlGnBu',vmin=0,vmax=9,aspect='auto')
ax.set_xticks(range(3),['0.25','0.40','0.60']);ax.set_yticks(range(3),['40 mm radius','55 mm radius','70 mm radius'])
for (i,j),v in np.ndenumerate(matrix):ax.text(j,i,f'{int(v)}/9',ha='center',va='center',fontsize=13,weight='bold',color='white' if v>=5 else '#152a35')
ax.set(xlabel='Static contact-friction coefficient',title='Candidate allocations passing v2 checks');fig.colorbar(im,ax=ax,label='Count / 9 candidate allocations');store('03_candidate_feasibility_map')
# 04 observed version differences
fig,ax=plt.subplots(figsize=(8.2,4.4));x=np.arange(3);width=.36
v1=[sum(z['candidate_guard_v1'] for z in rows if z['geom']==g) for g in [1,2,3]]
v2=[sum(z['candidate_guard_v2'] for z in rows if z['geom']==g) for g in [1,2,3]]
ax.bar(x-width/2,v1,width,color=MID,label='v1: nominal target wrench');ax.bar(x+width/2,v2,width,color=TEAL,label='v2: disturbed target wrench')
for i,y in enumerate(v1):ax.text(i-width/2,y+.25,str(int(y)),ha='center',fontsize=10)
for i,y in enumerate(v2):ax.text(i+width/2,y+.25,str(int(y)),ha='center',fontsize=10)
ax.set_xticks(x,['Geometry A (40 mm)','Geometry B (55 mm)','Geometry C (70 mm)']);ax.set_ylim(0,max(v1+v2)+3)
ax.set(ylabel='Mathematically feasible candidate allocations / 27',title='Same contact forces, two prescribed wrench requirements');ax.legend(fontsize=9);ax.grid(axis='y',alpha=.12);banner(ax);store('04_model_version_feasibility')
# 05 contact cost for contact geometry and a fixed mu & delta
fig,ax=plt.subplots(figsize=(8.2,4.6))
for geom,col in [(1,TEAL),(2,RUST),(3,PURPLE)]:
 p=sorted([z for z in rows if z['geom']==geom and z['mu']==.4 and z['delta']==-.25],key=lambda z:z['Fn'])
 ax.plot([z['Fn'] for z in p],[z['cost_v2_N2'] for z in p],lw=2.4,marker='o',color=col,label=f'Geometry {geom}')
ax.set(xlabel='Normal load per contact (N)',ylabel='Composite residual / slip-penalty score (N²)',title='Wrench-based candidate score under fixed disturbance');ax.legend();ax.grid(alpha=.15);banner(ax);store('05_wrench_score_by_geometry')
# 06 joint signed margins for each geometry, fixed force and friction
fig,ax=plt.subplots(figsize=(8.2,4.4))
for geom,col in [(1,TEAL),(2,MID),(3,RUST)]:
 p=sorted([z for z in rows if z['geom']==geom and z['Fn']==11 and z['mu']==.6],key=lambda z:z['delta'])
 ax.plot([z['delta'] for z in p],[z['joint_margin_v2_N'] for z in p],'-o',lw=2.3,color=col,label=f'Radius {int(float(inputs[p[0]["case_id"]]["R1"])*1000)} mm')
ax.axhline(0,ls='--',c='black');ax.set(xlabel='Axial contact-force perturbation (N)',ylabel='Combined signed margin (equivalent N)',title='Geometry and torque contributions to candidate margins');ax.legend();ax.grid(alpha=.14);banner(ax);store('06_signed_wrench_margin')
# 07 3D score surface of true actual MCP values
from mpl_toolkits.mplot3d import Axes3D # noqa
fig=plt.figure(figsize=(8.3,6.0));ax=fig.add_subplot(111,projection='3d')
p=[x for x in rows if x['geom']==2 and x['delta']==-.25]
x=np.array([z['mu'] for z in p]);y=np.array([z['Fn'] for z in p]);z=np.array([z['cost_v2_N2'] for z in p])
ax.plot_trisurf(x,y,z,cmap='viridis',linewidth=.25,alpha=.88)
ax.scatter(x,y,z,c='#232629',s=20);ax.set(xlabel='Contact friction μ',ylabel='Normal load (N)',zlabel='Composite score (N²)',title='Observed 3D score surface · Geometry B');ax.view_init(24,-55)
store('07_score_surface_actual_mcp')
# 08 TINC interval widths from paceval-supplied bounds only.
tinc=list(csv.DictReader((R/'results/mcp_tinc_observed.csv').open()))
fig,ax=plt.subplots(figsize=(8.2,4.5));names=[r['case_id']+' '+('F' if r['graph_id'].startswith('force') else 'M') for r in tinc]
width=[float(r['upper'])-float(r['lower']) for r in tinc]
ax.bar(np.arange(len(tinc)),width,color=[TEAL]*4+[RUST]*4)
ax.set_xticks(np.arange(len(tinc)),names,rotation=30,ha='right',fontsize=8)
ax.set_yscale('log');ax.set(ylabel='Width of printed TINC point interval (native units)',title='Reported interval widths on selected point inputs');ax.grid(axis='y',alpha=.2);banner(ax);store('08_tinc_point_interval_widths')
# 09 geometry sketch based on SYNTHETIC INPUTS; schematic, not a paceval result.
fig,ax=plt.subplots(figsize=(7.2,5.2))
from matplotlib.patches import Circle
ax.add_patch(Circle((0,0),.048,facecolor='#e8f3ef',edgecolor='#60796d',lw=2))
for angle in [0,2*math.pi/3,4*math.pi/3]:
 nx,ny=math.cos(angle),math.sin(angle);rx,ry=.048*nx,.048*ny
 ax.scatter([rx],[ry],s=75,c=RUST,zorder=4)
 ax.arrow(rx,ry,-.016*nx,-.016*ny,width=.00055,color=TEAL,length_includes_head=True,head_width=.003)
 ax.arrow(rx,ry,-.006*ny,.006*nx,width=.00038,color=PURPLE,length_includes_head=True,head_width=.002)
ax.scatter([0],[0],marker='+',s=100,c='black');ax.set_aspect('equal');ax.set(xlim=(-.085,.085),ylim=(-.085,.085),xlabel='Object-frame x (m)',ylabel='Object-frame y (m)',title='Schematic: three radial inward point contacts');ax.grid(alpha=.10)
ax.text(-.082,-.078,'Illustrative geometry only; arrows are local basis directions, not measured forces',fontsize=7.2)
store('09_contact_frame_schematic')
print('Generated 9 numbered plots from observed MCP data and 1 clearly marked input schematic')
