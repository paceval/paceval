#!/usr/bin/env python3
"""Scientific graphics generated exclusively from actual paceval CSV results."""
from pathlib import Path
import csv, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
with (ROOT/'results'/'screening.csv').open(newline='') as f: rows=list(csv.DictReader(f))
with (ROOT/'results'/'model_comparison.csv').open(newline='') as f: comp=list(csv.DictReader(f))
A=[x for x in rows if x['model']=='V1'];B=[x for x in rows if x['model']=='V2']
assert len(A)==len(B)>1000
BLUE='#146c83';GOLD='#d99a18';RED='#c2484c';INK='#233343'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':'#c6d0d6','figure.facecolor':'white','axes.facecolor':'white','axes.grid':True,'grid.alpha':.16})
def col(data,k):return np.array([float(x[k]) for x in data])
def save(fig,name):fig.tight_layout(pad=1.9);fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
# 1: actual pressure vs mass flow
fig,ax=plt.subplots(figsize=(9.0,5.0));ax.scatter(col(A,'Pabs_Pa')/1e5,col(A,'leak_kg_s')*3600,s=8,alpha=.20,c=BLUE,label='V1 empirical');ax.scatter(col(B,'Pabs_Pa')/1e5,col(B,'leak_kg_s')*3600,s=8,alpha=.20,c=GOLD,label='V2 orifice');ax.set(xlabel='Absolute upstream pressure (bar)',ylabel='Leak mass (kg/h)',title='Pressure-dependent leakage across synthetic operating points');ax.legend();save(fig,'fig01_leak_pressure')
# 2: specific compressor work
fig,ax=plt.subplots(figsize=(9.0,5.0));ax.scatter(col(A,'Pabs_Pa')/1e5,col(A,'work_J_kg')/1000,s=9,alpha=.30,color=BLUE);ax.set(xlabel='Absolute upstream pressure (bar)',ylabel='Modeled compression work (kJ/kg)',title='Specific compression work and upstream pressure');save(fig,'fig02_specific_work')
# 3: modeled leak fraction and downstream constraints
fig,ax=plt.subplots(figsize=(9.0,5.0));ok=col(B,'composite_guard')>.5;ax.scatter(col(B,'Pabs_Pa')[~ok]/1e5,col(B,'leak_fraction')[~ok]*100,s=10,alpha=.30,color=RED,label='One or more guards failed');ax.scatter(col(B,'Pabs_Pa')[ok]/1e5,col(B,'leak_fraction')[ok]*100,s=10,alpha=.27,color=BLUE,label='All guards passed');ax.set(xlabel='Absolute upstream pressure (bar)',ylabel='Leak mass share (%)',title='Illustrative feasibility screening with multiple constraints');ax.legend();save(fig,'fig03_operating_feasibility')
#4: pressure and leak-cost relation, synthetic
fig,ax=plt.subplots(figsize=(9.0,5.0));ax.scatter(col(A,'leak_fraction')*100,col(A,'leak_cost_USD'),s=8,alpha=.25,color=BLUE,label='V1');ax.scatter(col(B,'leak_fraction')*100,col(B,'leak_cost_USD'),s=8,alpha=.22,color=GOLD,label='V2');ax.set(xlabel='Modeled leakage share of production (%)',ylabel='Illustrative annual leakage electricity expenditure (USD)',title='Energy-accounting consequence of the leakage models');ax.legend();save(fig,'fig04_leak_fraction_cost')
#5: categories of synthetic scenarios
from collections import Counter
counts={v:Counter(x['scenario'] for x in d if float(x['composite_guard'])>.5) for v,d in [('V1',A),('V2',B)]}
groups=sorted(set(x['scenario'] for x in A));x=np.arange(len(groups));fig,ax=plt.subplots(figsize=(9,5));ax.bar(x-.18,[counts['V1'][g] for g in groups],width=.36,color=BLUE,label='V1');ax.bar(x+.18,[counts['V2'][g] for g in groups],width=.36,color=GOLD,label='V2');ax.set_xticks(x,groups,rotation=16);ax.set(ylabel='Scenarios meeting all modeled limits',title='Accepted cases by operating scenario');ax.legend();save(fig,'fig05_feasible_cases')
#6 version model difference
fig,ax=plt.subplots(figsize=(9,5));ax.scatter(col(comp,'Pabs_Pa')/1e5,col(comp,'delta_leak_kg_s')*3600,s=9,alpha=.32,color=BLUE);ax.axhline(0,color=INK,lw=.8);ax.set(xlabel='Absolute upstream pressure (bar)',ylabel='V2 − V1 leak mass (kg/h)',title='Difference between physically distinct leak model versions');save(fig,'fig06_model_difference')
#7 compressor power versus demanded mass flow
fig,ax=plt.subplots(figsize=(9,5));ax.scatter(col(A,'required_kg_s'),col(A,'power_kW'),s=9,alpha=.25,color=BLUE,label='V1');ax.scatter(col(B,'required_kg_s'),col(B,'power_kW'),s=9,alpha=.22,color=GOLD,label='V2');ax.set(xlabel='Compressor flow requirement (kg/s)',ylabel='Modeled electric input (kW)',title='Coupled mass balance and compression model');ax.legend();save(fig,'fig07_flow_compressor_power')
#8 3d actual scatter
fig=plt.figure(figsize=(9,5.8));ax=fig.add_subplot(projection='3d');idx=np.linspace(0,len(B)-1,900).astype(int);XX=col(B,'Pabs_Pa')[idx]/1e5;YY=col(B,'area_mm2')[idx];ZZ=col(B,'leak_kg_s')[idx]*3600;sc=ax.scatter(XX,YY,ZZ,c=ZZ,cmap='viridis',s=9,alpha=.65);ax.set_xlabel('Pabs (bar)',labelpad=7);ax.set_ylabel('Effective area (mm²)',labelpad=7);ax.set_zlabel('Leak mass (kg/h)',labelpad=6);ax.set_title('3D distribution of actual V2 paceval evaluations',pad=15);ax.view_init(22,-59);fig.colorbar(sc,ax=ax,pad=.10,shrink=.68,label='Leak mass (kg/h)');save(fig,'fig08_3d_leak_operating_space')
# 9 percentage relative difference, no algorithmic performance
fig,ax=plt.subplots(figsize=(9,5));v1=col(comp,'leak_V1_kg_s');relative=100*(col(comp,'leak_V2_kg_s')-v1)/v1;ax.scatter(col(comp,'Pabs_Pa')/1e5,relative,s=9,alpha=.3,color=BLUE);ax.axhline(0,color=INK,lw=.8);ax.set(xlabel='Absolute upstream pressure (bar)',ylabel='Orifice vs empirical model flow difference (%)',title='Model-form sensitivity, not numerical-engine accuracy');save(fig,'fig09_relative_model_difference')
print('Generated 9 scientifically grounded figures from',len(A),'paceval scenarios per model')
