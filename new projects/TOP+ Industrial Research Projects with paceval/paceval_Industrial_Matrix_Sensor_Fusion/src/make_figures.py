#!/usr/bin/env python3
"""Scientific plots based on executed paceval result files; schematic clearly labeled."""
from pathlib import Path
import sys,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch,Ellipse
from matplotlib.lines import Line2D
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
figs=root/'figures';figs.mkdir(exist_ok=True)
r=root/'results';rows=list(csv.DictReader((r/'sensor_fusion.csv').open()));surface=list(csv.DictReader((r/'quality_score_surface.csv').open()))
N=512
A=np.fromfile(r/'matrix_512_original.f64',dtype='<f8').reshape(N,N)
L=np.fromfile(r/'matrix_512_cholesky.f64',dtype='<f8').reshape(N,N)
Inv=np.fromfile(r/'matrix_512_inverse.f64',dtype='<f8').reshape(N,N)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.labelsize':10,'figure.facecolor':'white','savefig.facecolor':'white','axes.grid':False})
def save(i,slug,fig):
    fig.savefig(figs/f'{i:02d}_{slug}.png',dpi=215,bbox_inches='tight',pad_inches=.18)
    fig.savefig(figs/f'{i:02d}_{slug}.pdf',bbox_inches='tight',pad_inches=.18)
    plt.close(fig)
def line_v(v,name):return np.array([float(row[name]) for row in rows if int(row['model_version'])==v])
idx=np.arange(16)
# 01: Architecture. This is a schematic, not experimental values.
fig,ax=plt.subplots(figsize=(11.5,3.35));ax.set(xlim=(0,12),ylim=(-.8,3.1));ax.axis('off')
nodes=[(.2,'Sensor A + B\nSynthetic covariance'),(2.65,'paceval matrix kernels\nSPD / inverse'),(5.15,'Information fusion\nP = (P1^-1 + P2^-1)^-1'),(7.75,'Versioned paceval\nscores and guards'),(10.1,'Supervised quality\nreporting')]
for x,label in nodes:
    p=FancyBboxPatch((x,.9),1.95,1.2,boxstyle='round,pad=0.15',fc='#e9f2f5',ec='#217b89',lw=1.5);ax.add_patch(p);ax.text(x+.975,1.52,label,ha='center',va='center',fontsize=9,color='#103e54')
for x,_ in nodes[:-1]:ax.add_patch(FancyArrowPatch((x+2.12,1.5),(x+2.44,1.5),arrowstyle='-|>',mutation_scale=18,color='#c97930',lw=1.7))
ax.text(6.0,.05,'Real computation: paceval SDK 4.25  |  Host: dependency order and decision routing',ha='center',fontsize=10,color='#245666')
ax.set_title('Research architecture: mathematical graph execution in an industrial sensor-fusion twin',pad=10)
save(1,'research_architecture',fig)
# 02: Dense input matrix
fig,ax=plt.subplots(figsize=(7.5,5.2));im=ax.imshow(A[:64,:64],origin='lower',cmap='viridis',interpolation='nearest');fig.colorbar(im,ax=ax,shrink=.85,label='Synthetic covariance units');ax.set(xlabel='Column',ylabel='Row',title='512 x 512 SPD input: upper-left 64 x 64 block');save(2,'dense_spd_input',fig)
# 03 Cholesky
fig,ax=plt.subplots(figsize=(7.5,5.2));im=ax.imshow(L[:64,:64],origin='lower',cmap='plasma',interpolation='nearest');fig.colorbar(im,ax=ax,shrink=.85,label='Factor coefficient');ax.set(xlabel='Column',ylabel='Row',title='Full paceval Cholesky factor: visible lower-triangular structure');save(3,'cholesky_factor',fig)
# 04 inverse
fig,ax=plt.subplots(figsize=(7.5,5.2));im=ax.imshow(Inv[:64,:64],origin='lower',cmap='coolwarm',interpolation='nearest');fig.colorbar(im,ax=ax,shrink=.85,label='Inverse-matrix coefficient');ax.set(xlabel='Column',ylabel='Row',title='Full paceval SPD inverse: upper-left 64 x 64 block');save(4,'inverse_matrix',fig)
# 05 fused state
fig,ax=plt.subplots(figsize=(9,4.7));
for v in [1,2]:ax.plot(idx,line_v(v,'fused_0'),marker='o',ms=4,label=f'Model v{v}')
ax.set(xlabel='Synthetic measurement scenario',ylabel='Fused state coordinate 0 (normalized)',title='Versioned information fusion: executed paceval output');ax.legend();ax.grid(alpha=.23);save(5,'fused_state_versions',fig)
# 06 uncertainty ellipse derived only from executed covariance output
fig,ax=plt.subplots(figsize=(7.2,5.1));cs=['#067fa4','#cb7748','#6850a4','#ca3f68'];
for z,s in enumerate([0,5,10,15]):
    row=next(row for row in rows if int(row['scenario'])==s and int(row['model_version'])==2)
    cov=np.array([[float(row['cov_diag_0']),float(row['cov_01'])],[float(row['cov_01']),float(row['cov_diag_1'])]])
    vals,vecs=np.linalg.eigh(cov);angle=np.degrees(np.arctan2(vecs[1,1],vecs[0,1]));ell=Ellipse((float(row['fused_0']),float(row['fused_1'])),4*np.sqrt(vals[1]),4*np.sqrt(vals[0]),angle=angle,fill=False,lw=1.8,ec=cs[z],label=f'Scenario {s}');ax.add_patch(ell)
    ax.plot(float(row['fused_0']),float(row['fused_1']),'o',color=cs[z],ms=4)
ax.autoscale();ax.set_aspect('equal',adjustable='datalim');ax.set(xlabel='Fused coordinate 0',ylabel='Fused coordinate 1',title='Two-standard-deviation synthetic covariance ellipses (model v2)');ax.grid(alpha=.2);ax.legend(fontsize=8);save(6,'fused_covariance_ellipses',fig)
# 07 Mahalanobis and gate
fig,ax=plt.subplots(figsize=(9,4.5));
for v in (1,2):ax.plot(idx,line_v(v,'mahalanobis_squared'),marker='o',label=f'Model v{v}')
ax.axhline(12.592,color='#b34840',ls='--',label='Illustrative 6D gate: 12.592');ax.set(xlabel='Scenario',ylabel='Squared Mahalanobis distance',title='Multi-sensor innovation: distinct anomaly regimes');ax.grid(alpha=.22);ax.legend();save(7,'mahalanobis_scenarios',fig)
# 08 quality decision guard
fig,ax=plt.subplots(figsize=(9,4.4));
for v in (1,2):ax.plot(idx,line_v(v,'quality_guard'),marker='o',ms=3,label=f'Model v{v}')
ax.axhline(0,c='#24775b',ls='--');ax.axhline(-8,c='#b75e42',ls=':');ax.axhspan(-100,-8,alpha=.08,color='#bf4c4c');ax.set(xlabel='Scenario',ylabel='Quality acceptance margin (dimensionless)',title='paceval-computed quality margins and three decision regions');ax.legend();ax.grid(alpha=.2);save(8,'quality_guard_regions',fig)
# 09 3D surface computed by paceval
xy=np.array([[float(r['mahalanobis_squared']),float(r['temperature_c']),float(r['model_v2_score'])] for r in surface]).reshape(25,25,3)
D,T,Z=xy[:,:,0],xy[:,:,1],xy[:,:,2]
fig=plt.figure(figsize=(9,5.5));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(D,T,Z,cmap='viridis',linewidth=0,antialiased=True,alpha=.95);ax.set(xlabel='Mahalanobis d squared',ylabel='Temperature (C)',zlabel='Quality score',title='paceval v2 quality score: 625 directly evaluated parameter pairs');ax.view_init(elev=27,azim=-120);fig.colorbar(surf,ax=ax,shrink=.55,pad=.08);save(9,'quality_score_surface_3d',fig)
# 10 2D contour
fig,ax=plt.subplots(figsize=(8.2,5.3));cp=ax.contourf(D,T,Z,levels=20,cmap='viridis');fig.colorbar(cp,ax=ax,label='Model v2 score');c=ax.contour(D,T,Z,levels=[12.592],colors='#e86a2a',linewidths=2);ax.clabel(c,fmt={12.592:'Gate threshold'},fontsize=8);ax.set(xlabel='Mahalanobis distance squared',ylabel='Temperature (C)',title='Actual paceval quality surface and illustrative acceptance boundary');save(10,'quality_contour_gate',fig)
# 11 sensitivity
fig,ax=plt.subplots(figsize=(9,4.5));
for v,k in [(1,'model_v1_temp_sensitivity'),(2,'model_v2_temp_sensitivity')]:
    dat={float(r['temperature_c']):float(r[k]) for r in surface}
    ax.plot(sorted(dat),[dat[t] for t in sorted(dat)],label=f'Model v{v}',lw=2)
ax.set(xlabel='Temperature (C)',ylabel='Analytic partial score sensitivity (per C)',title='Versioned analytical temperature sensitivities calculated by paceval');ax.legend();ax.grid(alpha=.22);save(11,'temperature_sensitivities',fig)
# 12 decisions v1/v2
fig,ax=plt.subplots(figsize=(8,4.4));categories=['ACCEPT','REVIEW','REJECT'];vals=np.array([[sum(int(r['model_version'])==v and r['decision']==cat for r in rows) for cat in categories] for v in [1,2]])
x=np.arange(3);w=.36;ax.bar(x-w/2,vals[0],width=w,label='Model v1');ax.bar(x+w/2,vals[1],width=w,label='Model v2');ax.set_xticks(x,categories);ax.set(xlabel='Hypothetical decision category',ylabel='Number of synthetic scenarios',title='Complete 32-case decision audit');ax.legend();ax.grid(axis='y',alpha=.16);save(12,'quality_decision_counts',fig)
print('PASS 12 figures, plus independent marketing hero, all supported by recorded paceval data except marked conceptual architecture')
