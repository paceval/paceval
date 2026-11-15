"""Reconstruct publication graphics ONLY from saved real paceval result CSV files."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results';OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
Image.open(OUT/'00_sis_proof_test_hero.png').convert('RGB').resize((2400,1200),Image.Resampling.LANCZOS).save(OUT/'00_sis_proof_test_hero.png',optimize=True)
d=pd.read_csv(RES/'scenario_results.csv');cycle=pd.read_csv(RES/'proof_cycle.csv');surf=pd.read_csv(RES/'parameter_surface.csv');summary=pd.read_csv(RES/'model_summary.csv')
col={'M1':'#0F6D83','M2':'#EA6A37','green':'#289682','bg':'#F7F9FB'}
plt.rcParams.update({'font.size':10,'axes.titlesize':15,'axes.labelsize':11,'figure.facecolor':'white','axes.grid':True,'grid.alpha':0.2,'font.family':'DejaVu Sans','savefig.pad_inches':0.13})
figures={}
def save(fig,i,slug,caption):
    fig.tight_layout(pad=1.5)
    p=OUT/f'{i:02d}_{slug}'
    fig.savefig(p.with_suffix('.png'),dpi=180,bbox_inches='tight')
    fig.savefig(p.with_suffix('.pdf'),bbox_inches='tight')
    plt.close(fig);figures[i]={'file':p.with_suffix('.png').name,'caption':caption}

def std(title,x,y):
    f,ax=plt.subplots(figsize=(9,4.8));ax.set_title(title,loc='left',fontweight='bold');ax.set_xlabel(x);ax.set_ylabel(y);return f,ax

# Architecture diagram shows responsibilities, not a real plant or approval.
f,ax=plt.subplots(figsize=(10,4.5));ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
boxes=[(0.3,2.05,2.3,1.35,'Validated inputs','Failure rates, coverage,\ntest intervals, targets'),(3.1,2.05,2.55,1.35,'paceval graphs','1oo1 / 1oo2 models\nprobabilities and margins'),(6.2,2.05,3.25,1.35,'Independent reference','C++ / 85-digit mathematics\nno SIL verification')]
for x,y,w,h,t,b in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.14',edgecolor=col['M1'],facecolor='#EAF5F6',linewidth=1.7))
    ax.text(x+w/2,y+h*.69,t,ha='center',fontweight='bold',fontsize=12);ax.text(x+w/2,y+h*.31,b,ha='center',fontsize=9)
for x0,x1 in [(2.7,3.0),(5.78,6.08)]:ax.add_patch(FancyArrowPatch((x0,2.73),(x1,2.73),arrowstyle='-|>',mutation_scale=24,color=col['M2'],linewidth=2))
ax.text(5,.8,'Synthetic safety-reliability screening • mathematical execution only',ha='center',fontsize=12,color='#46566B')
save(f,1,'architecture','Research architecture: paceval executes the mathematical kernels, while host and independent references retain separate responsibilities.')
# Example PFD age curve direct paceval outputs
f,ax=std('Probability of failure during a proof-test interval','Elapsed time since proof test (h)','Instantaneous modeled PFD')
for ver,c in [(1,col['M1']),(2,col['M2'])]:
 s=cycle[cycle.model==ver];ax.plot(s.age_h,s.pfd_instant,color=c,label=f'Model {ver}: '+('1oo1' if ver==1 else '1oo2'),linewidth=2.6);ax.axhline(s.pfd_average.iloc[0],color=c,linestyle='--',linewidth=1.2,alpha=.65)
ax.legend(loc='upper left');save(f,2,'proof_cycle','Actual paceval instantaneous probability curves and cycle-average levels for the same synthetic input.')
# Interval PFD from real scenario outcomes
f,ax=std('Increasing proof-test interval and modeled demand failure','Proof-test interval (h)','PFD average')
for v,c in [(1,col['M1']),(2,col['M2'])]:
 s=d[d.model==v].iloc[::40];ax.scatter(s.interval_h,s.pfd_average,color=c,s=8,alpha=.24,label=f'Model {v}')
ax.legend();save(f,3,'interval_vs_pfd','Recorded synthetic scenario points showing the variability of modeled PFD with proof-test interval.')
# Surfaces (two model versions)
for ver,index in [(1,4),(2,5)]:
 s=surf[surf.model==ver];x=np.sort(s.interval_h.unique());y=np.sort(s.proof_coverage.unique());mat=s.pivot(index='proof_coverage',columns='interval_h',values='pfd_average').loc[y,x].values
 f,ax=std(f'Model {ver}: PFD by proof-test interval and coverage','Proof-test interval (h)','Proof-test coverage')
 hm=ax.imshow(mat,origin='lower',aspect='auto',extent=[x[0],x[-1],y[0],y[-1]],cmap='viridis');f.colorbar(hm,ax=ax,label='Average modeled PFD')
 save(f,index,f'pfd_surface_model_{ver}',f'paceval two-parameter PFD surface for model {ver}; parameters not shown are held fixed at one synthetic reference case.')
# Actual screening decisions
f,ax=std('Hypothetical screening-status distribution','Research model','Model cases')
status=['SCREEN_PASS','SCREEN_REVIEW','SCREEN_REJECT'];colors=[col['green'],'#E2B14C','#D96552'];mat=np.array([[sum((d.model==v)&(d.status==st)) for st in status] for v in [1,2]])
bottom=np.zeros(2);xx=np.arange(2)
for j,st in enumerate(status):ax.bar(xx,mat[:,j],bottom=bottom,label=st.replace('SCREEN_',''),color=colors[j]);bottom+=mat[:,j]
ax.set_xticks(xx,['M1 · 1oo1','M2 · 1oo2']);ax.legend();save(f,6,'screening_status','Counts from hypothetical project-level screening rules, not SIL approval or operational permissions.')
# PFD distribution
f,ax=std('Modeled average probability of failure','PFD average','Model cases')
for v,c in [(1,col['M1']),(2,col['M2'])]:ax.hist(d[d.model==v].pfd_average,bins=70,alpha=.66,label=f'Model {v}',color=c)
ax.set_yscale('log');ax.legend();save(f,7,'pfd_distribution','Distribution across two synthetic architecture and assumption models; log y-axis is for display only.')
# Analytic coverage sensitivities
f,ax=std('Sensitivity to proof-test coverage','Proof-test coverage','d(PFD average) / d(coverage)')
for v,c in [(1,col['M1']),(2,col['M2'])]:
 s=d[d.model==v].iloc[::60];ax.scatter(s.proof_coverage,s.coverage_sensitivity,s=8,alpha=.2,color=c,label=f'Model {v}')
ax.legend();save(f,8,'proof_coverage_sensitivity','Analytic paceval sensitivity of PFD to proof-test coverage, evaluated on the real synthetic scenario grid.')
f,ax=std('Sensitivity to the proof-test interval','Proof-test interval (h)','d(PFD average) / d(interval), h⁻¹')
for v,c in [(1,col['M1']),(2,col['M2'])]:
 s=d[d.model==v].iloc[::70];ax.scatter(s.interval_h,s.interval_sensitivity,s=8,alpha=.28,label=f'Model {v}',color=c)
ax.legend();save(f,9,'interval_sensitivity','paceval analytic interval sensitivity, independently checked against high-precision differentiation.')
# paired model version comparison
f,ax=std('Same inputs, two mathematical architecture models','M1: 1oo1 PFD average','M2: 1oo2 PFD average')
a=d[d.model==1].pfd_average.to_numpy()[::70];b=d[d.model==2].pfd_average.to_numpy()[::70];ax.scatter(a,b,s=12,alpha=.32,color=col['M1']);lim=max(a.max(),b.max());ax.plot([0,lim],[0,lim],ls='--',color='#697A86',label='Equal PFD');ax.legend()
save(f,10,'architecture_comparison','Paired model outputs for identical synthetic input rows; each model represents different architectural assumptions.')
# target margin
f,ax=std('Continuous target margins, not certified acceptances','Target margin: target − PFD','Model cases')
for v,c in [(1,col['M1']),(2,col['M2'])]:ax.hist(d[d.model==v].margin,bins=70,alpha=.65,color=c,label=f'Model {v}')
ax.axvline(0,color='#333',linewidth=1.2);ax.legend();save(f,11,'target_margin','Signed project-level screening margins from actual paceval expressions. Positive does not imply conformity to IEC 61511.')
# common cause vs M2 output: compare input beta values
raw=pd.read_csv(RES/'synthetic_input.csv',usecols=['beta']);s=d[d.model==2].iloc[::80];i=s.scenario.to_numpy();f,ax=std('Common-cause fraction in the 1oo2 screening model','Synthetic common-cause parameter β','Modeled PFD average')
ax.scatter(raw.beta.iloc[i].to_numpy(),s.pfd_average.to_numpy(),alpha=.27,s=13,color=col['M2']);save(f,12,'common_cause','Model 2 screening PFD as a function of the synthetic common-cause fraction, with other parameters varying.')
# monetized hypothetical loss proxy already computed paceval
f,ax=std('Hypothetical event-loss proxy','PFD average','PFD × per-demand loss units')
for v,c in [(1,col['M1']),(2,col['M2'])]:
 s=d[d.model==v].iloc[::70];ax.scatter(s.pfd_average,s.expected_loss_proxy,s=9,alpha=.28,color=c,label=f'Model {v}')
ax.legend();save(f,13,'loss_proxy','paceval-calculated expected-loss proxy using arbitrary synthetic consequence weights; no economic validation.')

import json
(OUT/'figure_manifest.json').write_text(json.dumps(figures,indent=2)+'\n')
print('FIGURES GENERATED:',len(figures),'from real recorded paceval calculation outputs')
