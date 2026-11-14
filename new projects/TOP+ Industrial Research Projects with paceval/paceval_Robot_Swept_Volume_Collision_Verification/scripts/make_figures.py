#!/usr/bin/env python3
"""Generate measured-in-this-run scientific illustrations from genuine paceval CSV and exact witness audit."""
from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
R=Path(__file__).resolve().parents[1]
O=R/'figures';O.mkdir(exist_ok=True)
a=pd.read_csv(R/'results/screening.csv');b=pd.read_csv(R/'results/model_comparison.csv');fine=pd.read_csv(R/'results/fine_clearance.csv');sample=pd.read_csv(R/'results/sampled_clearance.csv');cert=pd.read_csv(R/'results/exact_interval_certificates.csv');inp=pd.read_csv(R/'input/cases.csv')
colors={'V1':'#197f91','V2':'#e88d47'}
def save(num,name,ax=None):
 fig=plt.gcf();fig.tight_layout(pad=2);fig.savefig(O/f'fig{num:02d}_{name}.png',dpi=220,bbox_inches='tight');fig.savefig(O/f'fig{num:02d}_{name}.pdf',bbox_inches='tight');plt.close(fig)
def start(title,three=False):
 fig=plt.figure(figsize=(8.8,4.5),facecolor='white')
 ax=fig.add_subplot(111,projection='3d' if three else None);ax.set_title(title,fontsize=12,fontweight='bold',loc='left',pad=13)
 if not three:ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.18)
 return ax
# 1: coarse misses a narrow collision (only real evaluated values)
ax=start('A collision can hide between sampled waypoints')
d=fine[(fine.case_id=='T00000')&(fine.model=='V1')];s=sample[(sample.case_id=='T00000')&(sample.model=='V1')]
ax.plot(d.t,d.squared_margin_m2,c=colors['V1'],lw=2,label='paceval continuous-trajectory model, dense samples')
ax.scatter(s.t,s.squared_margin_m2,s=17,c='#e88d47',label='32-interval monitoring grid',zorder=3)
ax.axhline(0,c='#a73545',ls='--',lw=1);ax.axvline(.50390625,c='#a73545',lw=.8,ls=':');ax.set_xlim(.47,.53);ax.set_ylim(-.00010,.011);ax.set_xlabel('Normalized motion time u');ax.set_ylabel('Squared surface margin (m²)');ax.legend(loc='upper left',fontsize=7.5);save(1,'missed_narrow_overlap')
# 2: two model curves and robustness buffer
ax=start('The clearance-buffer version changes the collision interval')
for v in ['V1','V2']:
 d=fine[(fine.case_id=='T00003')&(fine.model==v)];ax.plot(d.t,d.surface_clearance_m,c=colors[v],lw=2.2,label=v+' signed clearance')
ax.axhline(0,c='#a73545',lw=1,ls='--');ax.set_xlabel('Normalized time u');ax.set_ylabel('Signed surface clearance (m)');ax.legend(fontsize=8);save(2,'buffer_changes_sign')
# 3: only novel actual missed collisions highlighted
ax=start('Sampled versus continuous minimum margins')
a1=a[a.model=='V1'];ax.scatter(a1.coarse_squared_margin_m2,a1.min_squared_margin_m2,s=8,alpha=.27,c=colors['V1'],label='Trajectories')
miss=a1[(a1.coarse_squared_margin_m2>0)&(a1.min_squared_margin_m2< -1e-9)]
ax.scatter(miss.coarse_squared_margin_m2,miss.min_squared_margin_m2,s=90,marker='x',linewidths=2,c='#a73545',label='Grid missed overlap')
lims=[min(a1.min_squared_margin_m2.min(),-.3),min(5,a1.coarse_squared_margin_m2.quantile(.99))];ax.plot([lims[0],lims[1]],[lims[0],lims[1]],ls='--',c='#737d8a',lw=1)
ax.set_xlim(lims);ax.set_ylim(lims);ax.set_xlabel('Grid minimum of paceval margin (m²)');ax.set_ylabel('Stationary-point minimum (m²)');ax.legend(fontsize=8);save(3,'sampled_vs_continuous')
# 4: margin distribution
ax=start('Continuous minimum margins across both model versions')
for v in ['V1','V2']:
 y=a[a.model==v].min_squared_margin_m2;ax.hist(y.clip(-1,3),bins=43,alpha=.56,label=v,color=colors[v])
ax.axvline(0,c='#a73545',ls='--');ax.set_xlabel('Continuous minimum squared margin (m²; clipped tails)');ax.set_ylabel('Synthetic trajectory/model counts');ax.legend();save(4,'minimum_margin_distributions')
# 5: model comparison difference
ax=start('Uncertainty inflation reduces the squared clearance margin')
ax.scatter(b.min_margin_V1_m2,b.delta_margin_m2,s=9,alpha=.3,c='#b87c43');ax.axhline(0,c='#a73545',ls='--');ax.set_xlabel('V1 minimum squared margin (m²)');ax.set_ylabel('V2 − V1 margin (m²)');save(5,'model_margin_shift')
# 6: certificate class count
ax=start('Independent exact rational Bernstein certification')
counts=cert.groupby(['model','exact_interval_status']).size().unstack(fill_value=0)
labels=['SEPARATED','OVERLAP','CONTACT_WITNESS_NO_OVERLAP_PROVEN'];bottom=np.zeros(2)
for label,color in zip(labels,['#1f877f','#d45f47','#f0b857']):
 vals=np.array([counts.get(label,pd.Series(index=['V1','V2'],data=[0,0])).get(v,0) for v in ['V1','V2']]);ax.bar(['V1','V2'],vals,bottom=bottom,color=color,label=label.replace('_',' ').title(),width=.55);bottom+=vals
ax.set_ylabel('Model–trajectory combinations');ax.legend(fontsize=7,loc='upper left');save(6,'exact_certificate_counts')
# 7: minima location versus margin
ax=start('The minimum often occurs within the motion interval')
for v in ['V1','V2']:
 d=a[a.model==v];ax.scatter(d.min_time_normalized,d.min_squared_margin_m2.clip(-1.2,3),s=6,alpha=.23,c=colors[v],label=v)
ax.axhline(0,c='#a73545',ls='--');ax.set_xlabel('Minimum location u');ax.set_ylabel('Squared margin (m², clipped tails)');ax.legend();save(7,'minimum_time_distribution')
# 8: derivative at tangency, real graph sampled
ax=start('The signed-margin derivative isolates a tangential contact')
d=sample[(sample.case_id=='T00001')&(sample.model=='V1')]
ax.plot(d.t,d.derivative_m2_per_normalized_time,'o-',markersize=3,c=colors['V1'],lw=1.5,label='paceval analytic first derivative')
ax.axhline(0,c='#a73545',ls='--');ax.axvline(.5,c='#7c8089',ls=':');ax.set_xlabel('Normalized time u');ax.set_ylabel('d(squared margin)/du (m²)');ax.legend(fontsize=8);save(8,'tangent_derivative')
# 9: 3D relative trajectories from genuine paceval samples
ax=start('Three-dimensional center trajectories in relative coordinates',three=True)
for i in [0,3,4,7,10]:
 d=sample[(sample.case_id==f'T{i:05d}')&(sample.model=='V1')];ax.plot(d.relative_x_m,d.relative_y_m,d.relative_z_m,lw=1.7,label=f'T{i:05d}')
 ax.scatter(d.relative_x_m.iloc[0],d.relative_y_m.iloc[0],d.relative_z_m.iloc[0],s=20)
ax.set_xlabel('Relative x (m)');ax.set_ylabel('Relative y (m)');ax.set_zlabel('Relative z (m)');ax.view_init(elev=23,azim=-60);ax.legend(fontsize=7);save(9,'relative_3d_trajectories')
# 10: 3D operating surface as actual points, not interpolated fabricated values
ax=start('Continuous margin over 3D input and motion configuration',three=True)
d=a[a.model=='V2'].merge(inp[['case_id','x0','y0']],on='case_id');d=d[d.scenario=='near_buffer']
sc=ax.scatter(d.x0,d.y0,d.min_squared_margin_m2,c=d.min_squared_margin_m2,cmap='coolwarm',s=12,alpha=.75)
ax.set_xlabel('Relative x0 (m)');ax.set_ylabel('Relative y0 (m)');ax.set_zlabel('Minimum squared margin (m²)');ax.view_init(23,-60);plt.gcf().colorbar(sc,ax=ax,shrink=.65,pad=.1,label='Actual V2 paceval margin (m²)');save(10,'three_dimensional_margin_map')
print('FIGURES 10 figure pairs saved from actual paceval CSV')
