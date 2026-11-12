#!/usr/bin/env python3
"""Render plots only from the paceval-exported CSVs."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
r=Path(__file__).resolve().parents[1];f=r/'figures'
req=list(csv.DictReader((r/'examples/requests.csv').open()))
reg=list(csv.DictReader((r/'examples/tool_registry.csv').open()))
surf=list(csv.DictReader((r/'examples/response_surface.csv').open()))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(stem):
    plt.savefig(f/(stem+'.png'),dpi=185,bbox_inches='tight',pad_inches=.22)
    plt.savefig(f/(stem+'.pdf'),bbox_inches='tight',pad_inches=.22)
    plt.close()
def chart(name,title,xlabel,ylabel,x,y):
    fig,ax=plt.subplots(figsize=(8.2,4.5));ax.plot(x,y,lw=1.6,color='#177d8a');ax.set(xlabel=xlabel,ylabel=ylabel,title=title);ax.grid(alpha=.22);save(name)
# 01 architecture diagram: factual host / computation boundary
fig,ax=plt.subplots(figsize=(10.0,2.6));ax.axis('off')
labels=['Fixed model inputs','C++ tool dispatcher','paceval handles (51)','Native / high-precision audit']
for i,label in enumerate(labels):
    ax.text(.125+.25*i,.51,label,ha='center',va='center',fontsize=11,fontweight='bold',transform=ax.transAxes,bbox=dict(boxstyle='round,pad=.7',fc=['#edf4f7','#e3eff2','#d8f0eb','#edf4f7'][i],ec='#328898'))
    if i<3:ax.annotate('',xy=(.253+.25*i,.51),xytext=(.225+.25*i,.51),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#328898',lw=2))
ax.set_title('Actual executed mathematical tool architecture',pad=12,fontweight='bold');save('01_execution_architecture')
# 02 tool family outputs in first 1500 requests
fig,ax=plt.subplots(figsize=(9,4.7));labels=['poly-log','damped-trig','rational-root','mixed-ratio','nonlinear-log']
for fam in range(5):
    rr=[q for q in req[:3000] if int(q['family'])==fam]
    ax.plot(range(len(rr[:200])),[float(z['paceval']) for z in rr[:200]],label=labels[fam],alpha=.8,lw=1.1)
ax.set(xlabel='Request index within family',ylabel='Model output (dimensionless)',title='Computed outputs of five mathematical tool families');ax.legend(ncol=3,fontsize=9);ax.grid(alpha=.2);save('02_tool_family_outputs')
# 03 audit errors by family
fig,ax=plt.subplots(figsize=(8.2,4.5)); values=[]
for fam in range(5):values.append(max(float(z['abs_error']) for z in req if int(z['family'])==fam))
ax.bar(labels,values,color='#2c8b87');ax.set(ylabel='Maximum absolute error',title='paceval versus independently coded C++');ax.tick_params(axis='x',rotation=15);save('03_numerical_audit')
# 04 tool formula catalogue
fig,ax=plt.subplots(figsize=(8.4,4.2));ids=np.arange(1,51)
ax.scatter(ids,[int(q['family']) for q in reg[:50]],c=np.arange(50),cmap='viridis',s=58);ax.set(xlabel='Tool identifier',ylabel='Formula family (0–4)',title='50 frozen version-1 mathematical tool definitions');ax.set_yticks(range(5),labels);ax.grid(alpha=.15);save('04_tool_registry')
# 05 surface
x=np.array([float(z['x']) for z in surf]);y=np.array([float(z['y']) for z in surf]);v=np.array([float(z['paceval']) for z in surf]);X=x.reshape(61,61);Y=y.reshape(61,61);Z=v.reshape(61,61)
fig=plt.figure(figsize=(9,6.3));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(X,Y,Z,cmap='viridis',alpha=.95,rstride=1,cstride=1,linewidth=0,antialiased=True)
ax.set(xlabel='x (dimensionless)',ylabel='y (dimensionless)',zlabel='Tool output',title='3D computed response surface, tool 23');ax.view_init(28,-58);save('05_response_surface_3d')
# 06 contour
fig,ax=plt.subplots(figsize=(8.4,5.2));p=ax.contourf(X,Y,Z,25,cmap='viridis');fig.colorbar(p,ax=ax,label='Tool output');ax.set(xlabel='x (dimensionless)',ylabel='y (dimensionless)',title='Computed 2D contour of tool 23');save('06_response_contours')
# 07 version comparison
ver=list(csv.DictReader((r/'examples/version_audit.csv').open()))[0]
fig,ax=plt.subplots(figsize=(6.5,4.4));ax.bar(['v1 (retained)','v2 (new graph)'],[float(ver['old_result']),float(ver['new_result'])],color=['#198e9b','#d08249']);ax.set(ylabel='Formula output',title='Immutable graph-version update on identical inputs');save('07_model_versioning')
# 08 distribution
fig,ax=plt.subplots(figsize=(8.4,4.5));ax.hist([float(q['paceval']) for q in req],bins=80,color='#2d8f88',alpha=.85);ax.set(xlabel='Tool output (dimensionless)',ylabel='Count',title='10,000 deterministic scripted requests');save('08_request_distribution')
print('Generated eight numbered figures (PNG+PDF) from actual CSV results')
