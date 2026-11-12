"""Rebuild WP032 scientific figures exclusively from actual paceval CSV outputs."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
root=Path(__file__).resolve().parents[1]
figdir=root/'figures';figdir.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/'examples'/'feature_replay.csv').open()))
surf=list(csv.DictReader((root/'examples'/'ecg_score_surface.csv').open()))
versions=list(csv.DictReader((root/'examples'/'formula_version_surface.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.labelsize':10})
def save(fig,name):
 fig.savefig(figdir/(name+'.png'),dpi=180,bbox_inches='tight',facecolor='white')
 fig.savefig(figdir/(name+'.pdf'),bbox_inches='tight',facecolor='white');plt.close(fig)
score=np.array([float(r['score']) for r in rows]);families=np.array([(int(r['rule_id'])-1)//10 for r in rows]);flags=np.array([int(r['review_flag']) for r in rows]);idx=np.arange(len(rows))
fig,ax=plt.subplots(figsize=(9,4));ax.plot(idx[:600],score[:600],lw=1,color='#137a95');ax.axhline(.65,color='#d9832a',ls='--',label='Research review threshold 0.65');ax.set(xlabel='Synthetic record index',ylabel='Dimensionless score',title='Repeated ECG-feature score evaluation');ax.legend();fig.tight_layout();save(fig,'01_feature_replay')
fig,ax=plt.subplots(figsize=(8,4));ax.hist(score,bins=42,color='#157f97',alpha=.85);ax.axvline(.65,color='#d9832a',ls='--');ax.set(xlabel='Dimensionless synthetic score',ylabel='Record count',title='Score distribution over 10,000 replayed feature vectors');fig.tight_layout();save(fig,'02_score_distribution')
fig,ax=plt.subplots(figsize=(9,4));ax.boxplot([score[families==f] for f in range(5)],tick_labels=['Linear','Interaction','Quadratic','Trigonometric','Log/exp'],patch_artist=True,boxprops={'facecolor':'#b8dee4'});ax.axhline(.65,color='#d9832a',ls='--');ax.set(ylabel='Dimensionless score',title='Five mathematical expression families');fig.tight_layout();save(fig,'03_rule_families')
x=np.array([float(r['rr_feature']) for r in surf]).reshape(61,61);y=np.array([float(r['qrs_feature']) for r in surf]).reshape(61,61);z=np.array([float(r['score']) for r in surf]).reshape(61,61)
fig=plt.figure(figsize=(9,5));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(x,y,z,cmap='viridis',linewidth=0,antialiased=True);ax.set(xlabel='Normalized RR-mean feature',ylabel='Normalized QRS-width feature',zlabel='Dimensionless score',title='paceval score surface: 3,721 evaluated inputs');ax.view_init(elev=27,azim=-125);fig.subplots_adjust(left=.01,right=.98,bottom=.07,top=.9);save(fig,'04_score_surface_3d')
fig,ax=plt.subplots(figsize=(8,5));h=ax.contourf(x,y,z,levels=21,cmap='viridis');fig.colorbar(h,ax=ax,label='Dimensionless score');ax.set(xlabel='Normalized RR-mean feature',ylabel='Normalized QRS-width feature',title='2D contours of the same paceval score surface');fig.tight_layout();save(fig,'05_score_contours')
fig,ax=plt.subplots(figsize=(8,4));vx=[float(r['rr_feature']) for r in versions];v1=[float(r['score_v1']) for r in versions];v2=[float(r['score_v2']) for r in versions];ax.plot(vx,v1,label='Original graph v1',lw=2);ax.plot(vx,v2,label='Revised graph v2',lw=2);ax.set(xlabel='Normalized RR-mean feature',ylabel='Dimensionless score',title='Controlled formula revision retains original handle');ax.legend();fig.tight_layout();save(fig,'06_formula_versions')
fig,ax=plt.subplots(figsize=(7,4));ax.bar(['Below synthetic\nreview threshold','At/above synthetic\nreview threshold'],[len(flags)-sum(flags),sum(flags)],color=['#137a95','#d9832a']);ax.set(ylabel='Record count',title='Research-only inspection flags, not medical alarms');fig.tight_layout();save(fig,'07_rule_flags')
fig,ax=plt.subplots(figsize=(8,4));thresholds=np.linspace(.4,.8,81);counts=[int(np.sum(score>=t)) for t in thresholds];ax.plot(thresholds,counts,color='#137a95',lw=2);ax.axvline(.65,color='#d9832a',ls='--');ax.set(xlabel='Synthetic score threshold',ylabel='Flagged synthetic records',title='Sensitivity of postprocessing flag counts to threshold');fig.tight_layout();save(fig,'08_threshold_sweep')
print('PASS 8 result figures regenerated from paceval CSV outputs')
