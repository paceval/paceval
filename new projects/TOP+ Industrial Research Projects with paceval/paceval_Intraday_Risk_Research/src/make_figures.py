#!/usr/bin/env python3
"""Render only graphs computed from released paceval CSV exports."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];ex=root/'examples';fig=root/'figures';fig.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'figure.dpi':115})
def data(n):return pd.read_csv(ex/n)
def save(n):plt.tight_layout(pad=2.4);plt.savefig(fig/(n+'.png'),dpi=180,bbox_inches='tight');plt.savefig(fig/(n+'.pdf'),bbox_inches='tight');plt.close()
a=data('risk_replay.csv');b=data('family_summary.csv');s=data('risk_surface.csv');t=data('stress_scenarios.csv');v=data('formula_revision.csv')
plt.figure(figsize=(8,4.4));plt.plot(a['update'],a['risk_eur_m'],linewidth=.9);plt.scatter(a.loc[a.limit_breach==1,'update'],a.loc[a.limit_breach==1,'risk_eur_m'],s=7,label='Illustrative limit exceedance');plt.title('Synthetic intraday risk replay');plt.xlabel('Market update index');plt.ylabel('Risk measure (EUR million)');plt.legend();save('01_intraday_replay')
plt.figure(figsize=(8,4.4));plt.hist(a.risk_eur_m,bins=38,edgecolor='white');plt.title('Distribution of risk measures across sampled updates');plt.xlabel('Risk measure (EUR million)');plt.ylabel('Sampled updates');save('02_risk_distribution')
plt.figure(figsize=(8,4.4));plt.bar(b.rule_id,b.mean_risk_eur_m);plt.title('Mean computed risk across 50 mathematical rules');plt.xlabel('Versioned rule ID');plt.ylabel('Mean risk measure (EUR million)');save('03_rule_family_risk')
from mpl_toolkits.mplot3d import Axes3D
x=sorted(s.w1_eur_m.unique());y=sorted(s.w2_eur_m.unique());xx,yy=np.meshgrid(x,y,indexing='ij');zz=s.risk_eur_m.values.reshape(len(x),len(y));f=plt.figure(figsize=(8,5.8));ax=f.add_subplot(111,projection='3d');surf=ax.plot_surface(xx,yy,zz,cmap='viridis',linewidth=0,antialiased=True);ax.set_xlabel('Factor 1 position (EUR m)',labelpad=7);ax.set_ylabel('Factor 2 position (EUR m)',labelpad=7);ax.set_zlabel('Risk measure (EUR m)',labelpad=7);ax.set_title('Two-factor portfolio risk surface');ax.view_init(elev=27,azim=-57);f.colorbar(surf,shrink=.65,pad=.13,label='Risk (EUR m)');save('04_risk_surface_3d')
plt.figure(figsize=(7.8,5));c=plt.contourf(xx,yy,zz,25,cmap='viridis');plt.colorbar(c,label='Risk measure (EUR million)');plt.xlabel('Factor 1 position (EUR m)');plt.ylabel('Factor 2 position (EUR m)');plt.title('Frozen-covariance risk contours');save('05_risk_contours')
plt.figure(figsize=(8,4.4));
for k in t.columns[1:]:plt.plot(t.shock,t[k],label=k.replace('_eur_m','').replace('_',' ').title())
plt.title('Shock-dependent mathematical risk functions');plt.xlabel('Synthetic scenario shock');plt.ylabel('Risk measure (EUR million)');plt.legend(fontsize=8);save('06_stress_scenarios')
plt.figure(figsize=(8,4.4));plt.plot(v.shock,v.version1_risk_eur_m,label='Original formula v1');plt.plot(v.shock,v.version2_risk_eur_m,label='Immutable revision v2',linestyle='--');plt.title('Controlled formula version change');plt.xlabel('Synthetic scenario shock');plt.ylabel('Risk measure (EUR million)');plt.legend();save('07_formula_versioning')
plt.figure(figsize=(8,4.4));counts=a.groupby('rule_id').limit_breach.sum();plt.bar(counts.index,counts.values);plt.title('Illustrative risk-limit exceedances by rule');plt.xlabel('Rule ID');plt.ylabel('Sampled threshold exceedances');save('08_risk_limit_alerts')
print('PASS: 8 scientific figures, PNG and vector PDF')
