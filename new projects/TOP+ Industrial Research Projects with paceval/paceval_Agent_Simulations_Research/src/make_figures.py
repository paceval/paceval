"""Render publication figures from the real WP035 paceval CSV outputs only."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; F=R/'figures'; F.mkdir(exist_ok=True)
def rows(name):return list(csv.DictReader((R/'examples'/name).open()))
ss=rows('scenario_summary.csv');tt=rows('simulation_trace.csv');srf=rows('residual_surface.csv');rev=rows('version_comparison.csv');logs=rows('orchestration_log.csv')
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'figure.facecolor':'white','axes.grid':True,'grid.alpha':.18})
def save(name):plt.tight_layout(pad=2.4);plt.savefig(F/(name+'.png'),dpi=190,bbox_inches='tight');plt.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close()
# Figure 1: the industrial orchestration workflow, conceptual diagram based on executed stages (not data plot).
fig,ax=plt.subplots(figsize=(11,3.5));ax.set_xlim(0,10);ax.set_ylim(0,3);ax.axis('off')
for x,c,t in [(0.2,'#E5F0F4','Validated input'),(2.2,'#D8EBF5','Deterministic controller'),(4.25,'#CCEDE8','paceval graph evaluation'),(6.4,'#FBEBD7','Residual / retry policy'),(8.45,'#E4F2E6','Audit and decision')]:
 from matplotlib.patches import FancyBboxPatch
 ax.add_patch(FancyBboxPatch((x,.95),1.45,1.07,boxstyle='round,pad=.05,rounding_size=.1',facecolor=c,edgecolor='#526779'))
 ax.text(x+.725,1.49,t,ha='center',va='center',fontsize=8.0,wrap=True)
for x in [1.72,3.78,5.93,8.02]:ax.annotate('',xy=(x+.39,1.5),xytext=(x,1.5),arrowprops=dict(arrowstyle='->',lw=1.8,color='#16858E'))
ax.set_title('Deterministic agent-like scientific orchestration — verified architecture',loc='left',fontweight='bold');save('01_workflow')
# Plot individual representative scenarios
fig,axs=plt.subplots(3,1,figsize=(9,8),sharex=True)
for m,ax in enumerate(axs):
 seq=[r for r in tt if int(r['scenario_id'])==m]
 x=[float(r['time_s']) for r in seq];ax.plot(x,[float(r['observed']) for r in seq],label='Reference observation (synthetic)',lw=2);ax.plot(x,[float(r['simulated']) for r in seq],'--',label='paceval simulated state',lw=1.6)
 ax.set_ylabel(['Thermal state','Damped state','Logistic state'][m]);ax.legend(fontsize=8,loc='best');
axs[-1].set_xlabel('Simulated time (dimensionless steps × 0.025)');fig.suptitle('Three different reusable mathematical simulation graphs');save('02_model_trajectories')
fig,ax=plt.subplots(figsize=(9,4));initial=np.array([float(x['initial_score']) for x in ss]);final=np.array([float(x['final_score']) for x in ss]);ax.scatter(initial,final,c=[int(x['model']) for x in ss],s=30,cmap='viridis',alpha=.8);ax.plot([0,max(initial)*1.01],[0,max(initial)*1.01],color='gray',ls=':');ax.axhline(.005,color='#CC7722',ls='--',label='Demonstration threshold');ax.set(xlabel='First-run average squared normalized residual',ylabel='Final-run average squared normalized residual',title='Scenario scores before and after deterministic policy');ax.legend();save('03_retry_scores')
fig,ax=plt.subplots(figsize=(8,4));names=['ACCEPT','REVIEW'];nums=[sum(x['decision']==s for x in ss) for s in names];bars=ax.bar(names,nums,color=['#1D8D88','#DF9750']);ax.bar_label(bars);ax.set(ylabel='Number of scenarios',title='Decision distribution in the 100-scenario research workload');save('04_decisions')
# Scatter of score by model
fig,ax=plt.subplots(figsize=(9,4));
for m in range(3):
 sub=[float(x['final_score']) for x in ss if int(x['model'])==m];ax.scatter(np.full(len(sub),m)+np.linspace(-.13,.13,len(sub)),sub,s=17,alpha=.65,label=['Thermal','Damped','Logistic'][m]);
ax.axhline(.005,color='#C76B28',ls='--');ax.set_xticks(range(3),['Thermal','Damped forced','Logistic']);ax.set_yscale('symlog',linthresh=1e-6);ax.set(ylabel='Final average normalized squared residual (symlog)',title='Different scientific model families share one orchestration policy');save('05_model_scores')
G=np.array([float(r['normalized_residual']) for r in srf]).reshape(61,61);sim=np.array(sorted(set(float(r['simulated']) for r in srf)));obs=np.array(sorted(set(float(r['observed']) for r in srf)));S,O=np.meshgrid(sim,obs,indexing='ij')
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(projection='3d');surf=ax.plot_surface(S,O,G,cmap='viridis',linewidth=0,rstride=2,cstride=2);ax.set(xlabel='Simulated state',ylabel='Observed state',zlabel='Normalized absolute residual',title='Actual paceval 3D residual surface (3,721 points)');fig.colorbar(surf,ax=ax,shrink=.65,pad=.12);save('06_residual_surface_3d')
fig,ax=plt.subplots(figsize=(8,5));cs=ax.contourf(S,O,G,levels=25,cmap='viridis');fig.colorbar(cs,ax=ax,label='Normalized absolute residual');ax.plot(sim,sim,'w--',lw=1.7,label='Matching states');ax.set(xlabel='Simulated state',ylabel='Observed state',title='paceval residual contour map (same 3,721 points)');ax.legend();save('07_residual_contour')
fig,ax=plt.subplots(figsize=(8,4));xx=[float(x['x']) for x in rev];ax.plot(xx,[float(x['rhs_v1']) for x in rev],label='Retained thermal graph v1',lw=2);ax.plot(xx,[float(x['rhs_v2']) for x in rev],label='Additional thermal graph v2',lw=2);ax.set(xlabel='Model state',ylabel='State derivative',title='Immutable graph versions remain simultaneously callable');ax.legend();save('08_versioned_models')
# hero: a data-driven typographic technical editorial rendering, explicitly not a numerical result.
fig,ax=plt.subplots(figsize=(14,5.2),facecolor='#0C233A');ax.set_facecolor('#0C233A');ax.axis('off');ax.set_xlim(0,14);ax.set_ylim(0,5.2)
from matplotlib.patches import FancyBboxPatch
for i,(a,b,c) in enumerate([(0.5,1.75,'INPUT'),(3.35,1.75,'ORCHESTRATE'),(6.2,1.75,'EVALUATE'),(9.05,1.75,'VERIFY'),(11.9,1.75,'DECIDE')]):
 ax.add_patch(FancyBboxPatch((a,b),1.55,1.35,boxstyle='round,pad=.10,rounding_size=.16',edgecolor='#42D4C8',linewidth=1.5,facecolor='#173B58'))
 ax.text(a+.775,b+.68,c,color='white',size=10,weight='bold',ha='center',va='center')
 if i<4:ax.annotate('',xy=(a+2.6,b+.7),xytext=(a+1.73,b+.7),arrowprops=dict(arrowstyle='->',color='#F6C572',lw=2))
ax.text(.55,4.55,'WP 035  /  AGENT-ORCHESTRATED MATHEMATICAL SIMULATIONS',color='white',fontsize=15,fontweight='bold')
ax.text(.55,.58,'Simulation states  •  Reusable mathematical execution graphs  •  Auditable decisions',color='#AFDEEB',fontsize=11)
fig.savefig(F/'00_workflow_hero.png',dpi=200,facecolor='#0C233A',bbox_inches='tight');plt.close(fig)
print('Generated 8 publication figures plus distinct graphical cover.')
