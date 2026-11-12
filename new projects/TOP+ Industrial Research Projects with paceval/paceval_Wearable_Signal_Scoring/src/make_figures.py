#!/usr/bin/env python3
"""Create publication graphics only from the recorded paceval SDK CSV outputs."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
ROOT=Path(__file__).resolve().parents[1];EX=ROOT/'examples';FIG=ROOT/'figures'
FIG.mkdir(exist_ok=True)
TEAL='#087e8b'; CORAL='#e65746'; PURPLE='#695c91'; GREY='#506579'; YELLOW='#e3a145'
plt.rcParams.update({'font.size':10,'axes.labelcolor':'#23364d','axes.titlesize':12,'axes.titleweight':'bold','axes.edgecolor':'#c2cbd3','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
def save(fig,stem):
 fig.savefig(FIG/(stem+'.png'),dpi=210,bbox_inches='tight')
 fig.savefig(FIG/(stem+'.pdf'),bbox_inches='tight')
 plt.close(fig)
def rows(name):return list(csv.DictReader((EX/name).open()))
def arr(rs,k):return np.array([float(r[k]) for r in rs])
R=rows('wearable_feature_windows.csv')
# 1: raw recorded 8-second PPG and accelerometer trace
raw=rows('synthetic_trace_3.csv');t=arr(raw,'time_s');fig,ax=plt.subplots(figsize=(9.5,4.6))
ax.plot(t,arr(raw,'ppg_normalized')-np.mean(arr(raw,'ppg_normalized')),color=CORAL,lw=1.7,label='PPG AC (normalized)')
ax.plot(t,arr(raw,'acc_x_g'),color=TEAL,lw=1.0,alpha=.82,label='IMU x acceleration (g)')
ax.set(xlabel='Elapsed time (s)',ylabel='Recorded synthetic signal',title='Synthetic optical and motion signals (8-second window)');ax.legend(loc='upper right',frameon=False);ax.grid(alpha=.14);fig.tight_layout();save(fig,'01_synthetic_ppg_imu_trace')
# 2: score replay over time (downsample by 5)
fig,ax=plt.subplots(figsize=(9.5,4.6));ids=arr(R,'window_id');sc=arr(R,'score');ax.plot(ids[::5],sc[::5],color=TEAL,lw=.8);ax.axhline(.65,color=CORAL,ls='--',lw=1.2,label='Illustrative review threshold');ax.set(xlabel='Deterministic synthetic window ID',ylabel='Dimensionless mathematical score',title='Wearable scoring across 10,000 synthetic windows');ax.set_ylim(0,1);ax.legend(frameon=False);ax.grid(alpha=.14);fig.tight_layout();save(fig,'02_scoring_replay')
# 3: score distribution
fig,ax=plt.subplots(figsize=(9.2,4.4));ax.hist(sc,bins=52,color=TEAL,alpha=.89,edgecolor='white',linewidth=.3);ax.axvline(.65,color=CORAL,ls='--',lw=2,label='Example screen flag threshold');ax.set(xlabel='Dimensionless score',ylabel='Window count',title='Computed score distribution');ax.legend(frameon=False);fig.tight_layout();save(fig,'03_score_distribution')
# 4/5: 3D + contour of actual paceval-evaluated surface
s=rows('signal_quality_surface.csv');x=arr(s,'normalized_motion').reshape(61,61);y=arr(s,'periodicity').reshape(61,61);z=arr(s,'score').reshape(61,61)
fig=plt.figure(figsize=(8.6,6.2));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(x,y,z,cmap='viridis',linewidth=0,antialiased=True);ax.set(xlabel='Normalized motion',ylabel='PPG periodicity proxy',zlabel='Quality-formula score');ax.set_title('Actual paceval score surface: motion and periodicity',pad=16);ax.view_init(elev=28,azim=-55);fig.subplots_adjust(left=.03,right=.9,top=.9,bottom=.07);save(fig,'04_quality_score_surface_3d')
fig,ax=plt.subplots(figsize=(7.6,5.7));cf=ax.contourf(x,y,z,levels=24,cmap='viridis');ax.contour(x,y,z,levels=12,colors='#14314b',linewidths=.38,alpha=.42);fig.colorbar(cf,ax=ax,label='Mathematical score');ax.set(xlabel='Normalized motion',ylabel='PPG periodicity proxy',title='Computed motion-periodicity score contours');fig.tight_layout();save(fig,'05_quality_score_contours')
# 6: five families actual proportions flagged
families=['Activity','Optical quality','Motion-aware','Trigonometric','Log-exp'];family=[np.array([int(r['formula_id']) for r in R])//10] # compute robust via (ID-1)//10
family=np.array([(int(r['formula_id'])-1)//10 for r in R]);counts=[]
for i in range(5):counts.append(int(np.sum((family==i)&(sc>=.65))))
fig,ax=plt.subplots(figsize=(9,4.6));bars=ax.bar(families,counts,color=[TEAL,CORAL,PURPLE,YELLOW,GREY]);ax.set(ylabel='Flagged synthetic windows',title='Technical threshold results by model family');ax.tick_params(axis='x',rotation=13);ax.bar_label(bars,padding=3);fig.tight_layout();save(fig,'06_formula_family_thresholds')
# 7: version revision
v=rows('formula_version_trace.csv');fig,ax=plt.subplots(figsize=(8.8,4.7));ax.plot(arr(v,'normalized_acc'),arr(v,'score_v1'),label='Version 1, unchanged handle',lw=2,color=TEAL);ax.plot(arr(v,'normalized_acc'),arr(v,'score_v2'),label='Version 2, new handle',lw=2,color=CORAL,ls='--');ax.set(xlabel='Normalized acceleration feature',ylabel='Dimensionless score',title='Controlled mathematical formula revision');ax.legend(frameon=False);ax.grid(alpha=.15);fig.tight_layout();save(fig,'07_versioned_formula_response')
# 8: physics-independent feature scatter
fig,ax=plt.subplots(figsize=(8.8,5));idx=np.arange(0,len(R),4);dots=ax.scatter(arr(R,'acc_rms_g')[idx],arr(R,'ppg_periodicity')[idx],c=sc[idx],s=6,cmap='viridis',alpha=.7);fig.colorbar(dots,ax=ax,label='Score for selected formula');ax.set(xlabel='Dynamic acceleration RMS (g)',ylabel='PPG autocorrelation peak (unitless)',title='Recorded signal-derived features and mathematical scores');fig.tight_layout();save(fig,'08_feature_scatter')
print('PASS: eight reproducible PNG and vector-PDF scientific figures')
