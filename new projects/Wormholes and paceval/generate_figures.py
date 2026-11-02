"""Recreate figures from the cited candidate model and run log. Python visualizations only; paceval was used for the underlying research run."""
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid
import csv
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'assets'; OUT.mkdir(exist_ok=True)
a=1.7573959995777182; c=1.9935043450750545
factor=1+np.cos(a)**2

def q(r): return (r-1)/r
def U(r):
 x=q(r);return x+x**3/((1+x*x)*factor)
def Up(r):
 x=q(r);return 1+(3*x*x+x**4)/((1+x*x)**2*factor)
def b(r): return (1+q(r)*U(r))/r
def bp(r):
 x=q(r); return ((U(r)+x*Up(r))/r**2)/r - (1+x*U(r))/r**2
# Verified derivative by finite difference below.
def phi(r): return -c/r
def phip(r): return c/r**2
def phipp(r): return -2*c/r**3
def nec8(r): return bp(r)/r**2-b(r)/r**3+2*(1-b(r)/r)*phip(r)/r
def Rrad(r): return (1-b(r)/r)*(phipp(r)+phip(r)**2) - (bp(r)*r-b(r))/(2*r*r)*phip(r)
def Rang(r): return (1-b(r)/r)*phip(r)/r
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':15,'axes.labelsize':11,'figure.dpi':145,'savefig.dpi':165})
def save(fn):plt.savefig(OUT/fn,bbox_inches='tight',facecolor='white');plt.close()
# Figure 1: copy editorial rendering, explicitly schematic
from PIL import Image
# Figure 1 is an editorial illustration; it is intentionally preserved from the archive.

# Figure 2: transcribed run data, not synthetic points. Read local CSV.
with (ROOT/'pareto_points.csv').open(newline='',encoding='utf-8') as fp:
 values=[(int(row['rank']),float(row['negative_nec_radial_metric']),float(row['max_static_tidal_component'])) for row in csv.DictReader(fp)]
assert len(values)==19, values
values.sort()
fig,ax=plt.subplots(figsize=(9,5.1));x=np.array([v[1] for v in values]);y=np.array([v[2] for v in values]);ax.plot(x,y,'-o',linewidth=1.6,markersize=4,color='#2369a4');ax.scatter([x[0]],[y[0]],s=130,c='#ef8c3a',zorder=5,label='Minimum NEC metric');ax.scatter([x[-1]],[y[-1]],s=130,c='#21866a',zorder=5,label='Minimum static tidal metric');ax.set(xlabel='Negative radial NEC metric (lower is better)',ylabel='Max. sampled static tidal curvature (lower is better)',title='Sampled multi-objective Pareto front');ax.legend();ax.grid(alpha=.25);fig.text(.5,-.01,'19 non-dominated solutions among 24 fine-grid evaluated candidates (preview subset; not globally optimal).',ha='center',fontsize=9);save('02_pareto_front.png')
# Figure 3: spatial embedding, both surfaces on identical scales; lower panel exposes their difference.
s=np.linspace(0,np.sqrt(11),1250)
rr=1+s*s
qv=(rr-1)/rr
up=qv+qv**3/((1+qv*qv)*(1+np.cos(a)**2))
bpv=(1+qv*up)/rr
bev=1/rr
def embedding_height(shape):
 derivative=np.empty_like(s)
 derivative[1:]=2*s[1:]*np.sqrt(shape[1:]/(rr[1:]-shape[1:]))
 derivative[0]=np.sqrt(2) # Both b'(1)=-1. Endpoint limit dz/ds=√2.
 return cumulative_trapezoid(derivative,s,initial=0)
zp=embedding_height(bpv); ze=embedding_height(bev)
fig=plt.figure(figsize=(15,8.5),layout='constrained')
gs=fig.add_gridspec(2,2,height_ratios=[1.65,1],hspace=.1)
theta=np.linspace(0,2*np.pi,105); rp=rr[::9]; tt=theta[::2]
xx=rp[:,None]*np.cos(tt)[None,:]; yy=rp[:,None]*np.sin(tt)[None,:]
for i,(name,zz,color) in enumerate([('paceval candidate',zp,'#286b97'),('Ellis special case',ze,'#6d7482')]):
 ax=fig.add_subplot(gs[0,i],projection='3d')
 for sign in [-1,1]:
  ax.plot_surface(xx,yy,sign*zz[::9,None],color=color,alpha=.8,linewidth=0,antialiased=True,shade=True)
 ax.set(xlim=(-12,12),ylim=(-12,12),zlim=(-4.4,4.4),xlabel='$x/r_0$',ylabel='$y/r_0$',zlabel='$z/r_0$')
 ax.set_title(name+f'  |  $z(12)={zz[-1]:.3f}$',fontsize=13,pad=8)
 ax.set_box_aspect((1,1,.65));ax.view_init(elev=21,azim=-59)
ax=fig.add_subplot(gs[1,:]);ax.plot(rr,zp,label='paceval embedding height $z(r)$',lw=2.2,color='#286b97');ax.plot(rr,ze,label='Ellis embedding height $z(r)$',lw=2.2,color='#6d7482',ls='--')
ax.set(xlabel='Areal radius $r/r_0$',ylabel='Embedding height $z/r_0$');ax.grid(alpha=.25)
ax2=ax.twinx();ax2.plot(rr,zp-ze,color='#d17a26',lw=2,label='Difference $\\Delta z(r)$');ax2.set_ylabel('Difference $\\Delta z/r_0$',color='#b4641b');ax2.tick_params(axis='y',labelcolor='#b4641b')
lines=ax.get_lines()+ax2.get_lines();ax.legend(lines,[ln.get_label() for ln in lines],loc='upper left',fontsize=9)
fig.suptitle('Computed equatorial spatial embeddings: paceval vs. Ellis',fontsize=18,fontweight='bold')
fig.text(.5,-.005,'Same throat radius $r_0=1$ and range $1\\leq r\\leq12$. Constant-time Euclidean embeddings; $z(1)=0$. Not full spacetime.',ha='center',fontsize=10)
save('03_embedding_comparison.png')
# Figure 4: computation workflow drawn as graph
fig,ax=plt.subplots(figsize=(11,3.7));ax.set_xlim(0,11);ax.set_ylim(0,3.6);ax.axis('off')
blocks=[(.7,'Symbolic search','U(q), V(q)'),(3.1,'Text expressions','b, b′, Φ, NEC'),(5.5,'paceval handles','Reusable graph'),(7.9,'Batch evaluation','Radial samples'),(10.0,'Verification','TINC bounds')]
for xx,lab,sub in blocks:
 ax.text(xx,1.95,lab,ha='center',va='center',fontsize=10.2,fontweight='bold',bbox=dict(boxstyle='round,pad=.8',fc='#e9f3fa',ec='#397ca7',lw=1.5))
 ax.text(xx,1.2,sub,ha='center',fontsize=9)
for i in range(4):
 ax.annotate('',xy=(blocks[i+1][0]-.85,2),xytext=(blocks[i][0]+.85,2),arrowprops={'arrowstyle':'->','color':'#256f9d','lw':2})
ax.text(5.5,3.15,'From explicit mathematics to reusable numerical evaluation',fontsize=15,ha='center',fontweight='bold');ax.text(5.5,.35,'Symbolic differentiation and evolutionary selection are implemented by the research application, not attributed to the paceval engine.',fontsize=9,ha='center');save('04_computation_workflow.png')
# Figure 5: semantic illustrative demo, no unsupported magnitudes
fig,ax=plt.subplots(figsize=(10,4));rr=np.linspace(1.05,4,500);vv=nec8(rr);ax.plot(rr,vv,color='#225c97',lw=2,label='Computed 8π(ρ + pᵣ) from reported candidate');idx=np.linspace(0,len(rr)-1,18,dtype=int);ax.scatter(rr[idx],vv[idx],s=22,c='#eb8b36',zorder=3,label='Illustrative sampling locations (not the run log grid)');ax.axhline(0,c='#333',lw=.8);ax.set(xlabel='Dimensionless radius r / r₀',ylabel='8π(ρ + pᵣ)',title='Pointwise verification vs. continuous-domain verification');ax.grid(alpha=.25);ax.legend(loc='lower right',fontsize=9);fig.text(.5,-.005,'Actual reported TINC bounds are not plotted: per-point lower/upper values were not supplied. No continuum enclosure is implied.',fontsize=9,ha='center');save('05_tinc_scope.png')
# Figure 6: actual model-derived physics profiles
fig,axes=plt.subplots(1,2,figsize=(11,4.2));r=np.linspace(1.0001,8,850);axes[0].plot(r,nec8(r),c='#275a92',lw=1.8,label='paceval candidate');axes[0].plot(r,-2/r**4,c='#78818b',ls='--',lw=1.6,label='Ellis b=1/r, Φ=0');axes[0].axhline(0,c='black',lw=.7);axes[0].set(xlabel='Radius r / r₀',ylabel='8π(ρ + pᵣ)',title='Radial NEC-related quantity');axes[0].legend(fontsize=9);axes[1].plot(r,np.abs(Rrad(r)),label='|R₍ₜᵣₜᵣ₎|',lw=1.8);axes[1].plot(r,np.abs(Rang(r)),label='|R₍ₜθₜθ₎|',lw=1.8);axes[1].set(xlabel='Radius r / r₀',ylabel='Absolute static orthonormal component',title='Selected tidal-curvature components');axes[1].legend(fontsize=9);[ax.grid(alpha=.25) for ax in axes];fig.suptitle('Local diagnostics computed from the published candidate formula',fontsize=14);fig.tight_layout();save('06_physics_diagnostics.png')
print('Created assets:',[f.name for f in OUT.glob('*.png')]);print('Pareto count',len(values),'bprime throat approx',bp(np.array([1.0])),'radial value',Rrad(np.array([1.])))
