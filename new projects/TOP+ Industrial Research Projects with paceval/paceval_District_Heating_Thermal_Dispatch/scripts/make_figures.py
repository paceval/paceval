#!/usr/bin/env python3
"""All scientific result figures are made exclusively from recorded MCP output CSV.
The architecture diagram is expressly conceptual and is not a computed result.
"""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
R=Path(__file__).resolve().parents[1]
F=R/'figures'
E=list(csv.DictReader((R/'results/mcp_edge_observed.csv').open()))
N=list(csv.DictReader((R/'results/mcp_network_observed.csv').open()))
C={'ink':'#17374A','teal':'#137f87','orange':'#db772b','violet':'#6e5bb5'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.labelsize':11,'axes.titlesize':13,'axes.grid':True,'grid.alpha':.2,'figure.facecolor':'white','savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 fig.savefig(F/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.16)
 fig.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.15)
 plt.close(fig)
def matrix(records,ykey,xkey,val):
 ys=sorted({float(r[ykey]) for r in records});xs=sorted({float(r[xkey]) for r in records})
 values=np.empty((len(ys),len(xs)))
 for r in records:values[ys.index(float(r[ykey])),xs.index(float(r[xkey]))]=float(r[val])
 return np.array(xs),np.array(ys),values
# 1. schematic, intentionally NOT numerical
fig,ax=plt.subplots(figsize=(10.6,3.4));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
def rect(x,y,w,h,label,fc):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.15,rounding_size=.15',fc=fc,ec='#a7c1c9',lw=1.1));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=11,color=C['ink'],weight='bold')
rect(.15,1.6,1.4,.85,'Heat plant','#deeee7');rect(2.1,1.6,1.45,.85,'Main trunk','#e6eef5');rect(4.2,2.75,1.4,.8,'Branch A','#f3e5d9');rect(4.2,.6,1.4,.8,'Branch B','#f3e5d9');rect(6.4,2.75,1.7,.8,'District A','#e7f1f1');rect(6.4,.6,1.7,.8,'District B','#e7f1f1')
for a,b in [((1.68,2.02),(1.93,2.02)),((3.72,2.02),(4.08,3.14)),((3.72,2.02),(4.08,1.0)),((5.78,3.14),(6.23,3.14)),((5.78,1.0),(6.23,1.0))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,lw=2,color=C['teal']))
ax.text(9.1,2.3,'T / loss',ha='center',color=C['ink']);ax.text(9.1,1.8,'P / flow',ha='center',color=C['ink']);ax.text(9.1,1.3,'Constraints',ha='center',color=C['ink'])
ax.text(.25,.3,'Stylized 3-edge radial topology; return temperature is fixed and hydraulics are prescribed.',fontsize=9,color='#5d737d')
fig.suptitle('Simplified source–trunk–two-consumer thermal network',fontsize=14,color=C['ink']);save(fig,'01_network_schematic')
# 2 edge loss vs UA
fig,ax=plt.subplots(figsize=(9.2,5.2));ys=sorted({float(r['Tamb_C']) for r in E})
for amb in [-8,4,16,28]:
 rows=sorted([r for r in E if float(r['Tamb_C'])==amb],key=lambda r:float(r['UA_W_per_K']))
 ax.plot([float(r['UA_W_per_K']) for r in rows],[float(r['heat_loss_v2_W'])/1000 for r in rows],marker='o',label=f'{amb:g} °C')
ax.set(xlabel='Pipe conductance UA (W/K)',ylabel='Heat loss (kW)',title='Executed pipe heat-loss map · exponential version');ax.legend(title='Ambient temperature',ncol=2);save(fig,'02_pipe_heat_losses')
# 3 edge temperature heatmap
x,y,z=matrix(E,'Tamb_C','UA_W_per_K','outlet_v2_C')
fig,ax=plt.subplots(figsize=(9.1,5.2));cf=ax.contourf(x,y,z,levels=17,cmap='viridis');ax.scatter(*np.meshgrid(x,y),s=6,c='white',alpha=.5);fig.colorbar(cf,ax=ax,label='Pipe outlet temperature (°C)');ax.set(xlabel='Pipe conductance UA (W/K)',ylabel='Ambient temperature (°C)',title='Recorded paceval pipe outlet temperature · v2');save(fig,'03_pipe_outlet_map')
# 4 model discrepancy physically meaningful and tiny
fig,ax=plt.subplots(figsize=(9.1,5.1));rows=sorted([r for r in E if float(r['Tamb_C'])==-8],key=lambda r:float(r['UA_W_per_K']))
ax.plot([float(r['UA_W_per_K']) for r in rows],[(float(r['outlet_v2_C'])-float(r['outlet_v1_C']))*1000 for r in rows],marker='s',color=C['orange']);ax.set(xlabel='Pipe conductance UA (W/K)',ylabel='v2 − v1 outlet temperature (mK)',title='Model version dependence · recorded point differences');save(fig,'04_pipe_model_versions')
# 5 guard grid
x,y,z=matrix(N,'Tamb_C','Ts_C','guard_v2')
fig,ax=plt.subplots(figsize=(8.6,5.0));from matplotlib.colors import ListedColormap
im=ax.imshow(z,origin='lower',aspect='auto',extent=[x.min()-2,x.max()+2,y.min()-2,y.max()+2],cmap=ListedColormap(['#cf7062','#6daa7a']),vmin=0,vmax=1)
for r in N:ax.text(float(r['Ts_C']),float(r['Tamb_C']), '✓' if int(r['guard_v2']) else '×',ha='center',va='center',fontsize=15,color='white',weight='bold')
ax.set(xlabel='Selected supply temperature (°C)',ylabel='Ambient temperature (°C)',title='Mathematical dispatch feasibility · v2 (15 / 25 cases)');save(fig,'05_dispatch_feasibility')
# 6 network margin map
x,y,z=matrix(N,'Tamb_C','Ts_C','temp_margin_v2_K')
fig,ax=plt.subplots(figsize=(9.1,5.2));cf=ax.contourf(x,y,z,levels=np.linspace(z.min(),z.max(),20),cmap='RdYlBu_r');ax.contour(x,y,z,[0],linewidths=2,colors='black');ax.scatter(*np.meshgrid(x,y),s=12,c='black');fig.colorbar(cf,ax=ax,label='Minimum branch temperature margin (K)');ax.set(xlabel='Supply temperature (°C)',ylabel='Ambient temperature (°C)',title='Temperature feasibility threshold · recorded v2 points');save(fig,'06_network_temperature_margin')
# 7 heat delivered vs required
fig,ax=plt.subplots(figsize=(9.2,5.2))
for amb in [-8,2,12]:
 rows=sorted([r for r in N if float(r['Tamb_C'])==amb],key=lambda r:float(r['Ts_C']))
 xs=[float(r['Ts_C']) for r in rows];ax.plot(xs,[float(r['delivered_v2_kW']) for r in rows],marker='o',label=f'{amb:g} °C delivered');ax.plot(xs,[float(r['demand_kW']) for r in rows],ls='--',alpha=.7,label=f'{amb:g} °C required')
ax.set(xlabel='Supply temperature (°C)',ylabel='Heat at customers (kW)',title='Delivered thermal power versus synthetic demand');ax.legend(ncol=2,fontsize=9);save(fig,'07_delivered_vs_demand')
# 8 loss fraction across dispatch candidates
fig,ax=plt.subplots(figsize=(9.2,5.1));
for amb in [-8,-3,2,7,12]:
 rows=sorted([r for r in N if float(r['Tamb_C'])==amb],key=lambda r:float(r['Ts_C']))
 ax.plot([float(r['Ts_C']) for r in rows],[100*float(r['loss_fraction_v2']) for r in rows],marker='o',label=f'{amb:g} °C')
ax.set(xlabel='Supply temperature (°C)',ylabel='Thermal network loss fraction (%)',title='Heat source versus delivered energy · v2');ax.legend(title='Ambient');save(fig,'08_network_loss_fraction')
# 9 3D surface
x,y,z=matrix(N,'Tamb_C','Ts_C','temp_margin_v2_K');XX,YY=np.meshgrid(x,y)
fig=plt.figure(figsize=(9.5,6.4));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(XX,YY,z,cmap='viridis',edgecolor='white',linewidth=.35,alpha=.96);ax.set(xlabel='Supply temperature (°C)',ylabel='Ambient temperature (°C)',zlabel='Supply margin (K)',title='Synthetic dispatch margin surface · actual paceval values');ax.view_init(elev=29,azim=-124);fig.colorbar(surf,ax=ax,shrink=.6,pad=.12,label='Margin (K)');save(fig,'09_dispatch_surface_3d')
# 10 pump proxy
fig,ax=plt.subplots(figsize=(9.2,4.8));rows=sorted([r for r in N if float(r['Ts_C'])==78],key=lambda r:float(r['Tamb_C']))
ax.plot([float(r['Tamb_C']) for r in rows],[float(r['pump_W'])/1000 for r in rows],marker='o',color=C['violet']);ax.set(xlabel='Ambient temperature (°C)',ylabel='Pump-power proxy (kW)',title='Hydraulic path proxy under prescribed mass flows');save(fig,'10_hydraulic_proxy')
# 11 model version delivered power 
fig,ax=plt.subplots(figsize=(9.2,4.8));
for amb in [-8,2,12]:
 rows=sorted([r for r in N if float(r['Tamb_C'])==amb],key=lambda r:float(r['Ts_C']))
 ax.plot([float(r['Ts_C']) for r in rows],[float(r['delivered_delta_W']) for r in rows],marker='o',label=f'{amb:g} °C ambient')
ax.set(xlabel='Supply temperature (°C)',ylabel='v2 − v1 delivered heat (W)',title='Mathematical model-version effect on aggregate delivery');ax.legend();save(fig,'11_delivery_version_delta')
print('Created 11 paired PNG/PDF figures from',len(E),'edge and',len(N),'network observed scenarios')
