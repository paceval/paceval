#!/usr/bin/env python3
"""Rebuild 11 publication figures from original paceval result CSV files.
Figure 01 describes architecture; figures 02-11 use recorded original paceval decisions/metrics.
"""
import argparse,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa

INK='#27343e';RUST='#c66b47';SAGE='#618477';GOLD='#d6a23e';PURPLE='#806d8e';CREAM='#faf7f1';COLORS=[RUST,SAGE,GOLD,PURPLE]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titleweight':'bold','axes.titlesize':14,'axes.labelcolor':INK,'axes.edgecolor':'#a7adb0','text.color':INK,'axes.grid':True,'grid.alpha':.16,'figure.facecolor':'white','savefig.facecolor':'white'})

def rows(path):
 with open(path,newline='') as f:return list(csv.DictReader(f))
def v(r,k):return float(r[k])
def save(root,name,fig):
 fig.savefig(root/'figures'/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.25)
 fig.savefig(root/'figures'/(name+'.pdf'),bbox_inches='tight',pad_inches=.22)
 plt.close(fig)

def pick(summary,setup=2,urgent=0,ver='v2'):
 return [r for r in summary if v(r,'setup_scale_h')==setup and int(r['urgent_due'])==urgent and r['model_version']==ver]

def produce(root):
 (root/'figures').mkdir(exist_ok=True)
 summary=rows(root/'results/scenario_summary.csv'); ops=rows(root/'examples/best_schedules.csv'); candidates=rows(root/'results/candidate_scores.csv')
 probes={}
 for row in rows(root/'results/graph_probe_values.csv'):probes.setdefault(row['scenario'],{})[row['graph_id']]=float(row['paceval_value'])
 # 01 - Architecture overview, conceptual (not a numeric result)
 fig,ax=plt.subplots(figsize=(11,5.2));ax.set(xlim=(0,12),ylim=(0,5));ax.axis('off');fig.patch.set_facecolor(CREAM);ax.set_facecolor(CREAM)
 boxes=[(.4,1.7,2.1,1.45,'Policy agent','Validated priorities'),(3.2,1.7,2.15,1.45,'C++ scheduler','Constraints + search'),(6.1,1.7,2.0,1.45,'paceval 4.25','Versioned score graphs'),(8.95,1.7,2.55,1.45,'C++ acceptance','Schedule + audit')]
 for i,(x,y,w,h,t,s) in enumerate(boxes):
  color=[SAGE,GOLD,RUST,PURPLE][i];ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.15',fc='white',ec=color,lw=2))
  ax.text(x+w/2,y+.90,t,ha='center',va='center',weight='bold',fontsize=11);ax.text(x+w/2,y+.4,s,ha='center',va='center',fontsize=9.4)
  if i<3:ax.add_patch(FancyArrowPatch((x+w+.2,y+.7),(boxes[i+1][0]-.3,y+.7),arrowstyle='-|>',mutation_scale=15,color=INK,lw=1.7))
 ax.text(6,4.3,'Agent intent → feasible plan → mathematical score → audited decision',ha='center',weight='bold',fontsize=14)
 ax.text(6,.55,'Research scope: deterministic fixture policies and exhaustive small-instance scheduling; no live LLM inference',ha='center',fontsize=10)
 save(root,'01_executed_decision_architecture',fig)
 # 02 - Gantt plot from winning actual scored schedule
 chosen='S2_regular_delivery_v2';use=sorted((r for r in ops if r['scenario']==chosen),key=lambda r:(int(r['machine']),v(r,'start_h')))
 fig,ax=plt.subplots(figsize=(11,6.5));
 for r in use:
  m=int(r['machine']);j=int(r['job']);ax.broken_barh([(v(r,'start_h'),v(r,'duration_h'))],(m-.35,.7),facecolors=COLORS[j],edgecolors='white',linewidth=1.5)
  ax.text((v(r,'start_h')+v(r,'end_h'))/2,m,'J'+str(j),ha='center',va='center',color='white' if j!=2 else INK,weight='bold',fontsize=10)
  if v(r,'setup_before_h')>0:ax.broken_barh([(v(r,'start_h')-v(r,'setup_before_h'),v(r,'setup_before_h'))],(m-.35,.7),facecolors='#dcdcdc',alpha=.7,hatch='///',edgecolors='#838383')
 ax.set_yticks([0,1,2],['Machine 0','Machine 1','Machine 2']);ax.set_xlabel('Schedule time (hours)');ax.set_title('Winning production schedule – delivery policy, v2, 2-h setup')
 ax.invert_yaxis();ax.grid(axis='x');ax.set_xlim(0,25);save(root,'02_feasible_schedule_gantt',fig)
 # 03 - score grouped by v1/v2 and policy
 subset=pick(summary);labs=[r['policy'] for r in subset if r['model_version']=='v2'];labs=list(dict.fromkeys(labs));order=['throughput','delivery','changeover','energy']
 fig,ax=plt.subplots(figsize=(10.4,6));x=np.arange(len(order));
 for k,version in enumerate(('v1','v2')):
  values=[v(next(r for r in summary if r['scenario']==f'S2_regular_{policy}_{version}'),'objective_score') for policy in order]
  ax.bar(x+(k-.5)*.34,values,width=.34,label='Score '+version,color=[SAGE,RUST][k])
 ax.set_xticks(x,order);ax.set_ylabel('Normalized planning objective');ax.set_title('Controlled scoring formula versions across agent priorities');ax.legend(frameon=False);save(root,'03_agent_version_score_comparison',fig)
 # 04 - all enumerated candidate scores, each point original paceval output
 fig,ax=plt.subplots(figsize=(10.7,6.6));m=np.array([v(r,'makespan_h') for r in candidates]);t=np.array([v(r,'weighted_tardiness_h') for r in candidates]);s=np.array([v(r,'objective_score') for r in candidates]);sc=ax.scatter(m,t,c=s,cmap='cividis',s=14,alpha=.55,edgecolors='none')
 fig.colorbar(sc,ax=ax,label='paceval composite objective v2');ax.set_xlabel('Makespan (h)');ax.set_ylabel('Priority-weighted tardiness (h)');ax.set_title('All feasible machine-order candidates: delivery-policy scoring');save(root,'04_combinatorial_candidate_tradeoffs',fig)
 # 05 - selected model-change response
 fig,ax=plt.subplots(figsize=(10.5,6));bar=[r for r in summary if r['urgent_due']=='0' and v(r,'setup_scale_h')==2];order=['throughput','delivery','changeover','energy'];xs=np.arange(4);diff=[v(next(r for r in bar if r['policy']==p and r['model_version']=='v2'),'objective_score')-v(next(r for r in bar if r['policy']==p and r['model_version']=='v1'),'objective_score') for p in order]
 ax.bar(xs,diff,color=COLORS);ax.set_xticks(xs,order);ax.set_ylabel('v2 score – v1 score');ax.set_title('Controlled formula revision: convex lateness and idle penalties');save(root,'05_version_revision_effect',fig)
 # 06 - true mathematical 3D parameter surface from measured paceval scores
 sweep=rows(root/'results/policy_weight_surface.csv')
 x=np.array([v(r,'makespan_weight') for r in sweep]);y=np.array([v(r,'tardiness_weight') for r in sweep]);z=np.array([v(r,'score_v2') for r in sweep])
 fig=plt.figure(figsize=(11,7));ax=fig.add_subplot(111,projection='3d')
 ax.plot_trisurf(x,y,z,cmap='viridis',alpha=.94,linewidth=.12,antialiased=True)
 ax.set_xlabel('Makespan priority weight',labelpad=11);ax.set_ylabel('Delivery priority weight',labelpad=10);ax.set_zlabel('paceval v2 objective',labelpad=9)
 ax.set_title('3D score response to controlled agent-priority changes',pad=22);ax.view_init(28,230);save(root,'06_paceval_planning_score_surface_3d',fig)
 # 07 - energy and tardiness policy contrasts (winners, all scenarios)
 fig,ax=plt.subplots(figsize=(10.5,6.5))
 for i,p in enumerate(('throughput','delivery','changeover','energy')):
  selection=[r for r in summary if r['policy']==p and r['model_version']=='v2'];ax.scatter([v(r,'energy_kwh') for r in selection],[v(r,'weighted_tardiness_h') for r in selection],color=COLORS[i],label=p,s=70,alpha=.85,edgecolors='white')
 ax.set_xlabel('Synthetic processing + setup electricity (kWh)');ax.set_ylabel('Priority-weighted tardiness (h)');ax.set_title('Policy trade-offs in selected feasible schedules');ax.legend(frameon=False);save(root,'07_energy_delivery_tradeoff',fig)
 # 08 - signed constraints, heatmap: explicitly synthetic budget and due/horizon
 sample=pick(summary,setup=2,urgent=1,ver='v2');sample=sorted(sample,key=lambda r:['throughput','delivery','changeover','energy'].index(r['policy']))
 metrics=['minimum_due_margin_h','horizon_margin_h','budget_margin'];A=np.array([[v(r,k) for k in metrics] for r in sample]);
 # different units deliberately separate as normalized relative summaries for plotting
 An=A/np.array([8,34,2]);fig,ax=plt.subplots(figsize=(10.4,5.7));im=ax.imshow(An,cmap='PiYG',vmin=-1,vmax=1,aspect='auto');ax.set_yticks(range(4),[r['policy'] for r in sample]);ax.set_xticks(range(3),['Due-date slack / 8 h','Horizon margin / 34 h','Score-budget margin / 2']);
 for i in range(4):
  for j in range(3):ax.text(j,i,f'{A[i,j]:+.2f}',ha='center',va='center',fontsize=10,weight='bold')
 fig.colorbar(im,ax=ax,label='Normalized signed margin (sign indicates pass/fail)');ax.set_title('Independent guard quantities computed by paceval – rush case');save(root,'08_policy_constraint_margins',fig)
 # 09 - analytic derivatives: actual paceval graph values across all winners
 sample=sorted(pick(summary,setup=2,urgent=0,ver='v2'),key=lambda r:['throughput','delivery','changeover','energy'].index(r['policy']))
 ids=['d_objective_d_wmakespan_v1','d_objective_d_wtardiness_v2','d_objective_d_wsetup_v1','d_objective_d_wenergy_v2'];A=np.array([[probes[r['scenario']][g] for g in ids] for r in sample]);
 fig,ax=plt.subplots(figsize=(10.5,5.8));im=ax.imshow(A,cmap='YlOrBr',aspect='auto');ax.set_yticks(range(4),[r['policy'] for r in sample]);ax.set_xticks(range(4),['Makespan weight','Lateness weight','Setup weight','Energy weight']);
 for i in range(4):
  for j in range(4):ax.text(j,i,f'{A[i,j]:.2f}',ha='center',va='center',weight='bold')
 fig.colorbar(im,ax=ax,label='Analytic objective sensitivity (normalized)');ax.set_title('paceval graph sensitivities to agent-defined priorities');save(root,'09_analytical_policy_sensitivities',fig)
 # 10 - composite cost decomposition of v2 (actual graph outputs)
 ids=['makespan_component','tardiness_component','changeover_component','energy_component','risk_tardiness_component_v2','idle_component_v2','worst_delay_component_v2']
 fig,ax=plt.subplots(figsize=(11,6.2));bars=np.arange(len(sample));bottom=np.zeros(4)
 for k,id in enumerate(ids):
  values=np.array([probes[r['scenario']][id] for r in sample]);ax.bar(bars,values,bottom=bottom,label=id.replace('_',' '),color=[SAGE,RUST,GOLD,PURPLE,'#b58669','#a4ada7','#596875'][k]);bottom+=values
 ax.set_xticks(bars,[r['policy'] for r in sample]);ax.set_ylabel('Composite objective score');ax.set_title('End-to-end paceval composition of the winning planning cost');ax.legend(frameon=False,fontsize=8,ncol=2,loc='upper right');save(root,'10_full_cost_decomposition',fig)
 # 11 - response to controlled setup changes, v2 and baseline due dates
 fig,ax=plt.subplots(figsize=(10.4,6));order=['throughput','delivery','changeover','energy'];xs=np.arange(4)
 for i,sc in enumerate((0,2)):
  vals=[v(next(r for r in summary if r['scenario']==f'S{sc}_regular_{p}_v2'),'makespan_h') for p in order]
  ax.bar(xs+(i-.5)*.36,vals,width=.36,color=[SAGE,RUST][i],label=f'{sc} h per family changeover')
 ax.set_xticks(xs,order);ax.set_ylabel('Selected schedule makespan (h)');ax.set_title('Controlled sequence-dependent setup scenarios');ax.legend(frameon=False);save(root,'11_changeover_scenario_impact',fig)
 print('PASS figures produced=11 (concept architecture + 10 actual computed result visualizations)')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=Path(__file__).resolve().parents[1],type=Path);produce(ap.parse_args().root)
