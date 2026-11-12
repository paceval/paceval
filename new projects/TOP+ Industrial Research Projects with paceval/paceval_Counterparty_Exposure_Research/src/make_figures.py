#!/usr/bin/env python3
"""Render industrial scientific figures solely from published paceval CSV outputs."""
from pathlib import Path
import csv,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]; out=root/'figures';out.mkdir(exist_ok=True)
def read(file):return list(csv.DictReader((root/'examples'/file).open()))
def save(n):plt.tight_layout();plt.savefig(out/f'{n}.png',dpi=175,bbox_inches='tight');plt.savefig(out/f'{n}.pdf',bbox_inches='tight');plt.close()
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'figure.figsize':(8.1,4.7)})
a=read('exposure_samples.csv');z=np.array([float(x['exposure_eur_m']) for x in a]);r=np.array([int(x['rule_id']) for x in a]);
plt.figure();plt.hist(z,bins=28,color='#167e91');plt.xlabel('Indicative exposure (EUR million)');plt.ylabel('Sampled updates');plt.title('Exposure distribution across the deterministic replay sample');save('01_sample_exposure_distribution')
m=read('rule_metrics.csv');fam=np.array([int(x['family']) for x in m]);means=np.array([float(x['mean_exposure_eur_m']) for x in m]);
plt.figure();plt.boxplot([means[fam==i] for i in range(1,6)],tick_labels=['Baseline','Stress','Quadratic','FX','Buffer']);plt.ylabel('Mean exposure (EUR million)');plt.title('Rule families produce different indicative exposure profiles');save('02_rule_family_exposure')
sc=read('stress_scenarios.csv');s=np.array([float(x['shock']) for x in sc]);
plt.figure();
for col,label in [('baseline_eur_m','Baseline'),('stressed_eur_m','Linear stress'),('quadratic_eur_m','Quadratic scenario'),('addon_eur_m','Buffer expression')]:plt.plot(s,[float(x[col]) for x in sc],label=label)
plt.xlabel('Dimensionless market shock');plt.ylabel('Indicative exposure (EUR million)');plt.title('Scenario responses computed with reusable paceval handles');plt.legend();save('03_market_stress_sensitivity')
surf=read('exposure_surface.csv');xx=np.array([float(x['mtm_eur_m']) for x in surf]).reshape(61,61);yy=np.array([float(x['collateral_eur_m']) for x in surf]).reshape(61,61);zz=np.array([float(x['exposure_eur_m']) for x in surf]).reshape(61,61)
fig=plt.figure(figsize=(9,6.2));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(xx,yy,zz,cmap='viridis',linewidth=0,antialiased=True,alpha=.97);ax.set_xlabel('Net MtM (EUR m)',labelpad=8);ax.set_ylabel('Collateral (EUR m)',labelpad=9);ax.set_zlabel('Exposure (EUR m)',labelpad=8);ax.set_title('3D collateral-adjusted exposure surface');ax.view_init(27,-55);save('04_exposure_surface_3d')
plt.figure(figsize=(8,5.2));cs=plt.contourf(xx,yy,zz,levels=20,cmap='viridis');plt.colorbar(cs,label='Indicative exposure (EUR million)');plt.contour(xx,yy,zz,levels=[0.000001],colors='white',linewidths=1);plt.xlabel('Net MtM (EUR million)');plt.ylabel('Collateral (EUR million)');plt.title('Collateral mitigation and the zero-exposure boundary');save('05_collateral_contour')
v=read('formula_revision.csv');shock=np.array([float(x['shock']) for x in v]);v1=[float(x['v1_exposure_eur_m']) for x in v];v2=[float(x['v2_exposure_eur_m']) for x in v]
plt.figure();plt.plot(shock,v1,label='Original v1');plt.plot(shock,v2,label='Controlled revision v2',ls='--');plt.xlabel('Dimensionless shock');plt.ylabel('Exposure (EUR million)');plt.title('Immutable formula versioning');plt.legend();save('06_immutable_formula_versioning')
plt.figure();plt.scatter([float(x['mtm_eur_m']) for x in a],[float(x['exposure_eur_m']) for x in a],c=[float(x['haircut']) for x in a],cmap='plasma',s=17);plt.colorbar(label='Collateral haircut');plt.xlabel('Net MtM (EUR million)');plt.ylabel('Indicative exposure (EUR million)');plt.title('Net MtM, collateral and haircut in the replay sample');save('07_haircut_scatter')
plt.figure();plt.scatter([float(x['collateral_eur_m']) for x in a],[float(x['exposure_eur_m']) for x in a],c=[float(x['shock']) for x in a],cmap='coolwarm',s=17);plt.colorbar(label='Dimensionless shock');plt.xlabel('Collateral (EUR million)');plt.ylabel('Indicative exposure (EUR million)');plt.title('Collateral and scenario shock in sampled updates');save('08_collateral_vs_exposure')
print('PASS 8 scientific figure pairs exported from paceval data')
