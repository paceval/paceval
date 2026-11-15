#!/usr/bin/env python3
"""Scientific figures use paceval-produced CSV records; no synthetic redrawing of results."""
from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d import Axes3D
p=Path(__file__).resolve().parents[1];r=p/'results';d=p/'figures'
d.mkdir(exist_ok=True)
sumry=pd.read_csv(r/'scenario_summary.csv');valuations=pd.read_csv(r/'cashflow_valuations.csv');curves=pd.read_csv(r/'curve_profiles.csv');buckets=pd.read_csv(r/'maturity_buckets.csv');surf=pd.read_csv(r/'stress_surface.csv')
navy='#182e4b';blue='#2279b9';gold='#e09c3c';red='#bb4c52';gray='#657589';teal='#298f88'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'axes.spines.right':False,'axes.spines.top':False,'figure.facecolor':'white','axes.grid':True,'grid.alpha':.18,'savefig.facecolor':'white'})
def save(i,key,fig):
 fig.tight_layout(pad=1.7);fig.savefig(d/f'fig{i:02d}_{key}.png',dpi=195);fig.savefig(d/f'fig{i:02d}_{key}.pdf',bbox_inches='tight');plt.close(fig)
order=['BASE','PARALLEL_UP','PARALLEL_DOWN','STEEPENER','FLATTENER','SHORT_UP','SHORT_DOWN','MIXED']
labels=['Base','Parallel +','Parallel −','Steepener','Flattener','Short +','Short −','Mixed']
# 01 Cash-flow maturity structure from actual paceval valuations
x=valuations[(valuations.model=='V2')&(valuations.scenario=='BASE')].copy();x['bucket']=np.floor(x.t_year).astype(int)
y=x.pivot_table(index='bucket',columns='side',values='pv_eur_m',aggfunc='sum').fillna(0)
fig,ax=plt.subplots(figsize=(9.3,4.6));ax.bar(y.index-.21,y['ASSET'],width=.42,color=blue,label='Asset PV');ax.bar(y.index+.21,y['LIABILITY'],width=.42,color=gold,label='Liability PV');ax.set(xlabel='Cash-flow maturity (whole-year bucket)',ylabel='Present value (EUR million)',title='Discounted asset and liability maturity distribution');ax.legend(frameon=False);save(1,'cashflow_maturity',fig)
# 02 stressed zero curves
fig,ax=plt.subplots(figsize=(9.3,4.6));styles=[('BASE',navy),('PARALLEL_UP',red),('STEEPENER',blue),('FLATTENER',gold),('SHORT_DOWN',teal)]
for name,color in styles:
 z=curves[(curves.model=='V2')&(curves.scenario==name)];ax.plot(z.t_year,z.zero_rate*100,label=name.replace('_',' ').title(),lw=2,color=color)
ax.set(xlabel='Maturity (years)',ylabel='Continuously compounded zero rate (%)',title='Illustrative nonparallel interest-rate shocks');ax.legend(ncol=2,frameon=False);save(2,'stressed_zero_curves',fig)
# 03 PV gap across scenarios
fig,ax=plt.subplots(figsize=(9.4,4.65));w=.37;k=np.arange(8)
for j,(version,c) in enumerate([('V1',blue),('V2',gold)]):
 y=sumry[sumry.model==version].set_index('scenario').loc[order];ax.bar(k+(j-.5)*w,y.net_gap_eur_m,width=w,label=version,color=c)
ax.axhline(0,color=gray,lw=.7);ax.set(xticks=k,xticklabels=labels,ylabel='Net asset minus liability PV (EUR million)',title='Economic-value gap changes with curve-shape assumptions');ax.tick_params(axis='x',rotation=25);ax.legend(frameon=False);save(3,'economic_value_gap',fig)
# 04 ΔEVE comparing V1/V2
fig,ax=plt.subplots(figsize=(9.4,4.6));k=np.arange(8);w=.37
for j,(model,c) in enumerate([('V1',blue),('V2',gold)]):
 z=sumry[sumry.model==model].set_index('scenario').loc[order];ax.bar(k+(j-.5)*w,z.delta_eve_eur_m,width=w,color=c,label=model)
ax.axhline(0,color=gray,lw=.8);ax.set(xticks=k,xticklabels=labels,ylabel='Scenario change in net PV (EUR million)',title='Rate-shock sensitivity of fixed contractual cash flows');ax.tick_params(axis='x',rotation=25);ax.legend(frameon=False);save(4,'stress_delta_eve',fig)
# 05 duration changes
fig,ax=plt.subplots(figsize=(9.2,4.6));z=sumry[sumry.model=='V2'].set_index('scenario').loc[order];k=np.arange(8);w=.38
ax.bar(k-w/2,z.asset_duration_years,width=w,color=blue,label='Asset duration');ax.bar(k+w/2,z.liability_duration_years,width=w,color=gold,label='Liability duration');ax.set(xticks=k,xticklabels=labels,ylabel='PV-weighted duration (years)',title='Maturity mismatch after repricing under V2');ax.set_ylim(0,11);ax.tick_params(axis='x',rotation=25);ax.legend(frameon=False);save(5,'asset_liability_duration',fig)
# 06 net DV01
fig,ax=plt.subplots(figsize=(9.2,4.6));z=sumry[sumry.model=='V2'].set_index('scenario').loc[order]
ax.bar(range(8),z.net_dv01_eur_m_per_bp,color=[blue if v>0 else gold for v in z.net_dv01_eur_m_per_bp]);ax.axhline(0,color=gray,lw=.8);ax.set(xticks=range(8),xticklabels=labels,ylabel='Net dEVE / 1 bp (EUR million)',title='Analytic parallel-rate exposure in each V2 scenario');ax.tick_params(axis='x',rotation=25);save(6,'net_dv01',fig)
# 07 grouped maturity gap
fig,ax=plt.subplots(figsize=(9.2,4.6));z=buckets[(buckets.model=='V2')&(buckets.scenario=='BASE')].sort_values('bucket');lab=['0–1','1–3','3–5','5–10','10–20','20–40']
ax.bar(lab,z.net_gap_eur_m,color=[blue if v>0 else gold for v in z.net_gap_eur_m]);ax.axhline(0,color=gray,lw=.9);ax.set(xlabel='Years to contractual payment',ylabel='Discounted asset–liability gap (EUR million)',title='Bucketed maturity structure of the baseline portfolio');save(7,'bucketed_gap',fig)
# 08 3-D stress-surface
fig=plt.figure(figsize=(9.2,5.8));ax=fig.add_subplot(111,projection='3d');x=surf.pivot(index='short_shock',columns='parallel_shock',values='net_gap_eur_m');XX,YY=np.meshgrid(x.columns.to_numpy()*10000,x.index.to_numpy()*10000);zz=x.to_numpy();ax.plot_surface(XX,YY,zz,cmap='cividis',linewidth=.2,edgecolor=(1,1,1,.18),alpha=.96);ax.set(xlabel='Parallel shock (bp)',ylabel='Short shock (bp)',zlabel='Net PV gap (EUR million)',title='paceval-evaluated two-factor EVE response surface');ax.view_init(elev=22,azim=-58);save(8,'3d_stress_surface',fig)
# 09 heatmap same surface to read values
fig,ax=plt.subplots(figsize=(9.2,5.5));g=surf.pivot(index='short_shock',columns='parallel_shock',values='net_gap_eur_m').sort_index(ascending=False)
im=ax.imshow(g.to_numpy(),cmap='RdBu_r',aspect='auto',extent=[-300,300,-300,300]);fig.colorbar(im,ax=ax,label='Net asset-liability PV (EUR million)');ax.set(xlabel='Parallel rate shock (basis points)',ylabel='Short-maturity shock (basis points)',title='Nonlinear operating map of deterministic ALM stress exposure');save(9,'alm_stress_heatmap',fig)
# 10 net curve parameter sensitivities
fig,ax=plt.subplots(figsize=(9.2,4.7));z=sumry[sumry.model=='V2'].set_index('scenario').loc[order];k=np.arange(8);w=.35
ax.bar(k-w/2,z.short_dv01_eur_m_per_bp,width=w,color=teal,label='Short shock parameter');ax.bar(k+w/2,z.long_dv01_eur_m_per_bp,width=w,color=gold,label='Long shock parameter');ax.axhline(0,color=gray,lw=.8);ax.set(xticks=k,xticklabels=labels,ylabel='Net sensitivity / 1 bp (EUR million)',title='Sensitivity allocation between short- and long-tenor shocks');ax.tick_params(axis='x',rotation=25);ax.legend(frameon=False);save(10,'tenor_exposures',fig)
print('PASS figure generation: 10 PNG and 10 vector PDF from actual paceval result CSV')
