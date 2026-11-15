#!/usr/bin/env python3
"""Figures use actual original paceval result tables, not freshly computed surrogate fields."""
from pathlib import Path
import csv,math,json
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
root=Path(__file__).resolve().parents[1];out=root/'figures';out.mkdir(exist_ok=True)
def read(f):return list(csv.DictReader((root/'results'/f).open()))
S=read('screening.csv');P=read('state_samples.csv');C=read('model_comparison.csv');T=read('closed_loop_traces.csv')
def save(name):
 plt.tight_layout(pad=1.5);plt.savefig(out/(name+'.png'),dpi=190,bbox_inches='tight');plt.savefig(out/(name+'.pdf'),bbox_inches='tight');plt.close()
def title(t):plt.title(t,fontsize=12,pad=12)
plt.figure(figsize=(8.4,4.4))
v1=[r for r in S if r['model']=='V1'];v2=[r for r in S if r['model']=='V2'];xx=np.arange(len(v1))
plt.scatter(xx,[float(r['analytic_cert_margin']) for r in v1],s=9,label='V1 linear feedback',alpha=.8)
plt.scatter(xx,[float(r['analytic_cert_margin']) for r in v2],s=9,label='V2 nonlinear feedback',alpha=.8)
plt.axhline(0,ls='--',lw=1);plt.xlabel('Candidate index');plt.ylabel('Sufficient Lyapunov coefficient margin');plt.legend();title('Analytic coefficient margins across candidate laws');save('fig01_certificate_margins')
plt.figure(figsize=(7.2,4.3));labels=['Sampled pass','Analytic certificate'];a=[sum(int(r['sampled_pass']) for r in v1),sum(int(r['analytic_certificate']) for r in v1)];b=[sum(int(r['sampled_pass']) for r in v2),sum(int(r['analytic_certificate']) for r in v2)];x=np.arange(2);width=.36
plt.bar(x-width/2,a,width,label='V1');plt.bar(x+width/2,b,width,label='V2');plt.xticks(x,labels);plt.ylim(0,200);plt.ylabel('Candidates out of 192');plt.legend();title('Sampling is not an analytic certificate');save('fig02_screening_funnel')
for model,num in [('V1','fig03_v1_residual_map'),('V2','fig04_v2_residual_map')]:
 p=[r for r in P if r['candidate_id']=='C0000' and r['model']==model];x=np.array([float(q['x']) for q in p]);y=np.array([float(q['y']) for q in p]);z=np.array([float(q['lyapunov_margin']) for q in p]);plt.figure(figsize=(6.6,5.1));tri=Triangulation(x,y);plt.tricontourf(tri,z,levels=19);plt.colorbar(label='Lyapunov residual (-eps |x|² - Vdot)');plt.contour # no effect
 plt.xlabel('$x_1$');plt.ylabel('$x_2$');plt.gca().set_aspect('equal');title('Computed state-space Lyapunov margin - '+model);save(num)
# Three-dimensional directly evaluated Vdot field
p=[r for r in P if r['candidate_id']=='C0000' and r['model']=='V2'];x=np.array([float(q['x']) for q in p]);y=np.array([float(q['y']) for q in p]);z=np.array([float(q['Vdot']) for q in p]);fig=plt.figure(figsize=(7.5,5.3));ax=fig.add_subplot(111,projection='3d');ax.plot_trisurf(x,y,z,cmap='viridis',linewidth=0,antialiased=True,alpha=.96);ax.set_xlabel('$x_1$');ax.set_ylabel('$x_2$');ax.set_zlabel('Vdot');ax.set_title('Actual paceval Lyapunov derivative surface');save('fig05_vdot_surface')
plt.figure(figsize=(8.4,4.5))
for model in ['V1','V2']:
 p=[r for r in T if r['candidate_id']=='C0000' and r['model']==model and r['initial_case']=='0'];plt.plot([float(q['time']) for q in p],[float(q['V']) for q in p],label=model)
plt.yscale('log');plt.xlabel('Simulation time (s)');plt.ylabel('Quadratic V');plt.legend();title('Closed-loop trajectory with original paceval RHS in RK4');save('fig06_trajectory_decay')
plt.figure(figsize=(8.3,4.4))
d=[float(r['delta_Vdot_x03_y04']) for r in C];plt.hist(d,bins=36);plt.axvline(0,ls='--',lw=1);plt.xlabel('V2 - V1 Lyapunov derivative at x=(0.3,0.4)');plt.ylabel('Candidates');title('Influence of bounded nonlinear feedback');save('fig07_nonlinear_controller_delta')
plt.figure(figsize=(7,5))
for model,marker in [('V1','o'),('V2','x')]:
 p=[r for r in S if r['model']==model];plt.scatter([float(q['analytic_cert_margin']) for q in p],[float(q['global_actuator_margin']) for q in p],marker=marker,s=18,label=model,alpha=.7)
plt.axvline(0,ls='--',lw=1);plt.axhline(0,ls='--',lw=1);plt.xlabel('Lyapunov sufficient margin');plt.ylabel('Disk-wide actuator headroom');plt.legend();title('Two distinct sufficient acceptance conditions');save('fig08_joint_constraints')
plt.figure(figsize=(8.1,4.6))
for model in ['V1','V2']:
 p=[r for r in T if r['candidate_id']=='C0001' and r['model']==model and r['initial_case']=='0'];plt.plot([float(q['time']) for q in p],[float(q['V']) for q in p],label=model)
plt.xlabel('Simulation time (s)');plt.ylabel('Quadratic V');plt.legend();title('Counterexample candidate, finite-horizon simulation');save('fig09_counterexample_trajectory')
plt.figure(figsize=(7.4,4.6))
for model in ['V1','V2']:
 p=[r for r in S if r['model']==model];v=[int(q['sampled_violations']) for q in p];plt.hist(v,bins=np.arange(-.5,max(v)+2.5,2),alpha=.65,label=model)
plt.xlabel('Number of sampled state violations per candidate');plt.ylabel('Candidates');plt.legend();title('Explicit sampled counterexamples to candidate inequalities');save('fig10_counterexample_counts')
print('SCIENTIFIC FIGURES',len(list(out.glob('fig*.png'))))
