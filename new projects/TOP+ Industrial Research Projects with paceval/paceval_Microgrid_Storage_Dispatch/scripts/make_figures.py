#!/usr/bin/env python3
"""Figures exclusively from documented original paceval output CSV records."""
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';D=ROOT/'figures';D.mkdir(exist_ok=True)
T=pd.read_csv(R/'dispatch_timeseries.csv',dtype={'schedule_id':str});S=pd.read_csv(R/'schedule_summary.csv',dtype={'schedule_id':str});C=pd.read_csv(R/'model_comparison.csv',dtype={'schedule_id':str})
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'axes.labelsize':10,'savefig.dpi':180,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
navy='#133a5b';teal='#11858d';amber='#e7a645';red='#c25362';violet='#7865b7'
def save(name,fig):
 fig.tight_layout(pad=1.6);fig.savefig(D/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(D/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def show(scenario='grid_sunny',sid='0001',version='V2'):return T[(T.scenario==scenario)&(T.schedule_id==sid)&(T.model==version)].sort_values('hour')
# 1: power schedule
fig,ax=plt.subplots(figsize=(8.8,3.85));a=show();x=a.hour
for col,label,color in [('load_kW','Demand',navy),('pv_kW','PV available',amber),('import_kW','Utility import',teal),('gen_kW','Local generator',red)]:ax.plot(x,a[col],marker='o',ms=2.4,lw=1.7,color=color,label=label)
ax.set(title='Grid-connected synthetic dispatch: electrical power flows',xlabel='Hour',ylabel='Power (kW)',xlim=(0,23));ax.legend(ncol=2,frameon=False);ax.grid(alpha=.18);save('fig01_power_flows',fig)
# 2: battery energy chain across models
fig,ax=plt.subplots(figsize=(8.8,3.85))
for v,col in [('V1',navy),('V2',red)]:
 a=show(version=v);ax.plot(a.hour,a.E_next_kWh,color=col,lw=2,marker='o',markersize=2.6,label=v)
ax.axhline(145,color=amber,ls='--',label='Reserve floor 145 kWh');ax.axhline(205,color=teal,ls=':',label='Terminal goal 205 kWh');ax.set(title='Battery energy propagation with two real paceval model versions',xlabel='Hour',ylabel='Stored energy after interval (kWh)');ax.legend(frameon=False,ncol=2);ax.grid(alpha=.18);save('fig02_battery_energy',fig)
# 3 island resources
fig,ax=plt.subplots(figsize=(8.8,3.85));a=show('island_outage','0001');x=a.hour
for col,label,color in [('load_kW','Total load',navy),('pv_kW','PV resource',amber),('gen_kW','Dispatchable generation',red),('discharge_kW','BESS discharge',teal)]:ax.plot(x,a[col],lw=1.8,color=color,label=label)
ax.fill_between(x,0,a['shed_kW'].to_numpy(),color=red,alpha=.12,label='Noncritical shed');ax.set(title='Islanded 24-hour dispatch with zero grid exchange',xlabel='Hour',ylabel='Power (kW)',xlim=(0,23));ax.legend(ncol=2,frameon=False);ax.grid(alpha=.18);save('fig03_island_operation',fig)
# 4 feasibility counts per model, scenario
fig,ax=plt.subplots(figsize=(8.8,3.85));tab=S.groupby(['scenario','model']).full_schedule_feasible.sum().unstack().loc[['grid_sunny','grid_cloudy','island_outage']];x=np.arange(3);ax.bar(x-.18,tab.V1,width=.36,label='V1',color=navy);ax.bar(x+.18,tab.V2,width=.36,label='V2',color=teal);ax.set_xticks(x,['Sunny grid','Cloudy grid','Islanded']);ax.set_ylim(0,360);ax.set(title='Complete 24-hour feasibility by synthetic scenario',ylabel='Feasible schedules out of 360');ax.legend(frameon=False);ax.grid(axis='y',alpha=.15);save('fig04_feasible_schedules',fig)
# 5 costs by version and scenario
fig,ax=plt.subplots(figsize=(8.8,3.85));names=['grid_sunny','grid_cloudy','island_outage'];positions=[1,2,3,5,6,7];groups=[S[(S.scenario==s)&(S.model==v)].total_cost_USD.to_numpy() for v in ['V1','V2'] for s in names];bp=ax.boxplot(groups,positions=positions,patch_artist=True,widths=.65,showfliers=False);[b.set_facecolor(navy if k<3 else teal) for k,b in enumerate(bp['boxes'])];ax.set_xticks([1,2,3,5,6,7],['Sunny','Cloudy','Island','Sunny','Cloudy','Island']);ax.axvline(4,color='#cccccc');ax.set(title='Operating-cost distribution by model and dispatch scenario',ylabel='Modeled 24-hour cost (USD)');ax.text(2,ax.get_ylim()[1]*.95,'V1',ha='center',color=navy);ax.text(6,ax.get_ylim()[1]*.95,'V2',ha='center',color=teal);ax.grid(axis='y',alpha=.18);save('fig05_cost_distributions',fig)
# 6 cost feasibility frontier scatter
fig,ax=plt.subplots(figsize=(8.8,3.85));q=S[(S.scenario=='grid_cloudy')&(S.model=='V2')]
for f,col,name in [(0,red,'Violates ≥1 constraint'),(1,teal,'Passes full horizon')]:b=q[q.full_schedule_feasible==f];ax.scatter(b.final_energy_kWh,b.total_cost_USD,s=13,alpha=.58,c=col,label=name)
ax.set(title='Cloudy-grid candidate set: 24-hour cost versus terminal stored energy',xlabel='Final stored energy (kWh)',ylabel='Modeled operating cost (USD)');ax.legend(frameon=False);ax.grid(alpha=.15);save('fig06_cost_vs_energy',fig)
# 7 characteristic heatmap SOC by candidate/time for island
q=T[(T.scenario=='island_outage')&(T.model=='V2')&(T.schedule_id.astype(int)%6==0)];arr=q.pivot(index='schedule_id',columns='hour',values='E_next_kWh').to_numpy();fig,ax=plt.subplots(figsize=(8.8,4.15));im=ax.imshow(arr,aspect='auto',origin='lower',cmap='viridis',extent=(0,23,0,len(arr)),vmin=100,vmax=620);ax.set(title='Islanded schedule ensemble: battery energy trajectories',xlabel='Hour',ylabel='Synthetic candidate index (every sixth schedule)');fig.colorbar(im,ax=ax,label='Stored energy (kWh)');save('fig07_energy_heatmap',fig)
# 8 sensitivity of graph-evaluated efficiencies and energy gradients
fig,ax=plt.subplots(figsize=(8.8,3.85));a=show('grid_sunny','0301','V2');ax.plot(a.hour,a.charge_eff,label='SOC-dependent charge efficiency',color=teal,marker='o',ms=2.2);ax.plot(a.hour,a.discharge_eff,label='SOC-dependent discharge efficiency',color=amber,marker='o',ms=2.2);ax.set(title='Graph-evaluated battery efficiency depends on stored energy',xlabel='Hour',ylabel='Model efficiency',ylim=(.75,.99));ax.legend(frameon=False);ax.grid(alpha=.18);save('fig08_efficiency_variation',fig)
# 9 comparison model differences / plot
fig,ax=plt.subplots(figsize=(8.8,3.85));cs=['grid_sunny','grid_cloudy','island_outage'];cols=[teal,amber,violet];
for s,col in zip(cs,cols):
 q=C[C.scenario==s];ax.scatter(q.delta_final_energy_kWh,q.delta_cost_USD,s=10,alpha=.45,label=s.replace('_',' '),color=col)
ax.set(title='Two formula versions: 24-hour energy versus cost differences',xlabel='V2 − V1: final stored energy (kWh)',ylabel='V2 − V1: modeled operating cost (USD)');ax.legend(frameon=False);ax.grid(alpha=.15);save('fig09_model_differences',fig)
# 10: 3d math output response surface from paceval results, no interpolated physics
from mpl_toolkits.mplot3d import Axes3D
z=S[(S.scenario=='grid_sunny')&(S.model=='V2')].sort_values('schedule_id').reset_index(drop=True);a=T[(T.scenario=='grid_sunny')&(T.model=='V2')&(T.hour==15)].sort_values('schedule_id')
fig=plt.figure(figsize=(8.8,5.2));ax=fig.add_subplot(111,projection='3d');ax.scatter(a.charge_kW.to_numpy(),z.final_energy_kWh.to_numpy(),z.total_cost_USD.to_numpy(),c=z.full_schedule_feasible.to_numpy(),cmap='coolwarm',s=10,alpha=.7);ax.set(xlabel='Hour-15 charge (kW)',ylabel='Terminal energy (kWh)',zlabel='24-hour cost (USD)',title='Three-dimensional landscape of evaluated schedule candidates');ax.view_init(elev=22,azim=-66);save('fig10_3d_schedule_landscape',fig)
print('CREATED',len(list(D.glob('fig??_*.png'))),'scientific PNG+vector-PDF figure pairs, sourced from original paceval CSV outputs')
