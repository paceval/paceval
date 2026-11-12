#!/usr/bin/env python3
"""Plots only numeric CSVs emitted by WP031's original paceval C++ SDK run."""
from pathlib import Path
import csv, math
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
def read(n):return list(csv.DictReader(open(ROOT/'examples'/n,encoding='utf-8')))
paths=read('selected_path_points.csv'); choices=read('selected_trajectories.csv'); rows=read('trajectory_candidates.csv')
policies=[('precision',1),('gentle',1),('clearance',1),('balanced',1),('gentle',2)]
name=lambda x:f'{x[0]} v{x[1]}'
def sub(p):return sorted([r for r in paths if (r['policy'],int(r['version']))==p],key=lambda z:int(z['sample']))
def saved(stem):plt.tight_layout(pad=2);plt.savefig(FIG/(stem+'.png'),dpi=190,bbox_inches='tight');plt.savefig(FIG/(stem+'.pdf'),bbox_inches='tight');plt.close()
# Technically grounded cover: data-derived curves, no generative imagery / pseudo-lab image.
fig,ax=plt.subplots(figsize=(14,6),facecolor='#0c1d32');ax.set_facecolor('#0c1d32')
for j,p in enumerate(policies[:4]):
 pts=sub(p);ax.plot([float(r['x_m']) for r in pts],[float(r['y_m']) for r in pts],lw=3.0,label=name(p),alpha=.95)
ax.scatter([1.15,.35],[.35,1.15],s=[230,210],c=['#f9a64f','#f9a64f'],edgecolors='white',zorder=5)
ax.set_xlabel('Planar tool x (m)',color='white');ax.set_ylabel('Planar tool y (m)',color='white');ax.tick_params(colors='white');ax.spines[:].set_color('white');ax.set_title('RECONFIGURABLE ROBOTIC TRAJECTORY COSTS  |  paceval',color='white',size=19,pad=19,weight='bold');ax.legend(facecolor='#132b46',labelcolor='white',loc='best');ax.grid(alpha=.13,color='white');saved('00_robotic_trajectory_hero')
fig,ax=plt.subplots(figsize=(9,5));
for p in policies[:4]:
 pts=sub(p);ax.plot([float(r['x_m']) for r in pts],[float(r['y_m']) for r in pts],lw=2,label=name(p))
for x,y,rad in [(.35,1.15,.13),(1.60,.35,.14)]:ax.add_patch(plt.Circle((x,y),rad,edgecolor='#ca6446',facecolor='#eeb3a2',alpha=.4))
ax.axis('equal');ax.set_xlabel('End-effector x (m)');ax.set_ylabel('End-effector y (m)');ax.set_title('Selected complete end-effector paths');ax.legend(fontsize=8);ax.grid(alpha=.2);saved('01_selected_cartesian_paths')
fig,ax=plt.subplots(figsize=(9,5));
for p in policies[:4]:
 pts=sub(p);ax.plot([float(r['q1_rad']) for r in pts],[float(r['q2_rad']) for r in pts],lw=2,label=name(p))
ax.set_xlabel('Joint 1 (rad)');ax.set_ylabel('Joint 2 (rad)');ax.set_title('Joint-space path selection');ax.legend(fontsize=8);ax.grid(alpha=.2);saved('02_joint_space_paths')
fig,ax=plt.subplots(figsize=(9,5));
for p in policies[:4]:
 pts=sub(p);ax.plot([float(r['time_s']) for r in pts],[float(r['step_cost']) for r in pts],label=name(p))
ax.set_xlabel('Trajectory time (s)');ax.set_ylabel('Instantaneous weighted cost (illustrative units)');ax.set_title('Versioned model costs along selected paths');ax.legend(fontsize=8);ax.grid(alpha=.2);saved('03_cost_profiles')
fig,ax=plt.subplots(figsize=(9,5));
for p in policies[:4]:
 pts=sub(p);ax.plot([float(r['time_s']) for r in pts],[float(r['margin_m2']) for r in pts],label=name(p))
ax.axhline(0,color='firebrick',ls='--',lw=1);ax.set_xlabel('Time (s)');ax.set_ylabel('Minimum squared disk/segment margin (m²)');ax.set_title('Sampled obstacle-clearance proxies');ax.legend(fontsize=8);ax.grid(alpha=.2);saved('04_sampled_clearance')
fig,ax=plt.subplots(figsize=(9,5));
for p in policies:
 values=[r for r in rows if (r['policy'],int(r['version']))==p];ax.plot([int(r['candidate']) for r in values],[float(r['total_cost']) if int(r['feasible']) else np.nan for r in values],'-o',markersize=3,label=name(p))
ax.set_yscale('log');ax.set_xlabel('Complete candidate ID');ax.set_ylabel('Total model cost (illustrative units)');ax.set_title('Finite-feasible trajectory ranking by cost version');ax.legend(fontsize=8);ax.grid(alpha=.2);saved('05_policy_candidate_costs')
fig,ax=plt.subplots(figsize=(9,5));
for p in policies[:4]:
 pts=sub(p);ax.plot([float(r['time_s']) for r in pts],[float(r['q1_rad']) for r in pts],label=name(p))
ax.set_xlabel('Time (s)');ax.set_ylabel('Joint 1 position (rad)');ax.set_title('Temporal joint motion by operating priority');ax.legend(fontsize=8);ax.grid(alpha=.2);saved('06_joint_time_profiles')
fig,ax=plt.subplots(figsize=(8.6,5));p0=sub(('gentle',1));p1=sub(('gentle',2));
ax.plot([float(r['time_s']) for r in p0],[float(r['step_cost']) for r in p0],label='gentle v1');ax.plot([float(r['time_s']) for r in p1],[float(r['step_cost']) for r in p1],label='gentle v2')
ax.set_xlabel('Time (s)');ax.set_ylabel('Instantaneous formula cost');ax.set_title('Immutable formula revision: changed jerk preference');ax.grid(alpha=.2);ax.legend();saved('07_immutable_revision')
# Surface computed from actual exported candidate totals, not an invented continuous optimizer.
fig=plt.figure(figsize=(9,5.8));ax=fig.add_subplot(111,projection='3d');
policy_indices=np.arange(4);candidate_indices=np.arange(16);P,C=np.meshgrid(policy_indices,candidate_indices,indexing='ij');Z=np.full_like(P,np.nan,dtype=float)
for k,p in enumerate(policies[:4]):
 for r in rows:
  if (r['policy'],int(r['version']))==p and int(r['feasible']):Z[k,int(r['candidate'])]=float(r['total_cost'])
ax.plot_surface(C,P,np.ma.masked_invalid(Z),cmap='viridis',alpha=.85,linewidth=.1);ax.set_xlabel('Candidate index');ax.set_ylabel('Policy index');ax.set_zlabel('');ax.text2D(0.81,0.85,'Cost (a.u.)',transform=ax.transAxes,fontsize=9);ax.set_yticks(range(4));ax.set_yticklabels([x[0] for x in policies[:4]],fontsize=7);ax.set_title('Discrete cost surface: actual paceval trajectory totals');saved('08_discrete_cost_surface')
print('Generated hero and eight research diagrams, all based on executed SDK CSV output')
