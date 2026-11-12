#!/usr/bin/env python3
"""Create publication-quality figures from the published deterministic CSV data."""
import csv
from collections import defaultdict
from pathlib import Path
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent.parent
EXAMPLES=ROOT/'examples'; OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
NAVY='#102d43'; CYAN='#087b9e'; BLUE='#4fa9ce'; GREEN='#16a085'; ORANGE='#cb8238'; GREY='#6f7e8d'; LIGHT='#f1f6f9'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'white',
                     'axes.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,
                     'axes.labelcolor':NAVY,'axes.titleweight':'bold','axes.titlesize':12,
                     'grid.color':'#dde6eb','savefig.facecolor':'white'})
def read(name):
 with (EXAMPLES/name).open(newline='') as f:return list(csv.DictReader(f))
def save(fig,name):
 fig.tight_layout(pad=2.0)
 for ext in ['png','svg']:fig.savefig(OUT/(name+'.'+ext),dpi=170,bbox_inches='tight')
 plt.close(fig)
shocks=read('factor_shocks.csv');distribution=[r for r in shocks if r['type']=='distribution']
metrics=read('risk_metrics.csv');stresses=read('stress_results.csv');update=read('rule_update.csv')
# Chart 1: precise architecture and division of responsibility.
fig,ax=plt.subplots(figsize=(11.1,3.6));ax.set_xlim(0,12.4);ax.set_ylim(0,4);ax.axis('off')
labels=[('Synthetic factor shocks','C++ host / CSV'),('100 prepared expressions','paceval SDK'),
 ('Batched P&L outputs','paceval SDK'),('VaR, ES and audit','C++ + Python')]
for i,(name,tag) in enumerate(labels):
 x=.15+i*3.1;ax.add_patch(FancyBboxPatch((x,.95), (2.70),2.15,boxstyle='round,pad=0.14',
 linewidth=1.4,edgecolor=BLUE,facecolor=LIGHT))
 ax.text(x+1.35,2.25,name,ha='center',va='center',fontweight='bold',fontsize=10,color=NAVY)
 ax.text(x+1.35,1.65,tag,ha='center',va='center',fontsize=9,color=GREY)
 if i<3: ax.annotate('',xy=(x+3.08,2.0),xytext=(x+2.82,2.0),arrowprops={'arrowstyle':'->','lw':2.3,'color':CYAN})
ax.text(6.2,3.68,'Mathematical execution vs. risk-analysis responsibilities',ha='center',fontsize=15,color=NAVY,fontweight='bold')
ax.text(6.2,0.30,'Only formula evaluation is attributed to paceval; risk estimators and scenario design belong to the host',ha='center',fontsize=9,color=GREY)
save(fig,'01_execution_architecture')
# Chart 2: four factors in comparable scale-normalized units.
fig,ax=plt.subplots(figsize=(10.5,4.2))
for key,scale,name,col in [('eq',.025,'Equity',CYAN),('ir',.0015,'Rates',GREEN),('fx',.015,'FX',ORANGE),('cr',.002,'Credit',GREY)]:
 v=np.array([float(r[key])/scale for r in distribution]);bins=np.linspace(-5.5,5.5,70)
 ax.hist(v,bins=bins,density=True,histtype='step',linewidth=1.8,label=name,color=col)
ax.set_title('Synthetic factor-shock distributions (scale-normalized)')
ax.set_xlabel('Shock divided by its disclosed scale parameter');ax.set_ylabel('Density');ax.grid(True,alpha=.7);ax.legend(frameon=False,ncol=4)
save(fig,'02_factor_shock_distributions')
# Read 410k output rows once, build a 1-model loss sample and max errors.
loss=[];differences=[];rule_count=0
with (EXAMPLES/'evaluations.csv').open(newline='') as f:
 for r in csv.DictReader(f):
  if r['rule_id']=='17':loss.append(-float(r['paceval_pnl']))
  if int(r['scenario_id'])%23==0: differences.append(float(r['abs_difference']))
  rule_count+=1
# Chart 3: full rule 17 loss distribution.
fig,ax=plt.subplots(figsize=(10.5,4.2));ax.hist(loss,bins=75,color=BLUE,alpha=.75,edgecolor='white',linewidth=.2)
selected=metrics[17];v95=float(selected['var95_loss']);es=float(selected['es975_loss']);
ax.axvline(v95,color=CYAN,linewidth=2,label='Empirical VaR 95%');ax.axvline(es,color=ORANGE,linewidth=2,label='ES 97.5% (tail mean)')
ax.set_title('Illustrative loss distribution for versioned rule 17')
ax.set_xlabel('Synthetic portfolio loss (arbitrary monetary units)');ax.set_ylabel('Scenario count');ax.grid(True,axis='y',alpha=.45);ax.legend(frameon=False)
save(fig,'03_pnl_distribution')
# Chart 4: risk metrics for all model variations.
ids=np.array([int(r['rule_id']) for r in metrics]);var=np.array([float(r['var95_loss']) for r in metrics]);es=np.array([float(r['es975_loss']) for r in metrics]);
fig,ax=plt.subplots(figsize=(10.5,4.2));ax.plot(ids,var,'-',linewidth=1.8,label='VaR 95%',color=CYAN)
ax.plot(ids,es,'-',linewidth=1.8,label='ES 97.5%',color=ORANGE)
ax.set_title('Scenario-based risk metrics across 100 model versions');ax.set_xlabel('Rule ID');ax.set_ylabel('Synthetic loss amount');ax.grid(True,alpha=.6);ax.legend(frameon=False)
save(fig,'04_var_es_across_models')
# Chart 5: named stresses show concentration differences across model families.
heat=np.zeros((100,6))
for r in stresses:heat[int(r['rule_id']),int(r['scenario_id'])-4096]=-float(r['paceval_pnl'])
fig,ax=plt.subplots(figsize=(10.5,4.4));im=ax.imshow(heat.T,interpolation='nearest',cmap='RdBu_r',aspect='auto',vmin=-np.max(np.abs(heat)),vmax=np.max(np.abs(heat)))
ax.set_title('Separate hypothetical stress-case losses (not used in VaR / ES)')
ax.set_yticks(np.arange(6),[f'Stress {i+1}' for i in range(6)]);ax.set_xlabel('Versioned mathematical rule ID');fig.colorbar(im,ax=ax,label='Loss / gain (synthetic units)',shrink=.9)
save(fig,'05_named_stress_scenarios')
# Chart 6: controlled rule update and unaffected version.
chg=np.array([float(r['new_pnl'])-float(r['old_pnl']) for r in update]);idx=np.arange(len(chg))
fig,ax=plt.subplots(figsize=(10.5,4.2));ax.plot(idx,chg,marker='o',markersize=4,color=GREEN,linewidth=1.5)
ax.axhline(0,color=GREY,lw=.7);ax.set_title('Rule 17 update: change of the equity delta coefficient')
ax.set_xlabel('Audited scenario index');ax.set_ylabel('v2 P&L minus v1 P&L');ax.grid(True,alpha=.5)
save(fig,'06_version_update_isolation')
# Chart 7: numerical residuals from independently coded native C++.
fig,ax=plt.subplots(figsize=(10.5,4.2));err=np.array(differences)
ax.hist(err,bins=55,color=CYAN,alpha=.8);ax.set_title('Mathematical evaluation residuals: paceval vs independent C++')
ax.set_xlabel('Absolute difference (synthetic monetary units)');ax.set_ylabel('Number of sampled evaluations');ax.grid(True,axis='y',alpha=.5)
save(fig,'07_numerical_crosscheck')
# Chart 8: demonstrate output distribution from each formula family rather than unsupported benchmark.
fig,ax=plt.subplots(figsize=(10.5,4.2))
families=['linear delta','delta + gamma','cross-factor','downside nonlinear']
for family,name,col in zip(range(4),families,[CYAN,GREEN,ORANGE,NAVY]):
 cur=[float(r['es975_loss']) for r in metrics if int(r['family'])==family]
 ax.boxplot(cur,positions=[family+1],widths=.5,patch_artist=True,
            boxprops={'facecolor':col,'alpha':.4,'edgecolor':col},
            medianprops={'color':col},whiskerprops={'color':col},capprops={'color':col})
ax.set_xticks([1,2,3,4],families,rotation=12);ax.set_ylabel('Empirical ES 97.5% (synthetic loss)');
ax.set_title('Four permitted mathematical approximation families');ax.grid(True,axis='y',alpha=.5)
save(fig,'08_formula_family_comparison')
print(f'Generated 8 scientific figures from {rule_count:,} distribution scenario evaluations')
