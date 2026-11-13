#!/usr/bin/env python3
"""Reproduce every technical plot from recorded paceval output files.
Figure 01 is explicitly a system schematic. Figure 00 is a concept illustration.
"""
from pathlib import Path
import numpy as np,csv,json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,ArrowStyle
from mpl_toolkits.mplot3d import Axes3D
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/'figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'white','axes.titlesize':13,'axes.labelsize':10,'savefig.facecolor':'white'})
NAVY='#102D46'; TEAL='#009E9C'; CORAL='#C87443'; BLUE='#436B91'
def save(fig,file):
 fig.savefig(F/(file+'.png'),dpi=190,bbox_inches='tight',pad_inches=.16)
 fig.savefig(F/(file+'.pdf'),bbox_inches='tight',pad_inches=.16)
 plt.close(fig)
def rows(file): return list(csv.DictReader((ROOT/'results'/file).open()))

def main():
 p=json.loads((ROOT/'examples/model_parameters.json').read_text())
 i512=np.fromfile(ROOT/'results/recorded_baseline/generic_spd_512_inverse.f64',dtype='<f8').reshape(512,512)
 i1024=np.fromfile(ROOT/'results/recorded_baseline/generic_spd_1024_inverse.f64',dtype='<f8').reshape(1024,1024)
 grid=rows('remote_paceval_grid.csv');sc=rows('remote_paceval_scenarios.csv')
 xx=np.array([float(v['x']) for v in grid]).reshape(9,9)
 yy=np.array([float(v['y']) for v in grid]).reshape(9,9)
 q=np.array([float(v['score_v1']) for v in grid]).reshape(9,9)
 q2=np.array([float(v['score_v2']) for v in grid]).reshape(9,9)
 delta=np.array([float(v['version_delta']) for v in grid]).reshape(9,9)
 fig,ax=plt.subplots(figsize=(10.6,4))
 ax.set_xlim(0,10);ax.set_ylim(0,3);ax.axis('off')
 labels=['Recorded 512D\npaceval inverse','Sparse residual\n3 active channels','paceval MCP\n8 reusable graphs','TINC and\nreference audit','Operational\ndecision']
 for j,title in enumerate(labels):
  x=.15+j*2.08
  box=FancyBboxPatch((x,.85),1.8,1.4,boxstyle='round,pad=0.07',facecolor='#edf7f6',edgecolor=TEAL,linewidth=1.5)
  ax.add_patch(box);ax.text(x+.9,1.55,title,ha='center',va='center',color=NAVY,weight='medium',fontsize=10)
  if j<len(labels)-1:ax.annotate('',(x+2.01,1.55),(x+1.82,1.55),arrowprops=dict(arrowstyle='->',color=CORAL,lw=2))
 ax.text(.12,.3,'Architecture schematic. Graph-derived numeric results appear in Figures 02 to 09.',fontsize=10,color='#596b79')
 save(fig,'01_architecture_schematic')
 fig,ax=plt.subplots(figsize=(9.4,5.8));sub=i512[:70,:70]
 im=ax.imshow(sub,cmap='BrBG',interpolation='nearest');ax.set(title='Recorded 512D inverse: leading 70 x 70 matrix block',xlabel='Channel index',ylabel='Channel index')
 fig.colorbar(im,ax=ax,label='Precision matrix coefficient, dimensionless',shrink=.8)
 save(fig,'02_recorded_inverse_matrix')
 fig,ax=plt.subplots(figsize=(9.2,5.1));N=150
 ax.plot(np.arange(N),np.diag(i512)[:N],label='512D baseline inverse',color=TEAL,lw=2)
 ax.plot(np.arange(N),np.diag(i1024)[:N],label='1024D baseline inverse',color=CORAL,lw=1.8,alpha=.8)
 ax.set(title='Persistent matrix arithmetic: precision diagonal',xlabel='Channel index (first 150)',ylabel='Inverse diagonal, dimensionless')
 ax.legend(frameon=False);ax.grid(alpha=.18)
 save(fig,'03_inverse_diagonal_models')
 fig=plt.figure(figsize=(9.1,6.2));ax=fig.add_subplot(111,projection='3d')
 surf=ax.plot_surface(xx,yy,q,cmap='viridis',linewidth=.2,edgecolor='#cccccc',alpha=.96)
 ax.set(title='paceval-computed 3D quality score, model v1',xlabel='Residual channel x',ylabel='Residual channel y',zlabel='Quadratic score q')
 ax.view_init(elev=29,azim=-52);fig.colorbar(surf,shrink=.67,aspect=18,pad=.11,label='q, dimensionless')
 save(fig,'04_mcp_quality_surface')
 fig,ax=plt.subplots(figsize=(9.2,5.9))
 cf=ax.contourf(xx,yy,delta,levels=15,cmap='YlGnBu');ax.contour(xx,yy,delta,levels=8,colors='white',alpha=.6,linewidths=.55)
 ax.set(title='Model revision: additional quadratic diagnostic penalty',xlabel='Residual x',ylabel='Residual y',aspect='equal');fig.colorbar(cf,ax=ax,label='Score v2 minus v1, dimensionless')
 save(fig,'05_model_revision_surface')
 fig,ax=plt.subplots(figsize=(9.2,5.9));t=float(p['threshold'])
 ax.contourf(xx,yy,q,levels=[0,t,35],colors=['#d5f2eb','#f4d9cd'],alpha=.85)
 cont=ax.contour(xx,yy,q,levels=[t],colors=[NAVY],linewidths=2.2)
 ax.clabel(cont,fmt={t:'Illustrative decision boundary'},fontsize=9)
 ax.set(title='Version v1: synthetic acceptance zones',xlabel='Residual x',ylabel='Residual y',aspect='equal')
 save(fig,'06_decision_regions_v1')
 fig,ax=plt.subplots(figsize=(9.4,5.7))
 xs=np.arange(len(sc));qlo=np.array([float(r['q_tinc_lo']) for r in sc]);qhi=np.array([float(r['q_tinc_hi']) for r in sc])
 widths=(qhi-qlo)*1e12
 ax.bar(xs,widths,color=TEAL,width=.6,alpha=.85)
 ax.set_xticks(xs,[f"({r['x']},{r['y']},{r['z']})" for r in sc],rotation=15,ha='right')
 ax.set(title='paceval TINC: recorded arithmetic enclosure widths',xlabel='Residual scenario (x,y,z)',ylabel='Upper minus lower bound, x 10^-12')
 ax.grid(alpha=.17,axis='y');fig.tight_layout()
 save(fig,'07_tinc_enclosure_width')
 fig,ax=plt.subplots(figsize=(9.1,5.3))
 v1=np.array([float(r['dx_v1']) for r in sc]);v2=np.array([float(r['dx_v2']) for r in sc]);x=np.arange(len(sc))
 ax.plot(x,v1,'o-',color=TEAL,lw=2,label='Version 1: dq/dx')
 ax.plot(x,v2,'s--',color=CORAL,lw=2,label='Version 2: dscore/dx')
 ax.set_xticks(x,[r['scenario_id'] for r in sc]);ax.set(title='Graph-computed score sensitivities',xlabel='Independent scenario ID',ylabel='Sensitivity per residual unit')
 ax.grid(alpha=.2);ax.legend(frameon=False)
 save(fig,'08_mcp_model_sensitivity')
 fig,ax=plt.subplots(figsize=(9.2,5.9))
 ax.contour(xx,yy,q,levels=[t],colors=[TEAL],linewidths=2.8)
 ax.contour(xx,yy,q2,levels=[t],colors=[CORAL],linewidths=2.8,linestyles='--')
 ax.plot([],[],color=TEAL,lw=2.5,label='v1 illustrative limit')
 ax.plot([],[],color=CORAL,lw=2.5,ls='--',label='v2 illustrative limit')
 ax.set(title='Boundary migration under an explicit score revision',xlabel='Residual x',ylabel='Residual y',aspect='equal');ax.legend(frameon=False)
 save(fig,'09_versioned_quality_boundaries')
 print('Generated 9 technical figures 01..09 in PNG and vector PDF.')
if __name__=='__main__':main()
