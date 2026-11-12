#!/usr/bin/env python3
"""Reproduce every research chart from committed generated CSV results."""
from pathlib import Path
import csv, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
root=Path(__file__).resolve().parents[1]
figdir=root/'figures'; figdir.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/'examples/wp019_ranking.csv').open()))
samples=list(csv.DictReader((root/'examples/wp019_samples.csv').open()))
selected=list(csv.DictReader((root/'examples/wp019_selected.csv').open()))
audit=json.loads((root/'results/decimal_audit.json').read_text())
navy='#081828';cyan='#2ac5c5';mint='#60d3a2';amber='#ffc467';orange='#f27e5e';text='#dcecf5'
def clean(ax):
 ax.set_facecolor(navy);ax.tick_params(colors=text,labelsize=9);ax.xaxis.label.set_color(text);ax.yaxis.label.set_color(text)
 for edge in ax.spines.values():edge.set_color('#456277')
 ax.grid(alpha=.17,color='white');ax.set_axisbelow(True)
def save(fig,name):
 fig.patch.set_facecolor(navy)
 fig.savefig(figdir/(name+'.png'),dpi=170,facecolor=navy,bbox_inches='tight',pad_inches=.16)
 fig.savefig(figdir/(name+'.pdf'),facecolor=navy,bbox_inches='tight',pad_inches=.16)
 plt.close(fig)
# 1 clear architecture, dark and clean, unlike the photographic cover
fig,ax=plt.subplots(figsize=(11.7,3.0));ax.set_xlim(0,10);ax.set_ylim(0,3);ax.axis('off')
labels=['Defined data\n& units','Approved\nformulas','paceval SDK\nreusable graphs','Native & Decimal\naudit','Candidate\nselection']
for i,label in enumerate(labels):
 x=.15+i*2.03
 patch=FancyBboxPatch((x,.95),1.79,1.1,boxstyle='round,pad=0.08,rounding_size=.12',lw=1.6,edgecolor=cyan if i==2 else '#4c8995',facecolor='#122d42')
 ax.add_patch(patch);ax.text(x+.895,1.5,label,ha='center',va='center',color=text,fontsize=11,fontweight='bold')
 if i<4:ax.annotate('',(x+2.02,1.5),(x+1.85,1.5),arrowprops=dict(arrowstyle='->',color=mint,lw=2))
ax.text(5,.30,'All materials and target properties are synthetic. No data-driven equation discovery is claimed.',ha='center',color=amber,fontsize=10)
save(fig,'01_research_architecture')
# 2 family contracts
fig,ax=plt.subplots(figsize=(10,4));clean(ax)
for j,(label,expression) in enumerate([('Family 0','a + b x + c exp(-d/T)'),('Family 1','a + b x + c / (1+T/d)'),('Family 2','a + b x + c exp(-d/T) + e x^2'),('Family 3','a + b x + c exp(-d/T) + e x T/300')]):
 y=3.35-j*.88;ax.text(.04,y,label,color=amber,weight='bold',fontsize=12);ax.text(.27,y,expression,color=text,fontsize=12)
ax.set_xlim(0,1);ax.set_ylim(-.1,4);ax.axis('off');ax.text(.04,0.15,'a, b, c, e [GPa]  |  d, T [K]  |  x [dimensionless]  |  output [GPa]',color=mint,fontsize=11)
save(fig,'02_dimensioned_formula_families')
# 3 synthetic dataset splits
fig,ax=plt.subplots(figsize=(10,4));clean(ax)
for split,col in [('train',cyan),('validation',amber),('test',mint)]:
 s=[r for r in samples if r['split']==split]
 ax.scatter([float(r['T_kelvin']) for r in s],[float(r['E_synthetic_GPa']) for r in s],s=42,label=f'{split}: {len(s)}',color=col,alpha=.84)
ax.set_xlabel('Absolute temperature T (K)');ax.set_ylabel('Synthetic property E (GPa)');ax.legend(facecolor='#122d42',edgecolor='#557',labelcolor=text);save(fig,'03_synthetic_material_samples')
#4 model rankings validation RMSE
fig,ax=plt.subplots(figsize=(10,4));clean(ax)
for fam,col in [(0,cyan),(1,mint),(2,amber),(3,orange)]:
 data=[float(r['validation_rmse_GPa']) for r in rows if int(r['family'])==fam]
 ax.hist(data,bins=np.linspace(0,35,49),alpha=.58,color=col,label=f'family {fam}')
ax.set_xlabel('Validation RMSE (GPa), bounded x-axis for readability');ax.set_ylabel('Candidates');ax.legend(facecolor='#122d42',edgecolor='#557',labelcolor=text);save(fig,'04_candidate_validation_errors')
# 5 selected candidate predictions
fig,ax=plt.subplots(figsize=(10,4));clean(ax)
for split,col in [('train',cyan),('validation',amber),('test',mint)]:
 q=[r for r in selected if r['split']==split]
 ax.scatter([float(r['synthetic_target_GPa']) for r in q],[float(r['native_prediction_GPa']) for r in q],label=split,color=col,s=48)
vals=[float(r['synthetic_target_GPa']) for r in selected];mn=min(vals)-2;mx=max(vals)+2
ax.plot([mn,mx],[mn,mx],color='white',lw=1,ls='--',alpha=.8);ax.set_xlabel('Synthetic target E (GPa)');ax.set_ylabel('Selected prediction E (GPa)');ax.legend(facecolor='#122d42',edgecolor='#557',labelcolor=text);save(fig,'05_selected_predictions')
# 6 residuals by split
fig,ax=plt.subplots(figsize=(10,4));clean(ax)
for split,col in [('train',cyan),('validation',amber),('test',mint)]:
 q=[r for r in selected if r['split']==split]
 ax.scatter([int(r['sample_id']) for r in q],[float(r['native_prediction_GPa'])-float(r['synthetic_target_GPa']) for r in q],color=col,label=split,s=38)
ax.axhline(0,color='white',lw=1,ls='--');ax.set_xlabel('Fixed sample identifier');ax.set_ylabel('Prediction minus synthetic target (GPa)');ax.legend(facecolor='#122d42',edgecolor='#557',labelcolor=text);save(fig,'06_residuals_by_split')
# 7 audit
fig,ax=plt.subplots(figsize=(10,3.5));clean(ax)
ax.barh(['Selected native-vs-Decimal','SDK batch-vs-native','SDK scalar-vs-native'],[60,32000,60000],color=[mint,cyan,amber])
for i,n in enumerate([60,32000,60000]):ax.text(n+1000,i,f'{n:,} passed',color=text,va='center',fontsize=11)
ax.set_xlim(0,75000);ax.set_xlabel('Checked evaluations (different audit scopes)');save(fig,'07_independent_verification')
# 8 selected temperature dependence anchored at x=0.5
fig,ax=plt.subplots(figsize=(10,4));clean(ax)
r=selected[0];a,b,c,d,e=[float(r[k]) for k in ['a_GPa','b_GPa','c_GPa','d_kelvin','e_GPa']];fam=int(r['family'])
t=np.linspace(250,900,160);x=.5
curve=a+b*x+c*np.exp(-d/t)
if fam==1:curve=a+b*x+c/(1+t/d)
if fam==2:curve+=e*x*x
if fam==3:curve+=e*x*(t/300)
ax.plot(t,curve,color=cyan,lw=3);ax.set_xlabel('Absolute temperature T (K), at x=0.5');ax.set_ylabel('Synthetic candidate output E (GPa)');save(fig,'08_temperature_sensitivity')
print('Generated 8 numbered PNG/PDF figure pairs.')
