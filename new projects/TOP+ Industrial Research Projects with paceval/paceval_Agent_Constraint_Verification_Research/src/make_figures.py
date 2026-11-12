#!/usr/bin/env python3
"""Create scientific figure panels exclusively from the released paceval CSV results."""
from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
D=pd.read_csv(ROOT/'examples/constraint_evaluations.csv'); S=pd.read_csv(ROOT/'examples/ellipse_surface.csv')
NAVY='#17324d';TEAL='#087e8b';ORANGE='#c56e38'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':NAVY,'text.color':NAVY,'axes.titlecolor':NAVY,'savefig.facecolor':'white','figure.facecolor':'white'})
def save(fig,i,name):
 fig.tight_layout(pad=1.7)
 for ext in ('png','pdf'):fig.savefig(FIG/f'{i:02d}_{name}.{ext}',dpi=180,bbox_inches='tight')
 plt.close(fig)
# 01: architecture (factual, not measured)
fig,ax=plt.subplots(figsize=(10.8,2.75));ax.set_xlim(0,11);ax.set_ylim(0,3);ax.axis('off')
from matplotlib.patches import FancyBboxPatch
stages=[('Generated guard\nallowlisted template',.3),('Host validation\ntypes, units, rights',3.0),('paceval graph\nsigned margin g(x)',5.7),('Host decision\naccept/reject/review',8.4)]
for text,x in stages:
 ax.add_patch(FancyBboxPatch((x,.92),2.15,1.15,boxstyle='round,pad=.12',fc='#e3f0f2',ec=TEAL,lw=1.5))
 ax.text(x+1.075,1.50,text,va='center',ha='center',fontsize=10)
for x in (2.5,5.2,7.9):ax.annotate('',xy=(x+.45,1.50),xytext=(x,1.5),arrowprops=dict(arrowstyle='->',lw=2,color=ORANGE))
ax.text(5.5,2.72,'Only finite, typed, authorized normalized inputs reach the mathematical kernel',ha='center',fontsize=11)
save(fig,1,'execution_architecture')
# 02 Decision counts
counts=D.decision.value_counts(); keys=['ACCEPT','REJECT','REVIEW_BOUNDARY']
fig,ax=plt.subplots(figsize=(8,4.2));bars=ax.bar(['Accept','Reject','Boundary review'],[counts.get(k,0) for k in keys],color=[TEAL,ORANGE,'#8b74ae'])
ax.bar_label(bars,fmt='%d',padding=3);ax.set_ylabel('Number of deterministic input cases');ax.set_title('100,000 executed inequality decisions');save(fig,2,'decision_distribution')
# 03 Boundary clusters on log scale
fig,ax=plt.subplots(figsize=(9,4.3));sub=D[D.guard_id.isin([1,2,3,4,5])]
for fam in range(5):
 s=sub[sub.family==fam];ax.scatter(s.sample_id,np.maximum(np.abs(s.paceval_margin),1.e-17),s=10,alpha=.65,label=['Threshold','Ellipse','Quadratic','Affine','Nonlinear'][fam])
ax.axhline(1e-8,ls='--',c='black',label='review threshold')
ax.set_yscale('log');ax.set_xlabel('Input index within guard');ax.set_ylabel('|signed margin| (dimensionless)');ax.set_title('Boundary-adversarial samples and review zone');ax.legend(ncol=3,fontsize=8);save(fig,3,'boundary_analysis')
#04 industrial decision profile (not a C++/paceval arithmetic difference)
fig,ax=plt.subplots(figsize=(8.8,4.35)); v=D.groupby('sample_id').decision.value_counts().unstack(fill_value=0)
for name,c in [('ACCEPT',TEAL),('REJECT',ORANGE),('REVIEW_BOUNDARY','#8b74ae')]:
 ax.plot(v.index,v.get(name,pd.Series(0,index=v.index)).values,label=name.replace('_',' ').title(),color=c,lw=1.7)
ax.set_xlabel('Adversarial input index (per guard)');ax.set_ylabel('Number of guards');ax.set_title('Industrial routing of boundary-sensitive constraint inputs');ax.legend(ncol=3,fontsize=8);save(fig,4,'decision_routing_profile')
#05 3d surface and 06 contour: both from actual paceval grid
pivot=S.pivot(index='y',columns='x',values='paceval_margin');xx=pivot.columns.to_numpy();yy=pivot.index.to_numpy();X,Y=np.meshgrid(xx,yy);Z=pivot.to_numpy()
fig=plt.figure(figsize=(9,5.7));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(X,Y,Z,cmap='coolwarm',linewidth=0,antialiased=True,rstride=2,cstride=2)
ax.plot_wireframe(X,Y,np.zeros_like(Z),rstride=7,cstride=7,color='#718096',alpha=.13)
ax.set(xlabel='Normalized x',ylabel='Normalized y',zlabel='Signed constraint margin',title='Elliptical guard: 3,721 paceval evaluations');fig.colorbar(surf,ax=ax,shrink=.65,pad=.11,label='Margin g(x,y,0)');save(fig,5,'elliptical_guard_3d')
fig,ax=plt.subplots(figsize=(7.7,5.6));c=ax.contourf(X,Y,Z,levels=32,cmap='coolwarm');ax.contour(X,Y,Z,levels=[0],colors='black',linewidths=2);fig.colorbar(c,ax=ax,label='Signed margin')
ax.set(xlabel='Normalized x',ylabel='Normalized y',title='Constraint decision boundary: g(x,y,0) = 0');ax.set_aspect('equal');save(fig,6,'elliptical_guard_contours')
# 07 False accept/reject metric by model family
v=D.groupby('family').decision.value_counts().unstack(fill_value=0);fig,ax=plt.subplots(figsize=(9,4.3));bottom=np.zeros(5)
for key,label,color in [('ACCEPT','Accept',TEAL),('REJECT','Reject',ORANGE),('REVIEW_BOUNDARY','Review','#8b74ae')]:
 values=v.get(key,pd.Series(0,index=v.index)).to_numpy();ax.bar(np.arange(5),values,bottom=bottom,label=label,color=color);bottom+=values
ax.set_xticks(range(5),['Threshold','Ellipse','Quadratic','Affine','Nonlinear']);ax.set_ylabel('Cases');ax.set_title('Decisions by mathematical guard family');ax.legend();save(fig,7,'family_decisions')
# 08 Review fraction by local boundary spacing index for exactly 1 family
m=D[D.family==1].groupby('sample_id').decision.apply(lambda a:(a=='REVIEW_BOUNDARY').mean())
fig,ax=plt.subplots(figsize=(9,4));ax.plot(m.index,m.values,color=TEAL,lw=1.5)
ax.set(xlabel='Sample index within guard',ylabel='Fraction classified REVIEW',title='Sensitivity of review outcomes to sampling around the boundary');ax.set_ylim(-.03,1.03);save(fig,8,'review_pattern')
print('PASS 8 figure pairs generated from original paceval CSV outputs')
