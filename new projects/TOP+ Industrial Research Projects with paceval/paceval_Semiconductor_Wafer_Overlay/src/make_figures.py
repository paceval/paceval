#!/usr/bin/env python3
"""Render industrial/scientific figures from archived genuine paceval CSV outputs."""
import csv,math
from collections import defaultdict
from pathlib import Path
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
from matplotlib.tri import Triangulation
from matplotlib.colors import Normalize
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
RES=ROOT/'results'
C0='#027c87';C1='#ed7352';NAV='#132f46';BLUE='#476caa';GRAY='#657587';BG='#f8fafc';GOLD='#d6a34b'
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'axes.titleweight':'bold','axes.labelsize':10,
 'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white',
 'axes.edgecolor':'#b4c1ce','grid.color':'#dfe6ed','font.family':'DejaVu Sans'})

def data(f):
 with open(RES/f,newline='') as h:return list(csv.DictReader(h))
rows=data('wafer_grid_sample.csv');holds=data('holdout_results.csv');summ=data('wafer_summary.csv');coef=data('fitted_coefficients.csv')
for row in rows+holds:
 for k in row:
  if k not in ('version',):row[k]=float(row[k])
for s in summ:
 for k in s:
  if k!='version':s[k]=float(s[k])
def sub(lot=0,version='cubic_harmonic_v2'):
 return [r for r in rows if r['lotId']==lot and r['version']==version]
def vec(r,key):return np.array([v[key] for v in r],dtype=float)
def make(name,fn,w=9.2,h=6.0):
 f=plt.figure(figsize=(w,h),layout='constrained');fn(f)
 for suffix in ('png','pdf'):f.savefig(FIG/f'{name}.{suffix}',dpi=220)
 plt.close(f)
def wafer_outline(ax):
 ax.add_patch(Circle((0,0),150,fill=False,edgecolor=NAV,linewidth=1.4))
 ax.set_aspect('equal');ax.set_xlim(-160,160);ax.set_ylim(-160,160);ax.set_xlabel('Wafer x (mm)');ax.set_ylabel('Wafer y (mm)');ax.grid(alpha=.35)

# 01: architecture diagram -- not numerical output, explicitly conceptual.
def arch(f):
 ax=f.add_subplot(111);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
 titles=[('Metrology CSV','x / y / temperature\nmeasured overlay'),('Householder fit\n(C++ host)','train / holdout split\nmodel coefficients'),('paceval graphs','overlay maps\nresiduals / derivatives'),('Quality review','risk, margins,\nACCEPT / REVIEW / REJECT')]
 xs=[.025,.27,.52,.765]
 for x,(title,desc) in zip(xs,titles):
  rect=FancyBboxPatch((x,.39),.21,.23,boxstyle='round,pad=0.012,rounding_size=0.025',facecolor='#ecf5f8',edgecolor=C0,lw=1.7)
  ax.add_patch(rect);ax.text(x+.105,.53,title,ha='center',va='center',fontsize=12,fontweight='bold',color=NAV)
  ax.text(x+.105,.44,desc,ha='center',va='center',fontsize=9,color=GRAY)
 for a,b in zip(xs[:-1],xs[1:]):ax.add_patch(FancyArrowPatch((a+.22,.5),(b-.014,.5),arrowstyle='-|>',mutation_scale=16,color=C1,lw=2))
 ax.text(.5,.77,'Executed research architecture',ha='center',fontsize=18,color=NAV,fontweight='bold')
 ax.text(.5,.24,'Synthetic measurements | persistent paceval graphs | independent audit',ha='center',fontsize=11,color=GRAY)
make('01_research_workflow',arch,11,4)

def waferDx(f):
 ax=f.add_subplot(111);r=sub();a=ax.scatter(vec(r,'xMm'),vec(r,'yMm'),c=vec(r,'overlayDx'),s=55,cmap='viridis',edgecolors='none')
 wafer_outline(ax);f.colorbar(a,ax=ax,label='Predicted overlay dx (nm)',shrink=.83)
 ax.set_title('Cubic-harmonic overlay correction across wafer, lot 0')
make('02_overlay_dx_wafer',waferDx)

def vector(f):
 ax=f.add_subplot(111);r=sub();x=vec(r,'xMm');y=vec(r,'yMm');u=vec(r,'overlayDx');v=vec(r,'overlayDy');mag=np.hypot(u,v)
 a=ax.quiver(x[::3],y[::3],u[::3],v[::3],mag[::3],cmap='plasma',angles='xy',scale_units='xy',scale=.1,width=.003)
 wafer_outline(ax);f.colorbar(a,ax=ax,label='Predicted vector magnitude (nm)',shrink=.83)
 ax.set_title('Two-dimensional overlay correction vector field, lot 0')
make('03_overlay_vector_field',vector)

def hist(f):
 ax=f.add_subplot(111)
 for version,col,title in [('quadratic_v1',C1,'Quadratic baseline'),('cubic_harmonic_v2',C0,'Cubic + harmonic')]:
  s=[r['residualNorm'] for r in rows if r['version']==version]
  ax.hist(s,bins=np.linspace(0,3.1,41),histtype='step',linewidth=2,color=col,label=title)
 ax.set_xlabel('Residual magnitude (nm)');ax.set_ylabel('Sampled wafer records');ax.set_title('Residual distribution over ten wafer lots')
 ax.legend(frameon=False);ax.grid(axis='y',alpha=.3)
make('04_overlay_residual_histogram',hist)

def bars(f):
 ax=f.add_subplot(111);lots=np.arange(10);w=.35
 for i,(v,col) in enumerate([('quadratic_v1',C1),('cubic_harmonic_v2',C0)]):
  rr=sorted([s for s in summ if s['version']==v],key=lambda r:r['lotId'])
  ax.bar(lots+(i-.5)*w,[z['residualRmsNm'] for z in rr],width=w,color=col,label=v.replace('_',' '))
 ax.set_xticks(lots);ax.set_xticklabels([f'Lot {i}' for i in lots]);ax.set_ylabel('RMS residual (nm)')
 ax.set_title('Model-family differences across ten synthetic lots');ax.grid(axis='y',alpha=.35);ax.legend(frameon=False)
make('05_lot_residual_rms',bars)

def status(f):
 ax=f.add_subplot(111);versions=['quadratic_v1','cubic_harmonic_v2']
 for i,v in enumerate(versions):
  rr=[r for r in summ if r['version']==v];N=sum(r['rows'] for r in rr)
  a=sum(r['accept'] for r in rr)/N;b=sum(r['review'] for r in rr)/N;c=sum(r['reject'] for r in rr)/N
  ax.barh(i,100*a,color=C0,label='Accept' if not i else None)
  ax.barh(i,100*b,left=100*a,color=GOLD,label='Review' if not i else None)
  ax.barh(i,100*c,left=100*(a+b),color=C1,label='Reject' if not i else None)
  ax.text(100*a*.55,i,f'{a:.1%}',ha='center',va='center',color='white',weight='bold',fontsize=11)
 ax.set_xlim(0,100);ax.set_yticks(range(2));ax.set_yticklabels(['Quadratic v1','Cubic + harmonic v2']);ax.set_xlabel('Synthetic wafer records (%)')
 ax.set_title('Hypothetical quality categories, all grid records');ax.legend(ncol=3,loc='lower center',bbox_to_anchor=(.5,-.22),frameon=False)
make('06_quality_decision_share',status,9,5)

def surface(f):
 ax=f.add_subplot(111,projection='3d');r=sub();a=vec(r,'xMm');b=vec(r,'yMm');z=vec(r,'overlayDx')
 tri=Triangulation(a,b);surf=ax.plot_trisurf(tri,z,cmap='viridis',linewidth=.05,antialiased=True,alpha=.97)
 ax.set_title('Predicted overlay surface in 3D');ax.set_xlabel('Wafer x (mm)',labelpad=5);ax.set_ylabel('Wafer y (mm)',labelpad=5);ax.set_zlabel('dx (nm)',labelpad=7)
 ax.view_init(elev=26,azim=-58);f.colorbar(surf,ax=ax,shrink=.5,pad=.07,label='dx (nm)')
make('07_overlay_surface_3d',surface,10,7)

def jac(f):
 ax=f.add_subplot(111);r=sub();j=np.hypot(vec(r,'dDx_dU'),vec(r,'dDx_dV'))
 a=ax.scatter(vec(r,'xMm'),vec(r,'yMm'),c=j,cmap='magma',s=52,edgecolor='none')
 wafer_outline(ax);f.colorbar(a,ax=ax,label='||grad(dx)|| (nm / normalized coordinate)',shrink=.84)
 ax.set_title('Analytic overlay-correction sensitivity field')
make('08_spatial_sensitivity',jac)

def heat(f):
 ax=f.add_subplot(111);quad=sub(0,'quadratic_v1');enh=sub(0,'cubic_harmonic_v2');v=np.array([z['overlayDx']-q['overlayDx'] for z,q in zip(enh,quad)])
 a=ax.scatter(vec(enh,'xMm'),vec(enh,'yMm'),c=v,s=55,cmap='coolwarm',vmin=-max(abs(v)),vmax=max(abs(v)))
 wafer_outline(ax);f.colorbar(a,ax=ax,label='v2 minus v1, dx (nm)',shrink=.84)
 ax.set_title('Controlled overlay formula revision, lot 0')
make('09_version_difference_map',heat)

def uncertainty(f):
 ax=f.add_subplot(111);r=sub(0,'cubic_harmonic_v2')
 ax.scatter(vec(r,'waferMargin'),vec(r,'illustrativeUncertainty'),s=28,alpha=.6,color=C0)
 ax.set_xlabel('Wafer domain margin, normalized');ax.set_ylabel('Illustrative combined u (nm)')
 ax.set_title('First-order illustrative uncertainty versus wafer position');ax.grid(alpha=.4)
make('10_uncertainty_propagation',uncertainty)

def radial(f):
 ax=f.add_subplot(111)
 bins=np.linspace(0,150,8);centres=.5*(bins[1:]+bins[:-1]);
 for version,col in [('quadratic_v1',C1),('cubic_harmonic_v2',C0)]:
  s=[r for r in rows if r['version']==version]
  rr=np.hypot(vec(s,'xMm'),vec(s,'yMm'));res=vec(s,'residualNorm')
  rms=[np.sqrt(np.mean(res[(rr>=a)&(rr<b)]**2)) for a,b in zip(bins[:-1],bins[1:])]
  ax.plot(centres,rms,'o-',color=col,lw=2,label=version.replace('_',' '))
 ax.set_title('Wafer-radius dependence of the overlay residual');ax.set_xlabel('Radius (mm)');ax.set_ylabel('Sampled RMS residual (nm)');ax.grid(alpha=.4);ax.legend(frameon=False)
make('11_radial_residual_profile',radial)

def hold(f):
 ax=f.add_subplot(111)
 v0=[r for r in holds if r['version']=='quadratic_v1'];v1=[r for r in holds if r['version']=='cubic_harmonic_v2']
 ax.scatter(vec(v0,'tempC'),vec(v0,'residualNorm'),s=9,alpha=.19,color=C1,label='Quadratic v1')
 ax.scatter(vec(v1,'tempC'),vec(v1,'residualNorm'),s=9,alpha=.19,color=C0,label='Cubic + harmonic v2')
 ax.set_xlabel('Measurement temperature (°C)');ax.set_ylabel('Holdout residual magnitude (nm)')
 ax.set_title('Unseen metrology sites: overlay residual versus temperature');ax.grid(alpha=.25);ax.legend(frameon=False)
make('12_temperature_holdout_residual',hold)

def coeffig(f):
 ax=f.add_subplot(111)
 pp=defaultdict(list)
 for r in coef:
  if int(r['lotId'])==0 and r['axis']=='dx':pp[r['version']].append(float(r['coefficient']))
 labels=['1','u','v','u²','uv','v²','τ','τu','τv','u³','u²v','uv²','v³','H₁','H₂'];a=np.arange(15)
 ax.bar(a-.2,pp['quadratic_v1']+[0]*6,width=.4,color=C1,label='Quadratic v1')
 ax.bar(a+.2,pp['cubic_harmonic_v2'],width=.4,color=C0,label='Cubic + harmonic v2')
 ax.set_xticks(a);ax.set_xticklabels(labels);ax.set_ylabel('Fitted coefficient (nm)');ax.set_title('Declared formula coefficients, lot 0, x correction')
 ax.legend(frameon=False);ax.grid(axis='y',alpha=.3)
make('13_coefficient_versions',coeffig)

def clip(f):
 ax=f.add_subplot(111);r=sub(0,'cubic_harmonic_v2');a=ax.scatter(vec(r,'xMm'),vec(r,'yMm'),c=vec(r,'residualMargin'),s=50,cmap='RdYlGn',vmin=-1,vmax=1)
 wafer_outline(ax);f.colorbar(a,ax=ax,label='3.5σ - residual (nm)',shrink=.83)
 ax.set_title('Signed hypothetical overlay quality margin, lot 0')
make('14_quality_margin_wafer',clip)
print('Rendered 14 figures (PNG + vector PDF) from executed paceval result CSV files.')
