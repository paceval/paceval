#!/usr/bin/env python3
"""All quantitative figures use emitted results from the original paceval SDK run."""
from pathlib import Path
import pandas as pd,numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap
P=Path(__file__).resolve().parents[1]
F=P/'figures';F.mkdir(exist_ok=True)
r=pd.read_csv(P/'results/inference_results.csv'); m=pd.read_csv(P/'results/split_metrics.csv'); rev=pd.read_csv(P/'results/model_revision.csv'); surf=pd.read_csv(P/'results/threshold_surface.csv')
ink='#1E2C33';pink='#CE5068';teal='#248A86';amber='#D59A4C';purple='#7E6CB2';grey='#6B7780';pale='#F7F8F8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titleweight':'bold','axes.labelcolor':ink,'axes.edgecolor':'#ABB8BB','text.color':ink,'xtick.color':grey,'ytick.color':grey,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'grid.color':'#DDE3E3','savefig.facecolor':'white'})
def save(n, fig):
 fig.savefig(F/f'{n}.png',dpi=190,bbox_inches='tight',pad_inches=.16)
 fig.savefig(F/f'{n}.pdf',bbox_inches='tight',pad_inches=.16)
 plt.close(fig)
def decorate(ax):ax.grid(True,axis='y',alpha=.5);ax.set_axisbelow(True)
# 01 conceptual workflow, diagram not data-based
fig,ax=plt.subplots(figsize=(13.8,3));ax.set_xlim(0,13.55);ax.set_ylim(0,3);ax.axis('off')
xs=[.2,2.9,5.6,8.3,11.0];titles=['Sensor features','Frozen trained MLP','paceval formulas','Versioned scoring','Advisory output']
sub=['8 synthetic inputs','8-8-4-1; two revisions','Layered and flattened','Margins, drift and weights','MONITOR / REVIEW / INSPECT']
for i,x in enumerate(xs):
 ax.add_patch(FancyBboxPatch((x,.72),2.2,1.6,boxstyle='round,pad=.15,rounding_size=.12',facecolor=('#F8F1F2' if i in [2,3] else '#E9F3F2'),edgecolor=pink if i in [2,3] else teal,linewidth=1.5))
 ax.text(x+1.1,1.65,titles[i],ha='center',va='center',fontsize=11,fontweight='bold')
 ax.text(x+1.1,1.08,sub[i],ha='center',va='center',fontsize=8,wrap=True)
 if i<4:ax.add_patch(FancyArrowPatch((x+2.35,1.55),(xs[i+1]-.08,1.55),arrowstyle='-|>',mutation_scale=13,color=amber,linewidth=1.6))
ax.set_title('Mathematical inference is one component of a governed monitoring workflow',pad=4)
save('01_pipeline_architecture',fig)
# 02 accuracy and false alarm by split
order=['train','validation','test','shift_test']; labels=['Training','Validation','Held-out bearings','Shifted operation']
fig,(ax,ay)=plt.subplots(1,2,figsize=(12.5,4.4));x=np.arange(4);w=.35
for k,(version,color) in enumerate([('v1',teal),('v2',pink)]):
 a=m.set_index(['version','split']).loc[[(version,s) for s in order]]
 ax.bar(x+(k-.5)*w,a.accuracy.values,width=w,color=color,label=version)
 ay.bar(x+(k-.5)*w,a.negative_false_alarm_rate.values*100,width=w,color=color)
ax.set_ylim(0,1.08);ax.set_ylabel('Classification accuracy');ax.set_xticks(x,labels,rotation=13);decorate(ax);ax.legend(frameon=False);ax.set_title('Synthetic bearing group classification')
ay.set_ylabel('False-alert rate among negatives [%]');ay.set_xticks(x,labels,rotation=13);ay.set_title('Domain shift changes the operational error profile');decorate(ay)
fig.tight_layout();save('02_generalization_and_false_alerts',fig)
# 03 Distribution on held-out vs shifted, v1 & v2
fig,axs=plt.subplots(1,2,figsize=(11.5,4.25),sharey=True)
for ax,vers in zip(axs,['v1','v2']):
 for sp,col in [('test',teal),('shift_test',pink)]:
  a=r[(r.model_version==vers)&(r.split==sp)].paceval_layered_score
  ax.hist(a,bins=np.linspace(0,1,32),color=col,alpha=.58,density=True,label=('held-out' if sp=='test' else 'shifted'))
 ax.axvline(.5,color=ink,linestyle='--',lw=1.5);ax.set_title(f'Model {vers}');ax.set_xlim(0,1);ax.set_xlabel('Frozen network output (not a calibrated probability)');decorate(ax)
axs[0].set_ylabel('Normalized frequency');axs[1].legend(frameon=False);fig.tight_layout();save('03_synthetic_score_distributions',fig)
# 04 version scatter
fig,ax=plt.subplots(figsize=(7,6));r1=rev[rev.split=='test'];r2=rev[rev.split=='shift_test'];ax.scatter(r1.score_v1,r1.score_v2,s=22,alpha=.7,c=teal,label='Held-out');ax.scatter(r2.score_v1,r2.score_v2,s=23,alpha=.65,c=pink,label='Shifted')
ax.plot([0,1],[0,1],color=grey,linestyle='--',lw=1);ax.axvline(.5,color=amber,ls=':',lw=1);ax.axhline(.5,color=amber,ls=':',lw=1);ax.set(xlim=(0,1),ylim=(0,1),xlabel='Frozen model v1',ylabel='Frozen model v2',title='Numerically reproduced model revision');ax.legend(frameon=False);decorate(ax);fig.tight_layout();save('04_version_revision_scatter',fig)
# 05 operating shift effect on feature scale
samples=pd.read_csv(P/'examples/synthetic_bearing_features.csv');z=pd.DataFrame({'split':r[r.model_version=='v1'].split.values,'distance':r[r.model_version=='v1'].normalized_shift_distance.values})
fig,ax=plt.subplots(figsize=(9,4));data=[z[z.split==s].distance.values for s in order];bp=ax.boxplot(data,tick_labels=labels,patch_artist=True,showfliers=False,medianprops={'color':ink,'linewidth':1.5});
for patch,c in zip(bp['boxes'],[teal,teal,teal,pink]):patch.set_facecolor(c);patch.set_alpha(.45)
ax.set_ylabel('RMS normalized feature distance');ax.set_title('Actual paceval drift-surrogate output by held-out partition');decorate(ax);fig.tight_layout();save('05_normalized_feature_shift',fig)
# 06 functional execution inventory (no performance comparison).
registry=pd.read_csv(P/'results/graph_registry.csv')
counts=registry.groupby(['domain','version']).size().unstack(fill_value=0)
order_domains=['preprocessing','neural','fused_neural','decision_math']
counts=counts.reindex(order_domains).fillna(0)
fig,ax=plt.subplots(figsize=(10.2,4.6));x=np.arange(len(order_domains));bottom=np.zeros(len(x))
for version,color in [('shared',grey),('v1',teal),('v2',pink)]:
 vals=counts[version].values if version in counts.columns else np.zeros(len(x))
 ax.bar(x,vals,bottom=bottom,label=version,color=color,width=.55)
 for i,v in enumerate(vals):
  if v>0:ax.text(i,bottom[i]+v/2,str(int(v)),ha='center',va='center',fontweight='bold',color='white')
 bottom+=vals
ax.set_xticks(x,['Normalization','Neural layers','Flattened exports','Decision mathematics'])
ax.set_ylabel('Executed reusable paceval graphs')
ax.set_title('Functional coverage of two frozen model revisions')
ax.legend(frameon=False,ncol=3)
ax.set_ylim(0,max(bottom)*1.17);decorate(ax);fig.tight_layout();save('06_paceval_graph_coverage',fig)
# 07 formula representation char count
import json
trace=json.loads((P/'results/recordformula_trace.json').read_text())
fig,ax=plt.subplots(figsize=(9,4.1))
names=['v1','v2'];full=[trace[v]['full_expression_character_count'] for v in names];bounded=[sum(len(y['formula_with_intermediate_variables']) for y in trace[v]['intermediate_variable_formulas']) for v in names]
x=np.arange(2);w=.32;ax.bar(x-w/2,full,width=w,color=pink,label='One flattened expression');ax.bar(x+w/2,bounded,width=w,color=teal,label='Intermediate-variable formula sum');ax.set_xticks(x,['Frozen model v1','Frozen model v2']);ax.set_ylabel('Exported expression characters');ax.set_title('Dynamic scalar trace demonstrates expression-size trade-off');ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(.02,1.01),ncol=2);decorate(ax);ax.set_ylim(0,max(full)*1.32);fig.tight_layout();save('07_formula_export_size',fig)
# 08 out decisions
fig,axs=plt.subplots(1,2,figsize=(11.5,4))
for ax,vers in zip(axs,['v1','v2']):
 counts=r[(r.model_version==vers)&(r.split.isin(['test','shift_test']))].groupby(['split','advisory_action']).size().unstack(fill_value=0).reindex(['test','shift_test']).fillna(0)
 bottom=np.zeros(2)
 for name,color in [('MONITOR',teal),('REVIEW',amber),('ADVISE_INSPECTION',pink)]:
  vals=counts[name].values if name in counts.columns else np.zeros(2)
  ax.bar(['Held-out','Shifted'],vals,bottom=bottom,label=name,color=color)
  bottom+=vals
 ax.set_title(f'{vers}: advisory policy count');ax.set_ylabel('Synthetic vectors');decorate(ax)
axs[1].legend(frameon=False,bbox_to_anchor=(1.02,1),loc='upper left');fig.tight_layout();save('08_advisory_outcomes',fig)
# 09 3D margin surface measured via real paceval
from mpl_toolkits.mplot3d import Axes3D
u=surf[surf.model_version=='v1'];xs=sorted(u.score.unique());ys=sorted(u.threshold.unique());M=u.pivot(index='threshold',columns='score',values='decision_margin').values
X,Y=np.meshgrid(xs,ys)
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');surface=ax.plot_surface(X,Y,M,cmap='coolwarm',alpha=.88,linewidth=0,antialiased=True);ax.set(xlabel='Neural output',ylabel='Decision threshold',zlabel='Signed margin',title='Real paceval threshold-margin graph surface');ax.view_init(elev=26,azim=-60);fig.colorbar(surface,shrink=.62,pad=.10);fig.tight_layout();save('09_threshold_margin_surface_3d',fig)
# 10 functional numerical parity vs native on heldout
fig,ax=plt.subplots(figsize=(10,4.3));v=r[(r.model_version=='v1')&(r.split=='test')].copy().reset_index(drop=True)
ax.plot(np.arange(len(v)),v.paceval_layered_score,color=teal,lw=1.6,label='paceval layer-wise')
ax.plot(np.arange(len(v)),v.native_cpp_score,color=pink,lw=.9,ls='--',label='native C++')
ax.set(xlabel='Held-out feature vector index',ylabel='Score',title='Frozen trained inference: identical numerical predictions');ax.legend(frameon=False);decorate(ax);fig.tight_layout();save('10_executed_reference_overlay',fig)
# 11 soft score vs original uncalibrated
fig,ax=plt.subplots(figsize=(8,5));v=r[(r.model_version=='v2') & (r.split=='shift_test')]
sc=ax.scatter(v.paceval_layered_score,v.advisory_index,c=v.normalized_shift_distance,cmap='magma',s=29,alpha=.75)
ax.plot([0,1],[0,1],ls='--',color=grey,lw=1);ax.set(xlabel='Frozen neural output',ylabel='Versioned paceval advisory index',title='Application-specific mathematical rule, not calibrated risk');fig.colorbar(sc,ax=ax,label='Normalized shift distance');decorate(ax);fig.tight_layout();save('11_paceval_composite_advisory_score',fig)
print('Saved figures:',len(list(F.glob('*.png'))))

# 12 actually executed non-linear advisory function, not merely an affine decision margin.
ad=pd.read_csv(P/'results/advisory_surface.csv');u=ad[ad.model_version=='v2'];xx=sorted(u.normalized_vibration.unique());yy=sorted(u.normalized_speed.unique());M=u.pivot(index='normalized_speed',columns='normalized_vibration',values='advisory_index').values;X,Y=np.meshgrid(xx,yy)
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');sf=ax.plot_surface(X,Y,M,cmap='viridis',edgecolor='none',alpha=.95);ax.set(xlabel='Normalized vibration',ylabel='Normalized speed',zlabel='Advisory index',title='Real paceval operating-point correction, frozen score 0.5');ax.view_init(elev=27,azim=-62);fig.colorbar(sf,ax=ax,shrink=.58,pad=.1);fig.tight_layout();save('12_operating_point_surface_3d',fig)
