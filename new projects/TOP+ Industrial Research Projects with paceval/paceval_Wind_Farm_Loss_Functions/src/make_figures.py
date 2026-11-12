#!/usr/bin/env python3
"""Recreate all scientific SVG/PNG diagrams exclusively from published CSV data."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

p=argparse.ArgumentParser();p.add_argument('--data',default='examples');p.add_argument('--output',default='figures');args=p.parse_args()
data=Path(args.data);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
farms=pd.read_csv(data/'farm_results.csv');layouts=pd.read_csv(data/'layouts.csv');models=pd.read_csv(data/'models.csv');turb=pd.read_csv(data/'selected_turbines.csv');audit=pd.read_csv(data/'audit_samples.csv');changes=pd.read_csv(data/'model_update.csv')
styles={'font.size':10,'axes.titlesize':13,'axes.labelsize':10,'savefig.dpi':180,'figure.dpi':120}
plt.rcParams.update(styles)
names=['Inline rows','Staggered','Wide-spaced']
def finish(name):
    plt.tight_layout(pad=1.9)
    for extension in ['png','svg']:plt.savefig(out/f'{name}.{extension}',dpi=200,bbox_inches='tight')
    plt.close()
# Layouts
fig, axs=plt.subplots(1,3,figsize=(12,3.8))
for l,ax in enumerate(axs):
    subset=layouts[layouts.layout_id==l]
    ax.scatter(subset.x_m/140,subset.y_m/140,c='tab:blue',s=65)
    for _,r in subset.iterrows():ax.annotate(str(int(r.turbine_id+1)),(r.x_m/140,r.y_m/140),xytext=(5,5),textcoords='offset points',fontsize=8)
    ax.set_title(names[l]);ax.set_xlabel('Downwind axis at 0° (rotor D)');ax.set_aspect('equal',adjustable='datalim');ax.grid(alpha=.2)
axs[0].set_ylabel('Crosswind axis (rotor D)');fig.suptitle('Eight-turbine synthetic layout configurations',fontsize=15);finish('01_wind_farm_layouts')
# Illustrative wake deficit surface direct native formula for known coefficients (not a CFD field)
dx=np.linspace(140,1450,180);dy=np.linspace(-650,650,160);X,Y=np.meshgrid(dx,dy);r=models.iloc[0];k=r.wake_expansion_k;ct=r.ct;z=(1-np.sqrt(1-ct))*(140/(140+2*k*X))**2*np.exp(-.5*(Y/(70+k*X))**2)
fig,ax=plt.subplots(figsize=(9.8,4.5));im=ax.pcolormesh(X/140,Y/140,z,cmap='viridis',shading='auto');plt.colorbar(im,ax=ax,label='Normalized velocity deficit');ax.set_xlabel('Streamwise separation (D)');ax.set_ylabel('Crosswind separation (D)');ax.set_title('Jensen-inspired wake with Gaussian lateral taper (model 0)');finish('02_wake_deficit_surface')
# directional wake loss at 10 m/s for 3 layouts
z=farms[(farms.model_id==0)&(farms.speed_mps==10)]
fig,ax=plt.subplots(figsize=(9.8,4.8))
for l in range(3):
 q=z[z.layout_id==l].sort_values('direction_deg');ax.plot(q.direction_deg,q.wake_loss_percent,marker='o',label=names[l])
ax.set_xticks(range(0,360,45));ax.set_xlabel('Direction (degrees)');ax.set_ylabel('Synthetic wake power reduction (%)');ax.set_title('Directional farm wake losses at 10 m/s, model 0');ax.grid(alpha=.25);ax.legend();finish('03_directional_wake_loss')
# power at direction zero and varying winds
z=farms[(farms.model_id==0)&(farms.direction_deg==0)]
fig,ax=plt.subplots(figsize=(9.8,4.8))
for l in range(3):
 q=z[z.layout_id==l].sort_values('speed_mps');ax.plot(q.speed_mps,q.net_power_mw,marker='o',label=names[l])
ax.plot(z[z.layout_id==0].sort_values('speed_mps').speed_mps,z[z.layout_id==0].sort_values('speed_mps').gross_power_mw,'k--',label='No-wake gross');ax.set_xlabel('Free-stream wind speed (m/s)');ax.set_ylabel('Eight-turbine output (MW)');ax.set_title('Power response under different layouts, model 0');ax.grid(alpha=.25);ax.legend();finish('04_farm_power_by_wind_speed')
# distribution of 100 model variants across 3 layouts
z=farms[(farms.direction_deg==0)&(farms.speed_mps==8)]
fig,ax=plt.subplots(figsize=(10,4.5));data_series=[z[z.layout_id==l].sort_values('model_id').wake_loss_percent.values for l in range(3)];ax.boxplot(data_series,tick_labels=names,patch_artist=True);ax.set_ylabel('Wake loss (%)');ax.set_title('100 parameterized wake-function variants (8 m/s, 0°)');ax.grid(axis='y',alpha=.2);finish('05_model_variant_sensitivity')
# turbine wake gradient
z=turb[(turb.model_id==0)&(turb.wind_case==16)]
fig,ax=plt.subplots(figsize=(10,4.5));n=np.arange(8)
for l in range(3):
 q=z[z.layout_id==l].sort_values('turbine_id');ax.plot(n+1,q.effective_speed_mps,marker='o',label=names[l])
ax.axhline(10,c='grey',ls='--',label='Free stream');ax.set_xlabel('Turbine index');ax.set_ylabel('Effective inflow (m/s)');ax.set_title('Wake-induced variation across eight turbines at 10 m/s, 0°');ax.grid(alpha=.25);ax.legend();finish('06_turbine_inflow_comparison')
# audit residuals
fig,ax=plt.subplots(figsize=(9.5,4.6));
for kind in ['wake','power']:
 q=audit[audit.kind==kind];ax.scatter(np.arange(len(q)),abs(q.paceval_value-q.native_value)+1e-20,alpha=.65,s=12,label=kind)
ax.set_yscale('log');ax.set_ylabel('|paceval − independent native result| + 1e−20');ax.set_xlabel('Audit sample index within formula class');ax.set_title('Native numerical agreement for sampled expressions');ax.grid(alpha=.2);ax.legend();finish('07_numerical_audit_residuals')
# version update
fig,ax=plt.subplots(figsize=(9.8,4.4));q=changes[(changes.layout_id==0)&(changes.wind_case.isin([0,8,16,24]))].sort_values('wind_case');ax.bar(np.arange(len(q))-.19,q.old_net_mw,width=.38,label='Model 17 v1');ax.bar(np.arange(len(q))+.19,q.new_net_mw,width=.38,label='Model 17 v2');ax.set_xticks(np.arange(len(q)),['6','8','10','12']);ax.set_xlabel('Wind speed (m/s) at 0°');ax.set_ylabel('Farm net power (MW)');ax.set_title('Targeted change to one Wake-graph version');ax.legend();ax.grid(axis='y',alpha=.2);finish('08_model_version_update')
print('Created eight scientific diagrams in PNG + SVG')
