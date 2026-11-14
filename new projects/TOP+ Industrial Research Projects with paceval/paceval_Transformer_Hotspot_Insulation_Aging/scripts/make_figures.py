#!/usr/bin/env python3
"""Produce publication figures from actual original-paceval output CSVs only."""
from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';F=ROOT/'figures';F.mkdir(exist_ok=True)
T=pd.read_csv(R/'hotspot_timeseries.csv');S=pd.read_csv(R/'asset_summary.csv');C=pd.read_csv(R/'model_comparison.csv')
plt.rcParams.update({'figure.figsize':(9,5.1),'figure.dpi':145,'font.size':10,'axes.labelsize':10,'axes.titlesize':13,'legend.fontsize':9,'savefig.bbox':'tight'})
def save(name):
 plt.grid(True,alpha=.18);plt.tight_layout();plt.savefig(F/(name+'.png'),dpi=205);plt.savefig(F/(name+'.pdf'));plt.close()
# 1. Hot-spot profiles of one asset under three independently generated scenarios.
plt.figure()
for scen in ['baseline','heatwave','overload']:
 d=T[(T.asset_id=='TR000')&(T.model=='V2')&(T.scenario==scen)];plt.plot(d.hour/24,d.hotspot_C,label=scen)
plt.axhline(110,ls='--',lw=1,label='TR000 illustrative limit');plt.xlabel('Simulation day');plt.ylabel('Winding hot-spot (°C)');plt.title('Synthetic duty cycles and thermal response');plt.legend();save('fig01_hotspot_scenarios')
# 2. Oil and winding lag variants at overload transition.
plt.figure();d=T[(T.asset_id=='TR014')&(T.scenario=='overload')&(T.hour<96)]
for mod in ['V1','V2']:
 z=d[d.model==mod];plt.plot(z.hour/24,z.hotspot_C,label=f'{mod}: winding hot-spot')
plt.plot(d[d.model=='V2'].hour/24,d[d.model=='V2'].top_oil_C,label='V2: top oil',ls=':')
plt.xlabel('Simulation day');plt.ylabel('Temperature (°C)');plt.title('Transient thermal memory across model versions');plt.legend();save('fig02_thermal_memory')
# 3 aging relation from computed graph values
plt.figure();d=T[(T.model=='V2')].iloc[::53];plt.scatter(d.hotspot_C,d.aging_factor,s=9,alpha=.55)
plt.xlabel('Hot-spot temperature (°C)');plt.ylabel('Relative aging acceleration FAA');plt.title('Nonlinear insulation-aging proxy in executed data');save('fig03_aging_vs_temperature')
# 4 cumulative aging TR000
plt.figure();d=T[(T.asset_id=='TR000')];
for scen in ['baseline','heatwave','overload']:
 for ver in ['V1','V2']:
  z=d[(d.model==ver)&(d.scenario==scen)];plt.plot(z.hour/24,z.cumulative_aging_h,label=f'{scen} / {ver}',ls='-' if ver=='V1' else '--')
plt.xlabel('Simulation day');plt.ylabel('Equivalent reference aging hours');plt.title('Cumulative relative aging under contrasting duty cycles');plt.legend(ncol=2);save('fig04_cumulative_aging')
# 5 heatmap
plt.figure(figsize=(9,5.5));d=T[(T.model=='V2')&(T.scenario=='heatwave')&(T.hour<72)].copy();d['asset_index']=d.asset_id.str[2:].astype(int)
a=d.pivot(index='asset_index',columns='hour',values='hotspot_C').sort_index();plt.imshow(a.values,aspect='auto',origin='lower',extent=[0,72,0,48]);plt.colorbar(label='Hot-spot (°C)');plt.xlabel('Hour');plt.ylabel('Synthetic asset number');plt.title('Three-day hot-spot field across the transformer fleet');save('fig05_fleet_heatmap')
# 6 ratio variants across scenarios
plt.figure();data=[C[C.scenario==scen].ratio_V2_to_V1.values for scen in ['baseline','heatwave','overload']];plt.boxplot(data,tick_labels=['Baseline','Heatwave','Overload'],showmeans=True)
plt.axhline(1,ls='--',lw=1);plt.ylabel('Equivalent aging ratio V2 / V1');plt.title('Effect of winding thermal lag on cumulative aging');save('fig06_model_aging_ratio')
# 7 counts
plt.figure();a=S.groupby(['scenario','model'])['all_intervals_within_illustrative_limits'].sum().unstack().reindex(['baseline','heatwave','overload']);x=np.arange(len(a));w=.35
plt.bar(x-w/2,a.V1,width=w,label='V1');plt.bar(x+w/2,a.V2,width=w,label='V2');plt.xticks(x,['Baseline','Heatwave','Overload']);plt.ylabel('48-asset series without a threshold exception');plt.title('Illustrative screening outcomes, not asset certification');plt.legend();save('fig07_screening_counts')
# 8 aging vs peak hotspot
plt.figure();d=S[S.model=='V2'];
for scen,group in d.groupby('scenario'):plt.scatter(group.peak_hotspot_C,group.equivalent_aging_h,label=scen,s=21,alpha=.75)
plt.xlabel('Peak hot-spot (°C)');plt.ylabel('14-day equivalent aging (h)');plt.title('Fleet-level consequence of thermal peak differences');plt.legend();save('fig08_peak_vs_age')
# 9 analytic graph sensitivity vs load
plt.figure();d=T[(T.scenario=='baseline')&(T.hour>18)&(T.hour<150)&(T.asset_id.isin(['TR000','TR014','TR032']))]
for ver,z in d.groupby('model'):plt.scatter(z.load_ratio,z.dHs_dK_K,label=ver,s=10,alpha=.55)
plt.xlabel('Current loading K = I / I-rated');plt.ylabel('One-step d(hot-spot)/dK (K)');plt.title('Independently derived paceval sensitivity graph');plt.legend();save('fig09_sensitivity')
# 10 direct 3D point cloud (no interpolated 'surface')
d=T[(T.scenario=='heatwave')&(T.model=='V2')].iloc[::17]
fig=plt.figure(figsize=(9,6.2));ax=fig.add_subplot(111,projection='3d');sc=ax.scatter(d.load_ratio,d.ambient_C,d.hotspot_C,c=d.hotspot_C,s=7,alpha=.7)
ax.set_xlabel('Load ratio K');ax.set_ylabel('Ambient (°C)');ax.set_zlabel('Hot-spot (°C)');ax.set_title('Actual evaluated input-output points, no FEM fit');fig.colorbar(sc,ax=ax,shrink=.65,label='Hot-spot (°C)');fig.tight_layout();fig.savefig(F/'fig10_3d_operating_cloud.png',dpi=205,bbox_inches='tight');fig.savefig(F/'fig10_3d_operating_cloud.pdf',bbox_inches='tight');plt.close(fig)
print('Generated 10 original paceval data visualizations (PNG + vector PDF)')
