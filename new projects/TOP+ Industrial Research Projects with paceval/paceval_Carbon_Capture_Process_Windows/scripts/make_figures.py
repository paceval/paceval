#!/usr/bin/env python3
"""Publication figures derived exclusively from actual paceval CSV results."""
from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'results/screening.csv');c=pd.read_csv(ROOT/'results/model_comparison.csv')
SCENARIOS=['BASELINE','LOW_PCO2','HOT_STRIPPER','HIGH_CAPTURE'];MODELS=['V1','V2']
def save(i,slug):
 plt.tight_layout(pad=2.0)
 plt.savefig(FIG/f'fig{i:02d}_{slug}.png',dpi=180,bbox_inches='tight')
 plt.savefig(FIG/f'fig{i:02d}_{slug}.pdf',bbox_inches='tight')
 plt.close()

def setup(title,xlabel,ylabel):
 plt.figure(figsize=(9.2,5.6));plt.title(title,fontsize=14,pad=14);plt.xlabel(xlabel);plt.ylabel(ylabel);plt.grid(alpha=.18)

setup('CO2 recovery across four synthetic operating scenarios','Operating scenario','CO2 recovery fraction')
positions=np.arange(len(SCENARIOS));width=.34
for mi,model in enumerate(MODELS):
 m=d[d.model==model].groupby('scenario')['recovery'].mean().reindex(SCENARIOS)
 plt.bar(positions+(mi-.5)*width,m.values,width,label=model)
plt.xticks(positions,[s.replace('_',' ').title() for s in SCENARIOS]);plt.ylim(0,1.07);plt.legend();save(1,'recovery_by_scenario')

setup('Capture-energy trade-off for the two process versions','CO2 capture fraction','Specific reboiler heat (GJ/tCO2)')
for model in MODELS:
 s=d[d.model==model].iloc[::4];plt.scatter(s.recovery,s.specific_duty_GJ_tCO2,s=13,alpha=.28,label=model)
plt.axvline(.78,ls=':',color='gray',label='Illustrative 0.78 recovery floor');plt.legend();save(2,'energy_recovery_scatter')

setup('Decomposition of modelled reboiler demand','Operating scenario','Mean thermal power (kW)')
w=.33;p=np.arange(len(SCENARIOS))
for mi,model in enumerate(MODELS):
 s=d[d.model==model].groupby('scenario')[['sensible_kW','desorption_kW','vapor_kW']].mean().reindex(SCENARIOS)
 bottom=np.zeros(len(s));offset=p+(mi-.5)*w
 for k,col in enumerate(s.columns):
  plt.bar(offset,s[col],w,bottom=bottom,label=f'{model} {col.replace("_kW","")}' if mi==0 else None,alpha=.85)
  bottom+=s[col].to_numpy()
plt.xticks(p,[x.replace('_',' ').title() for x in SCENARIOS]);plt.legend(ncol=3,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.12));save(3,'reboiler_components')

setup('Solvent loading after absorption versus CO2 recovery','CO2 recovery fraction','Rich solvent loading (mol CO2/mol amine)')
for model in MODELS:
 s=d[d.model==model].iloc[::4];plt.scatter(s.recovery,s.rich_loading,s=11,alpha=.30,label=model)
plt.legend();save(4,'rich_loading_recovery')

setup('Feasible candidate fractions by operating scenario','Operating scenario','Candidates meeting all four mathematical limits (%)')
for mi,model in enumerate(MODELS):
 y=d[d.model==model].groupby('scenario').composite_guard.mean().reindex(SCENARIOS)*100
 plt.bar(p+(mi-.5)*w,y.values,w,label=model)
plt.xticks(p,[x.replace('_',' ').title() for x in SCENARIOS]);plt.ylim(0,105);plt.legend();save(5,'feasible_by_scenario')

setup('Change in specific regeneration demand between model versions','V1 specific duty (GJ/tCO2)','V2 specific duty (GJ/tCO2)')
for s in SCENARIOS:
 x=c[c.scenario==s].iloc[::4];plt.scatter(x.duty_V1_GJ_t,x.duty_V2_GJ_t,s=14,alpha=.32,label=s.replace('_',' ').title())
mi=min(c.duty_V1_GJ_t.min(),c.duty_V2_GJ_t.min());ma=max(c.duty_V1_GJ_t.max(),c.duty_V2_GJ_t.max())
plt.plot([mi,ma],[mi,ma],linestyle=':',c='gray',label='Equal duty');plt.legend(fontsize=8);save(6,'versioned_specific_duty')

setup('Sensitivity of CO2 capture to the transfer coefficient','Absorber kLa (1/s)','Local sensitivity d(capture)/d(kLa) (mol)')
for model in MODELS:
 s=d[d.model==model].iloc[::3];plt.scatter(s.kLa_per_s,s.d_capture_d_kLa,s=13,alpha=.32,label=model)
plt.legend();save(7,'transfer_sensitivity')

setup('Product-side off-gas CO2 concentration proxy','CO2 capture fraction','Treated-gas CO2 mole fraction')
for model in MODELS:
 s=d[d.model==model].iloc[::3];plt.scatter(s.recovery,s.offgas_CO2_fraction,s=11,alpha=.35,label=model)
plt.legend();save(8,'offgas_co2')

fig=plt.figure(figsize=(9.3,6.8));ax=fig.add_subplot(projection='3d')
s=d[(d.model=='V2')].iloc[::5]
p3=ax.scatter(s.solvent_mol_s,s.kLa_per_s,s.recovery,c=s.specific_duty_GJ_tCO2,cmap='viridis',s=17,alpha=.72)
ax.set_title('Synthetic operating-point landscape from paceval V2',fontsize=14,pad=18);ax.set_xlabel('Amine flow (mol/s)',labelpad=9);ax.set_ylabel('kLa (1/s)',labelpad=9);ax.set_zlabel('CO2 recovery',labelpad=8);fig.colorbar(p3,ax=ax,shrink=.60,pad=.11,label='Specific duty (GJ/tCO2)');save(9,'three_dimensional_process_window')

setup('How mathematical operating limits exclude candidates','Constraint','Cases with negative signed margin (%)')
for mi,model in enumerate(MODELS):
 x=d[d.model==model];y=[100*(x[key]<-1e-12).mean() for key in ['capture_margin','duty_margin','loading_margin','temp_margin']]
 plt.bar(np.arange(4)+(mi-.5)*w,y,w,label=model)
plt.xticks(np.arange(4),['Capture target','Energy duty','Rich loading','Stripper temperature']);plt.ylim(0,max(15,plt.ylim()[1]));plt.legend();save(10,'constraint_limit_contributors')

print('FIGURES PASS: 10 paired PNG and vector PDF charts from real paceval results')
