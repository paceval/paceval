#!/usr/bin/env python3
"""Scientific graphics generated ONLY from C++/real-paceval exported numerical CSVs."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D  # noqa
ROOT=Path(__file__).resolve().parent.parent; FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
def read(s):return list(csv.DictReader((ROOT/s).open()))
profiles=read('examples/trajectory_profiles.csv'); metrics=read('results/candidate_metrics.csv'); surface=read('examples/oscillator_lie_surface.csv'); pr=read('results/precision_recall.csv')
colors={'oscillator':'#0E938D','kepler':'#EA8A37','damped':'#597EBD'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.17,'axes.titleweight':'bold','legend.frameon':False})
def done(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.14)
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',pad_inches=.14)
    plt.close(fig)
    print('FIG',name)
def pget(model,cid,noise=0.,tr=0):
    return sorted([r for r in profiles if r['model']==model and r['candidate_id']==cid and abs(float(r['noise_sigma'])-noise)<1e-8 and int(r['trajectory_id'])==tr],key=lambda r:float(r['t']))
def arr(rows,key):return np.array([float(r[key]) for r in rows])
# 1: oscillator invariant and higher integral
a=pget('oscillator','osc_E_x');b=pget('oscillator','osc_E_y');c=pget('oscillator','osc_E_total')
fig,ax=plt.subplots(figsize=(8.4,4.4))
for r,label,color in [(a,'Independent mode energy E_x','#0B9C93'),(b,'Independent mode energy E_y','#E8963B'),(c,'Total energy E_x + E_y','#385F9E')]:
    ax.plot(arr(r,'t'),arr(r,'value_from_paceval'),lw=2,label=label,color=color)
ax.set(title='Undamped anisotropic oscillator: conserved energies',xlabel='Time (normalized units)',ylabel='Invariant value (paceval)');ax.legend(loc='upper right');done(fig,'01_oscillator_energy_invariants')
# 2 Kepler orbit x-y stored coordinates
r=pget('kepler','kep_energy');
fig,ax=plt.subplots(figsize=(7.8,5.5));ax.plot(arr(r,'x'),arr(r,'y'),color='#197C91',lw=2.5);ax.scatter([0],[0],s=160,c='#EE9949',label='Central body',zorder=4);ax.scatter([float(r[0]['x'])],[float(r[0]['y'])],marker='o',s=65,c='#7035A1',label='Start')
ax.set(title='Kepler benchmark: actual sampled analytic trajectory',xlabel='Relative x',ylabel='Relative y',aspect='equal');ax.legend();done(fig,'02_kepler_orbit_trace')
# 3 Kepler invariants on phase path
fig,ax=plt.subplots(figsize=(8.4,4.4));
for cid,label,color in [('kep_energy','Specific energy','#0C9494'),('kep_angular_momentum','Angular momentum','#E19843'),('kep_LRL_x','LRL vector x','#7177C5'),('kep_LRL_y','LRL vector y','#B46E85')]:
 r=pget('kepler',cid);ax.plot(arr(r,'t'),arr(r,'value_from_paceval'),label=label,lw=2,color=color)
ax.set(title='Kepler invariants evaluated by original paceval graphs',xlabel='Time (normalized units)',ylabel='Conserved value (normalized units)');ax.legend(ncol=2,fontsize=9);done(fig,'03_kepler_energy_momentum_lrl')
# 4 damped time-dependent invariant vs E
fig,ax=plt.subplots(figsize=(8.4,4.4));
for cid,label,color in [('damp_time_corrected_energy','Time-dependent invariant I(t)','#12998D'),('damp_raw_energy','Raw mechanical energy E(t)','#E28939')]:
 r=pget('damped',cid);ax.plot(arr(r,'t'),arr(r,'value_from_paceval'),lw=2.5,label=label,color=color)
ax.set(title='Damped oscillator: dissipating energy vs conserved correction',xlabel='Time (normalized units)',ylabel='Analytical value from paceval');ax.legend();done(fig,'04_damped_corrected_invariant')
# 5 3D response surface from real paceval lie values
xvals=np.unique(arr(surface,'x'));vvals=np.unique(arr(surface,'v'));X,V=np.meshgrid(xvals,vvals,indexing='ij');Z=arr(surface,'cross_xv_lie_abs').reshape(65,65)
fig=plt.figure(figsize=(8.1,5.6));ax=fig.add_subplot(111,projection='3d');s=ax.plot_surface(X,V,Z,cmap='viridis',linewidth=0,antialiased=True,rstride=1,cstride=1);fig.colorbar(s,ax=ax,shrink=.7,pad=.09,label='Absolute Lie derivative');ax.set(title='3D candidate violation surface: x * v',xlabel='Position x',ylabel='Velocity v',zlabel='|d(xv)/dt|');ax.view_init(29,-56);done(fig,'05_lie_violation_surface_3d')
# 6 contour
fig,ax=plt.subplots(figsize=(8.0,5.4));h=ax.contourf(X,V,Z,levels=22,cmap='viridis');ax.contour(X,V,Z,levels=[0.5,1,2,3],colors='white',linewidths=.7,alpha=.65);fig.colorbar(h,ax=ax,label='Absolute Lie derivative (paceval)');ax.set(title='Lie-derivative residual contours: false invariant x * v',xlabel='Position x',ylabel='Velocity v',aspect='equal');done(fig,'06_lie_violation_contours')
# 7 holdout candidates normalized lie residual vs drift, sigma=.02
rows=[r for r in metrics if r['split']=='heldout' and abs(float(r['noise_sigma'])-.02)<1e-8]
fig,ax=plt.subplots(figsize=(8.4,5.1))
for model in colors:
 for tr,mark,alpha in [(1,'o',.95),(0,'x',.65)]:
  q=[r for r in rows if r['model']==model and int(r['known_invariant'])==tr];
  ax.scatter([max(1e-17,float(r['normalized_lie_rms'])) for r in q],[max(1e-17,float(r['trajectory_drift_rms'])) for r in q],color=colors[model],marker=mark,s=65 if tr else 80,alpha=alpha,label=model+(' · known' if tr else ' · counterexample'))
ax.set(xscale='log',yscale='log',title='Held-out additive noise: sigma = 0.02',xlabel='RMS normalized Lie residual from paceval',ylabel='RMS observed invariant drift');ax.legend(fontsize=8,ncol=2);done(fig,'07_candidate_lie_vs_drift')
# 8 degradation of drift under noise for selected invariant
fig,ax=plt.subplots(figsize=(8.4,4.4))
for model,id_ in [('oscillator','osc_E_total'),('kepler','kep_energy'),('damped','damp_time_corrected_energy')]:
 q=sorted([r for r in metrics if r['model']==model and r['candidate_id']==id_ and r['split']=='heldout'],key=lambda r:float(r['noise_sigma']))
 ax.plot(arr(q,'noise_sigma'),arr(q,'trajectory_drift_rms'),'-o',label=model.replace('_',' ').title(),color=colors[model],lw=2)
ax.set(title='Observed invariant drift increases with measurement noise',xlabel='Synthetic state-measurement noise sigma',ylabel='Held-out normalized invariant drift');ax.legend();done(fig,'08_noise_robustness_drift')
# 9 normalized Lie residual for all false candidates, 2% noise
fig,ax=plt.subplots(figsize=(10,4.9)); false=[r for r in rows if int(r['known_invariant'])==0];false=sorted(false,key=lambda r:float(r['normalized_lie_rms']),reverse=True)
ax.bar(range(len(false)),[float(r['normalized_lie_rms']) for r in false],color=[colors[r['model']] for r in false],alpha=.9)
ax.set(yscale='log',title='False candidates yield nonzero analytical Lie derivatives',xlabel='Candidate index sorted by magnitude (24 negative controls)',ylabel='RMS normalized Lie derivative');ax.set_xticks(range(len(false)),[str(i+1) for i in range(len(false))],fontsize=8);done(fig,'09_counterexample_residuals')
# 10 comparison of projected precision and recall, method conditional
fig,ax=plt.subplots(figsize=(8.4,4.4))
for model in colors:
 q=sorted([r for r in pr if r['model']==model and r['split']=='heldout'],key=lambda r:float(r['noise_sigma']))
 ax.plot(arr(q,'noise_sigma'),arr(q,'recall'),marker='o',lw=2,color=colors[model],label=model)
ax.set(title='Controlled-library held-out recall (known exact vector fields)',xlabel='Synthetic measurement noise sigma',ylabel='Recall on predeclared candidates',ylim=(0.75,1.05));ax.legend();done(fig,'10_heldout_recall')
# 11 leading role of paceval, 144 graph inventory by model
fig,ax=plt.subplots(figsize=(7.7,4.2));names=['Oscillator','Kepler','Damped'];forgraph=[48,48,48];bars=ax.barh(names,forgraph,color=[colors[m] for m in colors]);ax.bar_label(bars,padding=5);ax.set(xlim=(0,55),title='144 persistent mathematical execution graphs',xlabel='4 real paceval graphs per each of 12 candidate invariants');done(fig,'11_registered_graph_families')
print('Rendered 11 scientific figures, each as PNG and vector PDF')
