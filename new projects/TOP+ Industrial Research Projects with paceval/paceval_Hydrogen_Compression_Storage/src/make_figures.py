#!/usr/bin/env python3
"""Draw study figures ONLY from verified original paceval output CSVs."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results';F=ROOT/'figures';F.mkdir(exist_ok=True)
BLUE='#056B86';TEAL='#00AAB9';ORANGE='#EA744A';DARK='#122A41';GRAY='#64748B';BG='#F6F9FB'
plt.rcParams.update({'font.size':10,'axes.titlesize':14,'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','grid.alpha':0.24})
hero=Image.open(F/'00_hydrogen_compression_hero.png').convert('RGB')
if hero.size!=(2400,1200):hero.resize((2400,1200),Image.Resampling.LANCZOS).save(F/'00_hydrogen_compression_hero.png',quality=95)

def save(fname,fig):
    fig.savefig(F/fname,dpi=165,bbox_inches='tight',pad_inches=.16)
    fig.savefig(F/fname.replace('.png','.pdf'),bbox_inches='tight',pad_inches=.16)
    plt.close(fig)

# Compact, grounded data loading; no calculations standing in for paceval results.
rows=[]
with (R/'compression_scenarios.csv').open(newline='') as f:
    for r in csv.DictReader(f):
        rows.append((int(r['id']),int(r['version']),int(r['stages']),float(r['pressure_in_bar']),float(r['pressure_out_bar']),float(r['initial_temperature_K']),float(r['final_conditioned_temperature_K']),float(r['total_power_kW']),float(r['total_cooling_kW']),float(r['maximum_stage_temperature_K']),float(r['minimum_stage_temperature_margin_K']),float(r['minimum_cooler_margin_kW']),float(r['screening_score']),r['status']))
from collections import defaultdict,Counter
x=np.array([r[:13] for r in rows],float)
status=np.array([r[13] for r in rows]);v=x[:,1].astype(int);ns=x[:,2].astype(int)

# 01 conceptual workflow, not an experimental figure.
fig,ax=plt.subplots(figsize=(12,3.25));ax.set_xlim(0,12);ax.set_ylim(0,3);ax.axis('off')
blocks=[(.3,1.05,2.,.9,'Validated inputs','pressure, H2 flow, T'),(3,1.05,2.,.9,'paceval stages','polytropic + cooling'),(5.7,1.05,2.,.9,'paceval storage','mass, T, pressure'),(8.4,1.05,3.1,.9,'Host decision & audit','margins, versioned CSV')]
for i,(px,py,w,h,title,sub) in enumerate(blocks):
    ax.add_patch(FancyBboxPatch((px,py),w,h,boxstyle='round,pad=0.09',linewidth=1.6,edgecolor=TEAL if i in(1,2) else BLUE,facecolor='#EAF7F9' if i in(1,2) else '#EEF2F6'))
    ax.text(px+w/2,py+.59,title,ha='center',weight='bold',fontsize=11,color=DARK)
    ax.text(px+w/2,py+.22,sub,ha='center',fontsize=8.8,color=GRAY)
    if i<3:ax.add_patch(FancyArrowPatch((px+w+.1,1.5),(blocks[i+1][0]-.12,1.5),arrowstyle='-|>',mutation_scale=16,color=ORANGE,lw=1.8))
ax.text(6,2.58,'Mathematical responsibility: original paceval execution graphs',ha='center',fontsize=13,weight='bold',color=DARK)
ax.text(6,.5,'Independent C++ and 80-digit reference calculations verify the same data, not the production execution path',ha='center',fontsize=9,color=GRAY)
save('01_execution_architecture.png',fig)

# 02 mean compressor energy across stage counts.
fig,ax=plt.subplots(figsize=(9,5));
for ver,color in ((1,BLUE),(2,ORANGE)):
    pass
# MDOT is in the input CSV, pair it once with id to derive specific energy from actual reported power.
mdots={int(r['id']):float(r['mdot_kgs']) for r in csv.DictReader((R/'synthetic_compressor_scenarios.csv').open())}
spec=np.array([r[7]/mdots[r[0]] for r in rows])
for ver,color in ((1,BLUE),(2,ORANGE)):
    m=[spec[(v==ver)&(ns==k)].mean() for k in range(1,5)]
    ax.plot(range(1,5),m,'o-',linewidth=2.5,markersize=8,color=color,label=f'Model V{ver}')
ax.set(xticks=[1,2,3,4],xlabel='Number of compression stages',ylabel='Screening specific work (kJ/kg)',title='More stages with intercooling change specific work')
ax.grid(True,axis='y');ax.legend(frameon=False);save('02_specific_work_by_stage.png',fig)

# 03 peak thermal response.
fig,ax=plt.subplots(figsize=(9,5));
for ver,color in ((1,BLUE),(2,ORANGE)):
    points=[x[(v==ver)&(ns==j),9].mean() for j in range(1,5)]
    ax.plot(range(1,5),points,'s-',lw=2.5,markersize=8,color=color,label=f'V{ver}')
ax.axhline(445,ls='--',lw=1.2,color='#AA7947',label='Illustrative reference, 445 K')
ax.set(xticks=[1,2,3,4],xlabel='Number of compression stages',ylabel='Average maximum stage temperature (K)',title='Thermal peak versus staged compression');ax.legend(frameon=False);ax.grid(axis='y');save('03_peak_stage_temperature.png',fig)

# 04 status mix.
fig,ax=plt.subplots(figsize=(10,5.1));cats=['ACCEPT','REVIEW','REJECT'];colors=['#0C9B8B','#E5A541','#D85B51'];positions=[];labels=[]
for ver in (1,2):
    for stage in (1,2,3,4):
        mask=(v==ver)&(ns==stage);total=mask.sum();bottom=0;px=stage+(ver-1)*5;positions.append(px);labels.append(f'V{ver}\n{stage} stage')
        for label,color in zip(cats,colors):
            val=100*np.sum(status[mask]==label)/total;ax.bar(px,val,bottom=bottom,color=color,width=.72,edgecolor='white',linewidth=.6);bottom+=val
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor=color,label=label) for label,color in zip(cats,colors)],ncol=3,frameon=False,loc='upper center',bbox_to_anchor=(.5,-.13))
ax.set(xticks=positions,xticklabels=labels,ylim=(0,100),ylabel='Fraction of synthetic scenario cases (%)',title='Host screening decisions from paceval margins');save('04_quality_decisions.png',fig)

# 05 4-stage thermal guard by initial temperature and pressure ratio.
mask=(v==1)&(ns==4);ratio=x[mask,4]/x[mask,3];tin=x[mask,5];margin=x[mask,10]
hist=np.histogram2d(ratio,tin,bins=[np.linspace(3,14,28),np.linspace(280,325,21)],weights=margin)[0]
cnt=np.histogram2d(ratio,tin,bins=[np.linspace(3,14,28),np.linspace(280,325,21)])[0]
grid=np.where(cnt>0,hist/np.maximum(cnt,1),np.nan)
fig,ax=plt.subplots(figsize=(9,5.5));im=ax.imshow(grid.T,origin='lower',extent=[3,14,280,325],aspect='auto',cmap='RdYlGn',vmin=-80,vmax=110);fig.colorbar(im,ax=ax,label='Average minimum stage temperature margin (K)');ax.set(xlabel='Total compression pressure ratio',ylabel='Initial gas temperature (K)',title='V1 thermal screening landscape (4 stages)');save('05_thermal_margin_surface.png',fig)

# 06 Version paired change in specific work.
sp=np.zeros((2,len(mdots)))
for idx,r in enumerate(rows):sp[r[1]-1,r[0]]=spec[idx]
diff=sp[1]-sp[0]
fig,ax=plt.subplots(figsize=(9,4.8));dat=[diff[np.array([int(r[0])%4==k-1 for r in rows[:len(mdots)]])] for k in range(1,5)]
ax.boxplot(dat,patch_artist=True,showfliers=False,boxprops={'facecolor':'#D0E5E9','edgecolor':BLUE},medianprops={'color':ORANGE,'linewidth':2});ax.axhline(0,ls='--',color=GRAY);ax.set(xlabel='Number of stages',ylabel='V2 minus V1 specific work (kJ/kg)',title='Effect of the hypothetical efficiency-model revision');save('06_model_revision_energy.png',fig)

# 07 color scatter, sampled without inferential noise.
fig,ax=plt.subplots(figsize=(9,5));
for ver,c in ((1,BLUE),(2,ORANGE)):
    ids=np.flatnonzero(v==ver)[::80];ax.scatter(x[ids,7],x[ids,8],s=9,alpha=.37,color=c,label=f'V{ver}')
ax.set(xlabel='Total compressor power (kW)',ylabel='Total intercooler heat removal (kW)',title='Coupled power and heat removal at synthetic operating points');ax.legend(frameon=False);save('07_cooling_and_power.png',fig)

# 08 pressure sensitivity based on original paceval graph results.
sv=[]
for row in csv.DictReader((R/'stage_trace_samples.csv').open()):sv.append((int(row['version']),float(row['pout_bar'])/float(row['pin_bar']),float(row['dT_dpout_Kbar']),float(row['dT_detaeff_K'])))
sv=np.array(sv)
fig,ax=plt.subplots(figsize=(9,5));
for ver,c in ((1,BLUE),(2,ORANGE)):
    y=sv[sv[:,0]==ver];ax.scatter(y[:,1],y[:,2],s=14,alpha=.52,color=c,label=f'V{ver}')
ax.set(xlabel='Stage pressure ratio',ylabel='Analytical ∂T_out/∂P_out (K/bar)',title='Pressure sensitivity calculated in paceval');ax.legend(frameon=False);save('08_pressure_sensitivities.png',fig)

sr=[]
for row in csv.DictReader((R/'storage_profiles.csv').open()):sr.append((int(row['version']),int(row['profile']),int(row['step']),float(row['time_s']),float(row['tank_T_K']),float(row['pressure_bar']),float(row['temperature_margin_K']),float(row['pressure_margin_bar']),int(float(row['valid']))))
sr=np.array(sr)

# 09 temperature trajectories.
fig,ax=plt.subplots(figsize=(9,5));
for ver,c in ((1,BLUE),(2,ORANGE)):
    for prof in (1,5,9,13):
        a=sr[(sr[:,0]==ver)&(sr[:,1]==prof)];ax.plot(a[:,3]/60,a[:,4],color=c,alpha=.35+.15*(prof==5),lw=1.55,label=f'V{ver} profile {prof}' if prof in (1,5) else None)
ax.set(xlabel='Fill simulation time (min)',ylabel='One-zone storage temperature (K)',title='Storage temperature trajectories with heat transfer');ax.legend(ncol=2,fontsize=8,frameon=False);ax.grid(axis='y');save('09_storage_temperature_profiles.png',fig)

# 10 storage pressure trajectories.
fig,ax=plt.subplots(figsize=(9,5));
for ver,c in ((1,BLUE),(2,ORANGE)):
    for prof in (0,5,10,15):
        a=sr[(sr[:,0]==ver)&(sr[:,1]==prof)];ax.plot(a[:,3]/60,a[:,5],color=c,alpha=.5,lw=1.5,label=f'V{ver} profile {prof}' if prof in (0,5) else None)
ax.set(xlabel='Fill simulation time (min)',ylabel='Ideal-gas vessel pressure (bar)',title='Pressure evolution in the rigid-vessel screening model');ax.legend(ncol=2,fontsize=8,frameon=False);ax.grid(axis='y');save('10_storage_pressure_profiles.png',fig)

# 11 binary guard as a function of profile and integration step.
fig,ax=plt.subplots(figsize=(10,5.3));tab=np.zeros((32,180));
for ver,prof,step,_,_,_,_,_,passed in sr:tab[(int(ver)-1)*16+int(prof),int(step)]=passed
im=ax.imshow(tab,aspect='auto',origin='lower',cmap=LinearSegmentedColormap.from_list('allowed',['#D14E58','#F5B65A','#21A095'],N=2),interpolation='nearest',vmin=0,vmax=1);ax.axhline(15.5,color='white',lw=2);ax.set(xlabel='Discrete fill step (4 s each)',ylabel='Storage profiles, first 16 V1 / next 16 V2',title='Actual paceval storage guard outcome by step');save('11_storage_guard_outcomes.png',fig)

# 12 storage envelope positions at last step.
last=sr[sr[:,2]==179];fig,ax=plt.subplots(figsize=(8.5,5.4));
for ver,c in ((1,BLUE),(2,ORANGE)):
    a=last[last[:,0]==ver];colors=np.where(a[:,8]>0,'#0C9B8B','#D5524D');ax.scatter(a[:,5],a[:,4],c=colors,s=70,edgecolors='white',lw=.8,label=f'V{ver}',marker='o' if ver==1 else 's')
ax.set(xlabel='Final ideal-gas pressure (bar)',ylabel='Final single-zone temperature (K)',title='Storage screening endpoints (green: inside per-profile limits)');ax.legend(frameon=False);save('12_storage_endpoint_envelope.png',fig)

# 13 fraction accepted in stage-count series.
fig,ax=plt.subplots(figsize=(9,4.5));
for ver,c in ((1,BLUE),(2,ORANGE)):
    y=[100*np.mean(status[(v==ver)&(ns==k)]=='ACCEPT') for k in range(1,5)]
    ax.plot(range(1,5),y,'o-',lw=2.4,color=c,label=f'V{ver}')
ax.set(ylim=(0,102),xticks=[1,2,3,4],xlabel='Number of compression stages',ylabel='ACCEPT fraction (%)',title='Screening acceptance depends strongly on stage count');ax.legend(frameon=False);ax.grid(axis='y');save('13_accept_fraction_by_stages.png',fig)

print('PASS generated cover and 13 figures, each scientific figure grounded in original paceval result CSVs')
