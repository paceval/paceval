#!/usr/bin/env python3
"""Nine scientific figures exclusively from actual paceval-generated CSVs."""
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
root=Path(__file__).resolve().parent.parent;fig=root/'figures';fig.mkdir(exist_ok=True)
s=pd.read_csv(root/'examples'/'performance_surface.csv')
c=pd.read_csv(root/'examples'/'operating_candidates.csv')
t=pd.read_csv(root/'examples'/'seven_day_replay.csv')
v=pd.read_csv(root/'examples'/'versioned_model_sweep.csv')
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'axes.grid':False,'savefig.facecolor':'white'})
def save(name):
 plt.savefig(fig/(name+'.png'),dpi=230,bbox_inches='tight',pad_inches=.18)
 plt.savefig(fig/(name+'.pdf'),bbox_inches='tight',pad_inches=.16)
 plt.close()
def matrix(k):return s.pivot(index='source_C',columns='sink_C',values=k)
source=np.sort(s.source_C.unique());sink=np.sort(s.sink_C.unique());Y,X=np.meshgrid(source,sink,indexing='ij')
def surf(k,title,zlabel,name,cmap='viridis'):
 Z=matrix(k).to_numpy(); f=plt.figure(figsize=(8.6,6.1));a=f.add_subplot(111,projection='3d');p=a.plot_surface(X,Y,Z,cmap=cmap,rstride=2,cstride=2,linewidth=0,antialiased=True)
 a.set_xlabel('Sink temperature (°C)',labelpad=10);a.set_ylabel('Source temperature (°C)',labelpad=10);a.set_zlabel(zlabel,labelpad=9);a.set_title(title,pad=15);a.view_init(elev=24,azim=-130);f.colorbar(p,ax=a,shrink=.62,aspect=18,pad=.11);save(name)
surf('system_cop','System COP across source and sink temperatures','System COP (–)','01_system_cop_surface')
figg,ax=plt.subplots(figsize=(8,5.5));cs=ax.contourf(X,Y,matrix('system_cop').values,levels=26,cmap='viridis');ax.contour(X,Y,matrix('system_cop').values,levels=[2.5,3,3.5,4],colors='white',linewidths=.8);figg.colorbar(cs,ax=ax,label='System COP (–)');ax.set(xlabel='Sink temperature (°C)',ylabel='Source temperature (°C)',title='Constant operating setting: System COP contours');save('02_system_cop_contours')
surf('available_kw','Available heating capacity surface','Heating capacity (kW)','03_available_capacity_surface','plasma')
surf('total_electric_kw','Electrical power at the declared operating point','Electric power (kW)','04_electric_power_surface','cividis')
figg,ax=plt.subplots(figsize=(8,5));ax.hist(c.system_cop_v1,bins=55,color='#148b89',alpha=.85);ax.axvline(2.5,color='#d35c37',ls='--',label='Illustrative COP threshold');ax.set(xlabel='System COP (–)',ylabel='Synthetic operating points',title='Distribution over 6,000 deterministic candidates');ax.legend();save('05_cop_distribution')
figg,ax=plt.subplots(figsize=(9,5));ax.plot(t.hour,t.delivered_kw,color='#0f8b8d',lw=1.8,label='Delivered heat');ax.plot(t.hour,t.electric_kw,color='#df7d2a',lw=1.8,label='Electricity');ax.fill_between(t.hour,t.electric_kw,t.delivered_kw,color='#128785',alpha=.09);ax.set(xlabel='Synthetic replay hour',ylabel='Power (kW)',title='Seven-day paceval heat-pump operating replay');ax.legend();save('06_seven_day_replay')
figg,ax=plt.subplots(figsize=(8,5));ax.plot(v.source_C,v.system_cop_v1,label='Version 1',lw=2);ax.plot(v.source_C,v.system_cop_v2,label='Version 2',lw=2,ls='--');ax.set(xlabel='Source temperature (°C)',ylabel='System COP (–)',title='Two independently retained formula versions');ax.legend();save('07_formula_versions')
figg,ax=plt.subplots(figsize=(8,5));ax.plot(sink,s[s.source_C==source[len(source)//2]].d_cop_d_sink.to_numpy(),lw=2,color='#be6d3e',label='dCOP/d sink temperature');ax.plot(sink,s[s.source_C==source[len(source)//2]].d_cop_d_source.to_numpy(),lw=2,color='#16877d',label='dCOP/d source temperature');ax.axhline(0,color='gray',lw=.7);ax.set(xlabel='Sink temperature (°C)',ylabel='Sensitivity (per °C)',title='Analytical COP-map sensitivities, fixed source temperature');ax.legend();save('08_analytical_sensitivities')
figg,ax=plt.subplots(figsize=(8.3,5.3));good=c[c.screen_pass==1];bad=c[c.screen_pass==0];ax.scatter(bad.source_C,bad.sink_C,s=4,alpha=.1,label='Outside example margins',color='#cf6748');ax.scatter(good.source_C,good.sink_C,s=6,alpha=.18,label='Within example margins',color='#19877c');ax.set(xlabel='Source temperature (°C)',ylabel='Sink temperature (°C)',title='Illustrative screening decisions from paceval guard margins');ax.legend(markerscale=3);save('09_screening_decisions')
print('Nine figures exported as PNG and vector PDF')
