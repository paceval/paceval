#!/usr/bin/env python3
"""Reproduce application figures from actual paceval SDK and live MCP result files.
The hero concept illustration is deliberately not treated as a calculated field.
"""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.colors import ListedColormap
from mpl_toolkits.mplot3d import Axes3D
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
figs=root/'figures';figs.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/'results/local_sdk_results.csv').open()))
main=json.loads((root/'results/live_mcp_main_batch.json').read_text())
TEAL='#018BA4'; BLUE='#184A72'; ORANGE='#E58A35'; VIOLET='#6B5B95';INK='#25364A'
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'axes.labelsize':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','font.family':'DejaVu Sans'})
def save(name,fig):
 fig.savefig(figs/f'{name}.png',dpi=200,bbox_inches='tight',pad_inches=.25)
 fig.savefig(figs/f'{name}.pdf',bbox_inches='tight',pad_inches=.25)
 plt.close(fig)
def grid(T,key):
 v=[r for r in rows if r['scenario']==f'T{T}']
 A=np.array([float(r[key]) for r in v]).reshape(11,11)
 return np.arange(11)/10,np.arange(11)/10,A
# 01 architecture summary: conceptual, with explicitly marked engine stages
fig,ax=plt.subplots(figsize=(12,3.2));ax.set_xlim(0,12);ax.set_ylim(0,3);ax.axis('off')
labels=[('Machine records','Synthetic x, y, z, T'),('AI / model agent','Select version & inputs'),('paceval MCP','Remote graph handles'),('Mathematical outputs','Correction + guard scores'),('Host policy','Supervisory reports')]
for i,(title,sub) in enumerate(labels):
 x=.15+i*2.45;box=FancyBboxPatch((x,.9),2.1,1.25,boxstyle='round,pad=0.12',fc='#E7F2F5' if i%2==0 else '#EAF0F8',ec=TEAL if i in (1,2,3) else '#9EB4C3',lw=1.2);ax.add_patch(box)
 ax.text(x+1.05,1.61,title,ha='center',va='center',color=INK,fontsize=11,fontweight='bold');ax.text(x+1.05,1.2,sub,ha='center',va='center',fontsize=8,color='#56697C')
 if i<4:ax.annotate('',xy=(x+2.43,1.5),xytext=(x+2.12,1.5),arrowprops=dict(arrowstyle='->',lw=1.8,color=TEAL))
ax.text(6,2.7,'Verified workflow: mathematical outputs are evaluated in paceval graphs',ha='center',fontweight='bold',color=INK)
save('01_executed_architecture',fig)
# 02 3D surface
X,Y,Z=grid(25,'correction_v2');XX,YY=np.meshgrid(X,Y)
fig=plt.figure(figsize=(9.8,6.5));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(XX,YY,Z,cmap='viridis',rstride=1,cstride=1,edgecolor='none',alpha=.98);ax.view_init(25,-60)
ax.set(xlabel='Normalized X',ylabel='Normalized Y',zlabel='Synthetic correction',title='Version 2: evaluated correction surface at 25 °C');fig.colorbar(surf,ax=ax,shrink=.65,pad=.14,label='Correction (model units)');save('02_correction_surface_3d',fig)
#03/04/05/06 maps
for name,key,title,cmap,label in [
 ('03_corrected_field','correction_v2','Version 2 correction map at 25 °C','viridis','Model correction'),
 ('04_model_revision','version_delta','Mathematical change between model versions at 25 °C','coolwarm','V2 minus V1'),
 ('05_temperature_sensitivity','temperature_sensitivity_v2','Analytical temperature sensitivity (V2)','plasma','dCorrection/dT'),
 ('06_position_sensitivity','x_sensitivity_v2','Analytical X-position sensitivity (V2)','cividis','dCorrection/dx')]:
 x,y,A=grid(25,key);fig,ax=plt.subplots(figsize=(7.8,5.1));im=ax.imshow(A,origin='lower',extent=[0,1,0,1],aspect='auto',cmap=cmap);ax.set(xlabel='X, normalized',ylabel='Y, normalized',title=title);fig.colorbar(im,ax=ax,label=label);save(name,fig)
# 07 model decision outcomes heatmap
v=[r for r in rows if r['scenario']=='T25'];codes={'ACCEPT':0,'REVIEW':1,'REJECT':2};A=np.array([codes[r['decision']] for r in v]).reshape(11,11)
fig,ax=plt.subplots(figsize=(7.8,5.1));im=ax.imshow(A,origin='lower',extent=[0,1,0,1],aspect='auto',cmap=ListedColormap(['#2E9B90','#EFBB56','#CC5D55']),vmin=0,vmax=2);ax.set(xlabel='X, normalized',ylabel='Y, normalized',title='Synthetic quality classifications for the V2 model at 25 °C')
cb=fig.colorbar(im,ax=ax,ticks=[0,1,2]);cb.ax.set_yticklabels(['ACCEPT','REVIEW','REJECT']);save('07_quality_decision_regions',fig)
#08 outcomes at each temperature
fig,ax=plt.subplots(figsize=(9,4.8));temp=[15,25,35,45];bottom=np.zeros(4)
for status,c in [('ACCEPT','#2E9B90'),('REVIEW','#EFBB56'),('REJECT','#CC5D55')]:
 counts=[sum(r['decision']==status for r in rows if r['scenario']==f'T{T}') for T in temp]
 ax.bar([str(T) for T in temp],counts,bottom=bottom,label=status,color=c);bottom+=np.array(counts)
ax.set(title='Synthetic classifications across temperature scenarios',ylabel='Number of records',xlabel='Temperature (°C)');ax.legend(frameon=False,ncol=3,loc='upper right');save('08_temperature_decisions',fig)
#09 governance vs x across y=.5
v=[r for r in rows if r['scenario']=='T25' and abs(float(r['y'])-.5)<1e-8];v.sort(key=lambda r:float(r['x']))
fig,ax=plt.subplots(figsize=(8.5,4.8));ax.plot([float(r['x']) for r in v],[float(r['governance_score']) for r in v],marker='o',color=ORANGE,lw=2)
ax.set(title='Versioned model governance score along a machine cross-section',xlabel='X, normalized; Y = 0.5; T = 25 °C',ylabel='Composite score (dimensionless)');save('09_governance_cross_section',fig)
# 10 archived genuine MCP batch
z1=np.array([r['v1'] for r in main['data']]).reshape(4,4);z2=np.array([r['v2'] for r in main['data']]).reshape(4,4)
fig,axes=plt.subplots(1,2,figsize=(10.3,4.8),constrained_layout=True);a=min(z1.min(),z2.min());b=max(z1.max(),z2.max())
for ax,A,lab in zip(axes,[z1,z2],['V1: remote paceval MCP 4.26','V2: remote paceval MCP 4.26']):
 im=ax.imshow(A,origin='lower',extent=[0,1,0,1],cmap='viridis',vmin=a,vmax=b);ax.set(title=lab,xlabel='Normalized X',ylabel='Normalized Y')
fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.75,label='Actual server correction output');save('10_actual_remote_mcp_results',fig)
# 11 response vs temperature from 4 actual SDK conditions
v=[r for r in rows if abs(float(r['x'])-.5)<1e-10 and abs(float(r['y'])-.5)<1e-10 and r['scenario']!='stress'];v.sort(key=lambda r:float(r['temp']))
fig,ax=plt.subplots(figsize=(8.5,4.7));ax.plot([float(r['temp']) for r in v],[float(r['correction_v1']) for r in v],marker='o',label='Version 1',color=BLUE,lw=2);ax.plot([float(r['temp']) for r in v],[float(r['correction_v2']) for r in v],marker='s',label='Version 2',color=ORANGE,lw=2)
ax.set(title='Versioned correction at fixed machine position',xlabel='Temperature (°C)',ylabel='Correction (synthetic units)');ax.legend(frameon=False);save('11_temperature_version_profiles',fig)
print('PASS generated 11 application-specific figure pairs from executed paceval results')
