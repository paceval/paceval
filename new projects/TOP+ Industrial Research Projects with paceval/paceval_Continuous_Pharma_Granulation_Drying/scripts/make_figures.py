#!/usr/bin/env python3
"""Scientific figures from recorded ORIGINAL paceval outputs; no analytical redraw of results."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
rows=list(csv.DictReader((ROOT/'results/screening.csv').open(newline='',encoding='utf8')))
comp=list(csv.DictReader((ROOT/'results/model_comparison.csv').open(newline='',encoding='utf8')))
A=[z for z in rows if z['model']=='V1'];B=[z for z in rows if z['model']=='V2']
assert len(A)==len(B)==2880
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12.5,'axes.titleweight':'bold','axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.20,'savefig.facecolor':'white'})
def col(r,key):return np.array([float(z[key]) for z in r])
def save(fig,name):
 fig.tight_layout(pad=2.2);fig.savefig(OUT/(name+'.png'),dpi=190,bbox_inches='tight');fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def scatter(ax,x,y,label,alpha=.38,s=8):ax.scatter(x,y,label=label,alpha=alpha,s=s)
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(A,'time_s')/60,col(A,'exit_wet')*100,'V1 single rate');scatter(ax,col(B,'time_s')/60,col(B,'exit_wet')*100,'V2 two-population');ax.set(xlabel='Nominal dryer residence time (min)',ylabel='Exit water fraction, wet basis (%)',title='Dryer residence time and predicted residual water');ax.legend();save(fig,'fig01_residence_moisture')
fig,ax=plt.subplots(figsize=(9,5));ax.hist(col(A,'exit_wet')*100,bins=50,alpha=.65,label='V1');ax.hist(col(B,'exit_wet')*100,bins=50,alpha=.48,label='V2');ax.set(xlabel='Exit moisture, wet basis (%)',ylabel='Recorded scenario count',title='Predicted moisture distributions across identical candidate cases');ax.legend();save(fig,'fig02_moisture_distributions')
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(A,'air_K')-273.15,col(A,'moisture_eq_dry')*100,'Equilibrium dry-basis moisture');ax.set(xlabel='Drying-air temperature (°C)',ylabel='Illustrative equilibrium moisture, dry basis (%)',title='Temperature sensitivity of modeled equilibrium water');save(fig,'fig03_equilibrium_vs_air_temp')
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(A,'air_K')-273.15,col(A,'granule_temp_K')-273.15,'V1');scatter(ax,col(B,'air_K')-273.15,col(B,'granule_temp_K')-273.15,'V2');ax.plot([40,120],[40,120],ls='--',lw=.8,color='gray',label='Reference line');ax.set(xlabel='Drying-air temperature (°C)',ylabel='Modeled granule temperature (°C)',title='Illustrative evaporative cooling and product heating');ax.legend();save(fig,'fig04_granule_temperature')
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(B,'early_wet')*100,col(B,'late_wet')*100,'V2 residence endpoints',alpha=.34);ax.plot([0,14],[0,14],ls='--',lw=1,color='gray');ax.axvline(5,linestyle=':',color='red');ax.axhline(.9,linestyle=':',color='red');ax.set(xlabel='Short-residence predicted moisture (%)',ylabel='Long-residence predicted moisture (%)',title='Residence-time spread and two-sided moisture constraints');save(fig,'fig05_residence_window')
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(A,'evaporation_kg_h'),col(A,'latent_duty_kW'),'V1 evaporation indicator',alpha=.32);scatter(ax,col(B,'evaporation_kg_h'),col(B,'latent_duty_kW'),'V2 evaporation indicator',alpha=.26);ax.set(xlabel='Modeled water evaporation (kg/h)',ylabel='Latent heat-load indicator (kW)',title='Mass and latent-duty consistency');ax.legend();save(fig,'fig06_water_latent_duty')
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(A,'sensor_residual')*100,col(A,'exit_wet')*100,'V1',alpha=.28);scatter(ax,col(B,'sensor_residual')*100,col(B,'exit_wet')*100,'V2',alpha=.20);ax.axvline(0,lw=.8,color='gray');ax.set(xlabel='Synthetic PAT residual, observed − predicted (percentage points)',ylabel='Predicted exit moisture (%)',title='Sensor consistency diagnostic with synthetic observations');ax.legend();save(fig,'fig07_pat_residuals')
fig,ax=plt.subplots(figsize=(9,5));scatter(ax,col(comp,'time_s')/60,col(comp,'delta_wet')*100,'V2 − V1',alpha=.34);ax.axhline(0,color='gray',lw=.8);ax.set(xlabel='Residence time (min)',ylabel='Version difference (percentage points wet moisture)',title='Physical model-form differences, not engine accuracy');save(fig,'fig08_model_version_difference')
groups=['normal','humid','hot','short_residence'];counts={v:Counter(r['scenario'] for r in dat if float(r['quality_guard'])>.5) for v,dat in [('V1',A),('V2',B)]};xx=np.arange(4);fig,ax=plt.subplots(figsize=(9,5));ax.bar(xx-.19,[counts['V1'][g] for g in groups],width=.38,label='V1');ax.bar(xx+.19,[counts['V2'][g] for g in groups],width=.38,label='V2');ax.set_xticks(xx,['Normal','Humid air','Hot air','Short residence']);ax.set(ylabel='Scenarios passing illustrative guards',title='Feasibility by explicitly synthetic operating group');ax.legend();save(fig,'fig09_group_feasibility')
fig=plt.figure(figsize=(9,5.8));ax=fig.add_subplot(111,projection='3d');idx=np.linspace(0,len(B)-1,900).astype(int);x=col(B,'time_s')[idx]/60;y=col(B,'air_K')[idx]-273.15;z=col(B,'exit_wet')[idx]*100;sc=ax.scatter(x,y,z,c=z,cmap='viridis',alpha=.72,s=10);ax.set_xlabel('Residence (min)',labelpad=8);ax.set_ylabel('Drying air (°C)',labelpad=8);ax.set_zlabel('Exit water (%)',labelpad=8);ax.view_init(23,-57);ax.set_title('3D sample of recorded V2 paceval output',pad=14);fig.colorbar(sc,ax=ax,pad=.13,shrink=.70,label='Wet-basis moisture (%)');save(fig,'fig10_3d_operating_surface')
source=Path('/mnt/data/a_highly_detailed_stylized_scientific_industrial.png')
assert source.is_file(),source
img=Image.open(source).convert('RGB');img=img.resize((2400,1200),Image.Resampling.LANCZOS)
img.save(OUT/'00_pharma_granulation_hero_2400x1200.png',optimize=True)
print('FIGURES PASS: 10 actual paceval graphs in PNG+vector PDF and 2400x1200 illustration')
