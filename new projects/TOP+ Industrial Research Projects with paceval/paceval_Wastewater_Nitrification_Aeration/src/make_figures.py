#!/usr/bin/env python3
"""Plot only archived selected decimal transcriptions of actual paceval MCP responses."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures'
with (ROOT/'results'/'mcp_grid_selected_observations.csv').open() as f:grid=list(csv.DictReader(f))
with (ROOT/'results'/'mcp_hourly_selected_observations.csv').open() as f:hours=list(csv.DictReader(f))
levels=sorted({float(x['NH4']) for x in grid});dolist=sorted({float(x['DO']) for x in grid})
assert len(levels)==len(dolist)==7 and len(grid)==49

def mtx(key):
    z=np.empty((len(levels),len(dolist)))
    for row in grid:
        i=levels.index(float(row['NH4']));j=dolist.index(float(row['DO']))
        z[i,j]=float(row[key])
    return z

def grid_image(file,key,title,cbar,cmap,contour=None):
    z=mtx(key)
    fig,ax=plt.subplots(figsize=(11.8,6.4),layout='constrained')
    im=ax.imshow(z,origin='lower',aspect='auto',interpolation='nearest',cmap=cmap)
    ax.set_xticks(range(7),labels=[f'{v:g}' for v in dolist]);ax.set_yticks(range(7),labels=[f'{v:g}' for v in levels])
    ax.set_xlabel('Dissolved oxygen, DO [mg O2/L]');ax.set_ylabel('Influent NH4-N [mg N/L]')
    ax.set_title(title,fontsize=17,fontweight='bold',pad=17)
    fig.colorbar(im,ax=ax,label=cbar,shrink=.93)
    if contour is not None and z.min()<contour<z.max():
        c=ax.contour(z,[contour],colors='white',linewidths=2)
        ax.clabel(c,fmt=lambda val:f'Limit {val:g}',fontsize=10)
    fig.text(.01,-.045,'Synthetic input grid | paceval MCP 4.26 selected actual response values | Not plant measurements',fontsize=9,color='#54616b')
    fig.savefig(FIG/file,dpi=170,bbox_inches='tight');plt.close(fig)

grid_image('01_ammonium_outlet_v2_actual_mcp.png','nh4out_v2',
           'Model v2: predicted ammonium outlet proxy','NH4-N out [mg N/L]','viridis',5)
grid_image('02_oxygen_transfer_margin_actual_mcp.png','oxygen_margin_v2',
           'Oxygen transfer margin: OTR minus OUR, v2','Oxygen margin [mg O2/L/h]','coolwarm',0)
grid_image('04_power_proxy_actual_mcp.png','power_v2',
           'Demand-based electric power proxy, model v2','Power proxy [kW]','plasma')

# Four discrete categories: neither accepted, v1 only, v2 only, both accepted.
a=mtx('guard_v1');b=mtx('guard_v2');z=a+2*b
fig,ax=plt.subplots(figsize=(11.8,6.4),layout='constrained')
cmap=ListedColormap(['#dce3ea','#faaf62','#77d3cf','#18685f'])
im=ax.imshow(z,origin='lower',aspect='auto',cmap=cmap,norm=BoundaryNorm(np.arange(-.5,4.5,1),4))
ax.set_xticks(range(7),labels=[f'{v:g}' for v in dolist]);ax.set_yticks(range(7),labels=[f'{v:g}' for v in levels]);ax.set_xlabel('DO [mg O2/L]');ax.set_ylabel('Influent NH4-N [mg N/L]')
ax.set_title('Two simultaneously retained mathematical guard versions',fontsize=16,fontweight='bold',pad=16)
c=fig.colorbar(im,ax=ax,ticks=[0,1,2,3]);c.ax.set_yticklabels(['Neither','v1 only','v2 only','Both'])
for i in range(7):
 for j in range(7): ax.text(j,i,str(int(z[i,j])),ha='center',va='center',color='white' if z[i,j]==3 else '#172b38',fontsize=10)
fig.text(.01,-.045,'Legend = mathematical screening conditions, not permitted operation; paceval MCP 4.26',fontsize=9,color='#54616b')
fig.savefig(FIG/'03_guard_v2_actual_mcp.png',dpi=170,bbox_inches='tight');plt.close(fig)

# Archived 12-snapshot study: not integrated reactor model.
h=np.array([int(row['hour']) for row in hours]);n0=np.array([float(row['NH4']) for row in hours]);
n1=np.array([float(row['nh4out_v1']) for row in hours]);n2=np.array([float(row['nh4out_v2']) for row in hours]);
fig,ax=plt.subplots(figsize=(11.8,6.4),layout='constrained');ax.plot(h,n0,marker='o',label='Input NH4-N',lw=2.2,color='#8794a6')
ax.plot(h,n1,marker='s',label='Model v1 outlet',lw=2.2,color='#22a7ae');ax.plot(h,n2,marker='D',label='Model v2 outlet',lw=2.2,color='#c97236')
ax.axhline(5,ls='--',lw=1.8,color='#a6464d',label='Illustrative target 5 mg N/L')
ax.set(xlabel='Synthetic snapshot index [not integrated hours]',ylabel='Ammonium-N [mg/L]')
ax.grid(alpha=.2);ax.set_title('Synthetic load sequence: simultaneous model versions',fontweight='bold',fontsize=17,pad=16);ax.legend(loc='upper left',ncol=2)
fig.text(.01,-.045,'12 separate mathematical snapshots, NOT a continuous-time or calibrated process simulation | Actual paceval MCP 4.26 outputs',fontsize=9,color='#54616b')
fig.savefig(FIG/'05_twelve_snapshot_outlets_actual_mcp.png',dpi=170,bbox_inches='tight');plt.close(fig)

# Versions directly compared for three selected DO profiles, all from remote results.
fig,ax=plt.subplots(figsize=(11.8,6.4),layout='constrained')
for j,oxy in enumerate([1.0,1.5,2.5,3.5]):
 rows=[r for r in grid if float(r['DO'])==oxy]
 xx=[float(r['NH4']) for r in rows]
 yy=[float(r['nh4out_v2'])-float(r['nh4out_v1']) for r in rows]
 ax.plot(xx,yy,'-o',lw=2,markersize=6,label=f'DO = {oxy:g} mg/L')
ax.axhline(0,color='#505d66',lw=1)
ax.set(xlabel='Influent NH4-N [mg N/L]',ylabel='v2 minus v1 ammonium outlet [mg N/L]');ax.grid(alpha=.2)
ax.set_title('Sensitivity of mathematical screening to model version',fontweight='bold',fontsize=17,pad=16)
ax.legend();fig.text(.01,-.045,'Illustrative parameter assumptions; not biological model validation | Actual paceval MCP 4.26 outputs',fontsize=9,color='#54616b')
fig.savefig(FIG/'06_model_version_comparison_actual_mcp.png',dpi=170,bbox_inches='tight');plt.close(fig)

# Additional dual-axis oxygen and power by snapshot without any invented points.
our=np.array([float(row['OUR_v2']) for row in hours]);otr=np.array([float(row['OTR']) for row in hours]);
fig,ax=plt.subplots(figsize=(11.8,6.4),layout='constrained')
ax.plot(h,our,'-o',lw=2.2,color='#ca6b40',label='Modeled oxygen demand OUR');ax.plot(h,otr,'-s',lw=2.2,color='#207e89',label='Specified oxygen transfer OTR')
ax.fill_between(h,our,otr,where=otr>=our,alpha=.13,color='#329e8d');ax.fill_between(h,our,otr,where=our>otr,alpha=.19,color='#e4675a')
ax.set(xlabel='Synthetic snapshot index',ylabel='mg O2/(L h)');ax.grid(alpha=.2)
ax.set_title('Synthetic snapshots: oxygen requirement and transfer potential',fontsize=17,fontweight='bold',pad=16);ax.legend(loc='upper left')
fig.text(.01,-.045,'Both oxygen quantities are modeled, not directly measured | Actual paceval MCP 4.26 outputs',fontsize=9,color='#54616b')
fig.savefig(FIG/'07_snapshot_oxygen_actual_mcp.png',dpi=170,bbox_inches='tight');plt.close(fig)
print('Figures built:',len(list(FIG.glob('*.png'))))
