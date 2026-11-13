#!/usr/bin/env python3
"""Recreate 10 substantive scientific figures from archived real paceval result CSVs."""
from pathlib import Path
import csv,sys,collections
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
root=Path(sys.argv[1]);out=root/'figures';out.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/'results'/'decision_results.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'figure.dpi':135,'savefig.dpi':200})
status_colors={'ACCEPT':'#288e78','REVIEW':'#e6ac47','REJECT':'#b64f58'}
def save(fig,name):
    fig.savefig(out/(name+'.png'),dpi=220,bbox_inches='tight',facecolor='white');fig.savefig(out/(name+'.pdf'),bbox_inches='tight',facecolor='white');plt.close(fig)
# 01 Architecture: manually drawn non-data architecture, figure caption identifies as schematic.
fig,ax=plt.subplots(figsize=(12,3.4));ax.set(xlim=(0,12),ylim=(0,3));ax.axis('off')
steps=[('Six synthetic sensors','Input + range checks'),('Two paceval graphs','Sensor corrections'),('8 paceval graphs','Tree + leaf + coverage'),('24 paceval graphs','Scores, guards, sensitivities'),('C++ decision policy','Accept / Review / Reject')]
for j,(name,detail) in enumerate(steps):
 x=.15+2.42*j;box=FancyBboxPatch((x,1.15),2.22,1.15,boxstyle='round,pad=.11',linewidth=1.1,edgecolor='#25556a',facecolor='#edf5f4' if j in [1,2,3] else '#f3f1ee');ax.add_patch(box)
 ax.text(x+1.11,1.84,name,ha='center',va='center',weight='bold',fontsize=10,color='#203647');ax.text(x+1.11,1.48,detail,ha='center',va='center',fontsize=8.5,color='#55707a')
 if j<4:ax.annotate('',xy=(x+2.40,1.72),xytext=(x+2.27,1.72),arrowprops=dict(arrowstyle='->',lw=1.3,color='#497685'))
ax.set_title('Executed mathematical decision pipeline',weight='bold',pad=10);save(fig,'01_executed_architecture')
# data helper
surf={v:sorted([r for r in rows if r['case_kind']=='parameter_surface' and r['version']==v],key=lambda x:int(x['sample_id'])) for v in ['v1','v2']}
X=np.array([float(r['t_raw']) for r in surf['v1']]).reshape(20,20);Y=np.array([float(r['v_raw']) for r in surf['v1']]).reshape(20,20)
Z1=np.array([float(r['final_score']) for r in surf['v1']]).reshape(20,20)
Z2=np.array([float(r['final_score']) for r in surf['v2']]).reshape(20,20)
fig=plt.figure(figsize=(10,6));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(X,Y,Z1,cmap='viridis',linewidth=0,alpha=.95);ax.set(xlabel='Raw temperature (deg C)',ylabel='Raw vibration (mm/s)',zlabel='Computed score',title='Mathematical risk-score surface: model v1');ax.view_init(elev=24,azim=-64);save(fig,'02_model_v1_score_surface_3d')
fig,axs=plt.subplots(1,2,figsize=(12,4.4),layout='constrained');vmin=min(Z1.min(),Z2.min());vmax=max(Z1.max(),Z2.max())
for ax,z,v in zip(axs,[Z1,Z2],['v1','v2']):
 im=ax.pcolormesh(X,Y,z,shading='auto',cmap='viridis',vmin=vmin,vmax=vmax);ax.set(title=f'Formula version {v}',xlabel='Raw temperature (deg C)',ylabel='Raw vibration (mm/s)')
fig.colorbar(im,ax=axs,shrink=.88,label='paceval score');fig.suptitle('Versioned evaluation of the same sensor grid',weight='bold');save(fig,'03_two_model_score_maps')
fig,ax=plt.subplots(figsize=(9,5));im=ax.pcolormesh(X,Y,Z2-Z1,shading='auto',cmap='coolwarm',vmin=-.23,vmax=.23);fig.colorbar(im,ax=ax,label='v2 score minus v1 score');ax.set(title='Controlled model revision: change in final score',xlabel='Raw temperature (deg C)',ylabel='Raw vibration (mm/s)');save(fig,'04_version_change_surface')
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for ax,ver in zip(axs,['v1','v2']):
 values=np.array([{'ACCEPT':0,'REVIEW':1,'REJECT':2}[r['status']] for r in surf[ver]]).reshape(20,20)
 from matplotlib.colors import ListedColormap,BoundaryNorm
 cmap=ListedColormap([status_colors[x] for x in ['ACCEPT','REVIEW','REJECT']]);norm=BoundaryNorm([-.5,.5,1.5,2.5],3)
 ax.pcolormesh(X,Y,values,cmap=cmap,norm=norm,shading='auto');ax.set(title=f'{ver} decision regions',xlabel='Raw temperature (deg C)',ylabel='Raw vibration (mm/s)')
fig.suptitle('Sensor-driven decision categories on a fixed scenario grid',weight='bold');save(fig,'05_quality_decision_regions')
fig,ax=plt.subplots(figsize=(9,4.8));v1=[float(r['final_score']) for r in rows if r['version']=='v1'];v2=[float(r['final_score']) for r in rows if r['version']=='v2']
ax.hist([v1,v2],bins=35,alpha=.73,label=['v1','v2'],color=['#386e83','#cb8f5c']);ax.axvline(.30,color='#2f927d',ls='--',label='ACCEPT threshold');ax.axvline(.43,color='#b8515a',ls='--',label='REJECT threshold');ax.set(xlabel='Computed risk score',ylabel='Recorded cases',title='Risk-score distributions and policy thresholds');ax.legend(fontsize=9);save(fig,'06_score_distribution')
fig,ax=plt.subplots(figsize=(10,4.7));groups=['ACCEPT','REVIEW','REJECT'];xx=np.arange(3)
for idx,v in enumerate(['v1','v2']):
 counts=collections.Counter(r['status'] for r in rows if r['version']==v)
 ax.bar(xx+(.22 if idx else -.22),[counts[x] for x in groups],width=.44,label=v,color=['#39748a','#b77f52'][idx])
ax.set_xticks(xx,groups);ax.set(ylabel='Number of evaluated cases',title='Decision outcomes for two simultaneously retained versions');ax.legend();save(fig,'07_decision_outcome_counts')
fig,axs=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
for ax,field,title in zip(axs,['dscore_dt','dscore_dv'],['Temperature partial sensitivity','Vibration partial sensitivity']):
 for ver,col in [('v1','#39748a'),('v2','#c08154')]:
  data=[r for r in rows if r['version']==ver and r['case_kind']=='parameter_surface'];ax.scatter([float(r['t_raw']) for r in data],[float(r[field]) for r in data],alpha=.5,s=10,c=col,label=ver)
 ax.set(xlabel='Raw temperature (deg C)',ylabel=field,title=title)
axs[1].legend();fig.suptitle('Analytic within-leaf sensitivities returned by paceval',weight='bold');save(fig,'08_analytic_sensitivities')
fig,ax=plt.subplots(figsize=(10,5));v1rows=[r for r in rows if r['version']=='v1' and r['case_kind']=='synthetic_sensor']
guards=['guard_t','guard_v','guard_p','guard_l','guard_i','guard_d']
counts=[]
for ver in ['v1','v2']:
    subsetv=[r for r in rows if r['version']==ver and r['case_kind']=='synthetic_sensor']
    counts.append([sum(float(r[c])<0 for r in subsetv) for c in guards])
x=np.arange(len(guards));ax.bar(x-.2,counts[0],width=.4,label='v1',color='#3d7890');ax.bar(x+.2,counts[1],width=.4,label='v2',color='#bc8652')
ax.set_xticks(x,['Temperature','Vibration','Pressure','Load','Current','Drift']);ax.set(ylabel='Number of inputs with negative guard margin',title='Individually violated mathematical validity guards');ax.legend();save(fig,'09_constraint_guard_results')
fig,ax=plt.subplots(figsize=(10,4.6));subset=v1rows[:220]
for field,color,label in [('guard_t','#d78548','temperature (deg C)'),('guard_v','#287c9e','vibration (mm/s)'),('guard_p','#8a62a9','pressure (bar)')]:
 ax.plot([float(r[field]) for r in subset],label=label,linewidth=1,color=color)
ax.axhline(0,color='black',ls=':');ax.set(title='Three individually defined signed constraint margins',xlabel='Synthetic sensor index',ylabel='Signed margin in its respective native unit');ax.legend();save(fig,'10_selected_individual_guards')
# Figure 11 formula representation size based on actual graph strings stored in registry.
reg=list(csv.DictReader((root/'results'/'graph_registry.csv').open()))
ids=['v1_masked_tree','v1_nested_tree','v2_masked_tree','v2_nested_tree'];length=[len(next(r['formula'] for r in reg if r['graph_id']==x)) for x in ids]
fig,ax=plt.subplots(figsize=(9,4));ax.barh(ids[::-1],length[::-1],color=['#c7954f','#5e8498','#c7954f','#5e8498']);ax.set(title='Actual length of compiled mathematical source expressions',xlabel='Characters in the stored paceval expression');save(fig,'11_formula_representation')
# Generate a separate reproducible example input CSV without reusing independently produced results as provenance.
fields=['sample_id','case_kind','t_raw','v_raw','p_raw','load','current','drift']
with (root/'examples'/'synthetic_sensor_inputs.csv').open('w',newline='') as f:
 outcsv=csv.DictWriter(f,fieldnames=fields);outcsv.writeheader()
 for r in rows:
  if r['version']=='v1':outcsv.writerow({k:r[k] for k in fields})
print('Saved 11 figures (PNG and vector PDF) from executed paceval CSV data and documented architecture')
