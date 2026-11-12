#!/usr/bin/env python3
"""Re-create figures from the bundled synthetic numeric audit and explicitly labeled conceptual mathematics."""
import csv, json, math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
p=Path(__file__).resolve().parents[1]; f=p/'figures'
navy='#0b1627'; cyan='#29d6e5'; mint='#59d7ac'; amber='#ffd274'; gray='#c1d0de';
plt.rcParams.update({'figure.facecolor':navy,'axes.facecolor':navy,'axes.edgecolor':'#455a72','axes.labelcolor':gray,'xtick.color':gray,'ytick.color':gray,'text.color':gray,'font.size':10,'savefig.facecolor':navy})
def save(name):
    plt.tight_layout(pad=1.6);plt.savefig(f/name,dpi=180,bbox_inches='tight');plt.savefig(f/name.replace('.png','.pdf'),bbox_inches='tight');plt.close()
# workflow
fig,ax=plt.subplots(figsize=(11.6,3.3));ax.set_xlim(0,10);ax.set_ylim(0,2);ax.axis('off')
labels=['Versioned synthetic\nscorecard + inputs','Host validation\nand finite domain','Reusable paceval\nPD expression graph','Independent numerical\naudit and provenance']
for i,label in enumerate(labels):
    x=.1+i*2.53
    ax.add_patch(FancyBboxPatch((x,.72),2.18,.78,boxstyle='round,pad=.09',linewidth=1.5,edgecolor=cyan if i==2 else '#4cacc3',facecolor='#122a3d'))
    ax.text(x+1.09,1.11,label,ha='center',va='center',color='white',fontsize=10,weight='bold')
    if i<3:ax.annotate('',xy=(x+2.5,1.1),xytext=(x+2.27,1.1),arrowprops={'arrowstyle':'-|>','color':mint,'lw':1.8})
ax.text(5,.30,'Host-controlled features, model versions and reason calculation  |  paceval scope: mathematical graph execution',ha='center',fontsize=9)
save('01_execution_architecture.png')
# mathematical logistic
fig,ax=plt.subplots(figsize=(10.8,4.0));zs=[-8+i/50 for i in range(801)];ys=[1/(1+math.exp(-z)) for z in zs];ax.plot(zs,ys,color=cyan,lw=2.8);ax.axvline(0,color='#66788e',ls='--');ax.axhline(.5,color='#66788e',ls='--');ax.set(xlabel='Synthetic log-odds z',ylabel='Logistic output (not a calibrated PD)',title='Mathematical kernel: sigmoid(z)');ax.grid(alpha=.15);save('02_logistic_kernel.png')
rows=list(csv.DictReader((p/'examples/scorecard_samples.csv').open()))
pds=[float(x['pd']) for x in rows];fig,ax=plt.subplots(figsize=(10.8,4));ax.hist(pds,bins=30,color=mint,edgecolor=navy);ax.set(title='10,000 exported synthetic paceval-audited scorecard outputs',xlabel='Uncalibrated logistic output',ylabel='Frequency');ax.grid(axis='y',alpha=.16);save('03_synthetic_output_distribution.png')
# contributions for first non-boundary row
r=rows[5];terms=[float(r['b'+str(j)])*float(r['x'+str(j)]) for j in range(5)];fig,ax=plt.subplots(figsize=(10.8,3.8));ax.barh([f'Feature {i}' for i in range(5)],terms,color=[amber if i==int(r['dominant_logodds_feature']) else cyan for i in range(5)]);ax.invert_yaxis();ax.set(xlabel='Additive contribution to synthetic log-odds',title='Illustrative contribution ranking (not a regulatory reason code)');ax.grid(axis='x',alpha=.14);save('04_logodds_contributions.png')
# sensitivity, model first and different utilization only
first=rows[10];b=[float(first['b'+str(i)]) for i in range(5)];x=[float(first['x'+str(i)]) for i in range(5)];base=float(first['intercept']);xv=[i/100 for i in range(101)]; y=[]
for xx in xv:
    z=base+b[0]*xx+sum(b[j]*x[j] for j in range(1,5));y.append(1/(1+math.exp(-z)))
fig,ax=plt.subplots(figsize=(10.8,4));ax.plot(xv,y,c=cyan,lw=2.6);ax.axvline(x[0],c=amber,ls='--',label='Original synthetic value');ax.legend(facecolor=navy,labelcolor='white');ax.set(title='Controlled single-feature sensitivity: one fixed synthetic model',xlabel='Synthetic feature 0 (all other features held fixed)',ylabel='Uncalibrated logistic output');ax.grid(alpha=.15);save('05_single_feature_sensitivity.png')
# numeric audit
summary=json.loads((p/'results/high_precision_audit.json').read_text());fig,ax=plt.subplots(figsize=(10.8,3.6));ax.bar(['80-digit decimal audit\npassed','80-digit decimal audit\nfailed'],[summary['rows_checked']-summary['failures'],summary['failures']],color=[mint,amber]);ax.set(title='Observed arithmetic audit on 10,000 exported samples',ylabel='Rows');ax.grid(axis='y',alpha=.15);forbidden=False
for i,y in enumerate([summary['rows_checked']-summary['failures'],summary['failures']]):ax.text(i,y+130,str(y),ha='center',fontsize=12,weight='bold',color='white')
ax.set_ylim(0,11500);save('06_independent_numeric_audit.png')
# scope
fig,ax=plt.subplots(figsize=(10.8,3.5));ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3));blocks=[(.2,5,'Verified with paceval','10,000 scalar checks; 6,400 batch checks; 10,000 Decimal checks'),(5.25,4.55,'Outside research scope','Credit model calibration; fairness; compliant lending decisions')]
for x,w,head,sub in blocks:
    ax.add_patch(FancyBboxPatch((x,.52),w,1.9,boxstyle='round,pad=.11',edgecolor=mint if x<1 else amber,facecolor='#122a3d',lw=2));ax.text(x+.18,1.90,head,fontsize=14,color=mint if x<1 else amber,weight='bold');ax.text(x+.18,1.25,sub,fontsize=9,color='white',wrap=True)
save('07_evidence_boundary.png')
