#!/usr/bin/env python3
"""Regenerate all eight scientific figures from released paceval CSV results."""
from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; EX=ROOT/'examples'; OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
rec=pd.read_csv(EX/'quality_records.csv');su=pd.read_csv(EX/'score_summary.csv');s=pd.read_csv(EX/'quality_surface.csv');v=pd.read_csv(EX/'formula_versions.csv')
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(stem):
 plt.savefig(OUT/(stem+'.png'),dpi=180,bbox_inches='tight',pad_inches=.25)
 plt.savefig(OUT/(stem+'.pdf'),bbox_inches='tight',pad_inches=.25)
 plt.close()
fig,ax=plt.subplots(figsize=(9,4));ax.bar(['Execution graphs','Input records','Batch checks','Surface points'],[51,10000,1600,3721]);ax.set_title('Executed mathematical workload');ax.set_ylabel('Count');ax.grid(axis='y',alpha=.25);save('01_executed_scope')
fig,ax=plt.subplots(figsize=(9,4));ax.hist(rec['score'],bins=35,edgecolor='white');ax.axvline(.6,color='darkred',ls='--',label='Review threshold = 0.60');ax.set(xlabel='Dimensionless risk proxy',ylabel='Number of records',title='Score distribution from 10,000 paceval evaluations');ax.legend();save('02_score_distribution')
fig,ax=plt.subplots(figsize=(9,4));grp=rec.groupby('score_id')['inspect_flag'].mean();ax.bar(np.arange(1,51),grp);ax.set(xlabel='Versioned model ID',ylabel='Fraction routed to inspection',title='Inspection policy response across 50 score models');ax.set_ylim(0,1);save('03_inspection_by_model')
fig,ax=plt.subplots(figsize=(9,4));x=np.arange(5);d=su.groupby('family').agg({'inspection_rate':'mean','label_rate':'mean'});ax.bar(x-.18,d.inspection_rate,width=.36,label='Inspection flag');ax.bar(x+.18,d.label_rate,width=.36,label='Synthetic defect labels');ax.set_xticks(x,[f'Family {i}' for i in range(1,6)]);ax.set(ylabel='Fraction of cases',title='Illustrative policy decisions and synthetic labels');ax.legend();save('04_family_profile')
X=s.pivot(index='pressure_dev',columns='temperature_dev',values='score');xx=X.columns.to_numpy();yy=X.index.to_numpy();Z=X.to_numpy()
fig=plt.figure(figsize=(9,5.5));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(*np.meshgrid(xx,yy),Z,cmap='viridis',linewidth=0,antialiased=True);fig.colorbar(surf,ax=ax,pad=.1,shrink=.68,label='Dimensionless risk proxy');ax.set(xlabel='Temperature deviation',ylabel='Pressure deviation',zlabel='Score',title='paceval score surface (3,721 evaluations)');ax.view_init(25,-57);save('05_quality_surface_3d')
fig,ax=plt.subplots(figsize=(8,5));c=ax.contourf(xx,yy,Z,levels=20,cmap='viridis');fig.colorbar(c,ax=ax,label='Score');if_contour=ax.contour(xx,yy,Z,levels=[.6],colors=['tomato'],linewidths=2);ax.clabel(if_contour,inline=True,fmt={.6:'Inspection threshold'});ax.set(xlabel='Temperature deviation',ylabel='Pressure deviation',title='Same score surface: process operating map');save('06_quality_contours')
fig,ax=plt.subplots(figsize=(9,4));ax.plot(v.temperature_dev,v.score_version_1,label='Version 1');ax.plot(v.temperature_dev,v.score_version_2,label='Version 2',ls='--');ax.axhline(.6,color='grey',lw=1,ls=':');ax.set(xlabel='Temperature deviation',ylabel='Score',title='Controlled formula revision with immutable graph handles');ax.legend();save('07_versioned_scores')
fig,ax=plt.subplots(figsize=(9,4));rec['bin']=pd.cut(rec.score,bins=np.linspace(0,1,11),include_lowest=True);z=rec.groupby('bin',observed=False).agg(label_rate=('synthetic_defect_label','mean'),count=('score','size'));ax.plot(np.linspace(.05,.95,10),z.label_rate,marker='o',label='Synthetic label frequency');ax.plot([0,1],[0,1],ls=':',color='grey',label='Identity (not fitted)');ax.set(xlabel='Score-bin center',ylabel='Observed synthetic-label fraction',title='Illustrative diagnostic: scores are not calibrated scrap probabilities');ax.legend();save('08_label_diagnostics')
print('Created 8 figure pairs from paceval datasets')
