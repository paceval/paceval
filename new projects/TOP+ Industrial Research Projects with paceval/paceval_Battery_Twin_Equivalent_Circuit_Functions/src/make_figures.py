#!/usr/bin/env python3
"""Reconstruct 10 publication-ready figures using original paceval recorded outputs.
Only Figure 01 is a conceptual architecture diagram and is labelled as such.
"""
import csv, argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D  # noqa
BG='#fffdfa';INK='#263942';TEAL='#236b67';ORANGE='#da7549';LIME='#8e9c64';NAVY='#24415d';GREY='#5f7076'
plt.rcParams.update({'font.size':10,'axes.labelsize':10,'axes.titlesize':12,'xtick.labelsize':9,'ytick.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':BG,'axes.facecolor':BG,'savefig.facecolor':BG,'axes.titleweight':'medium','font.family':'DejaVu Sans','legend.fontsize':9})

def load(path):
 with path.open() as f:return list(csv.DictReader(f))
def save(fig, folder, name):
 fig.savefig(folder/(name+'.png'),dpi=230,bbox_inches='tight',pad_inches=.22)
 fig.savefig(folder/(name+'.pdf'),bbox_inches='tight',pad_inches=.22)
 plt.close(fig)

def generate(root):
 folder=root/'figures';folder.mkdir(exist_ok=True)
 traces=load(root/'examples/trace_samples.csv');summary=load(root/'results/scenario_summary.csv');surf=load(root/'results/parameter_surface.csv')
 fig,ax=plt.subplots(figsize=(11,3.2));ax.set(xlim=(0,11.6),ylim=(0,2.1));ax.axis('off')
 nodes=[('Synthetic cell\ncurrent & ambient',.12,2.3),('Original paceval\nECM graphs',3.2,2.25),('C++ state\norchestration',6.23,2.25),('Independent\nverification & plots',9.17,2.3)]
 for text,x,w in nodes:
  ax.add_patch(FancyBboxPatch((x,.53),w,1.15,boxstyle='round,pad=.1,rounding_size=.1',linewidth=1.4,edgecolor=TEAL,facecolor='#eaf2ed'))
  ax.text(x+w/2,1.12,text,ha='center',va='center',fontweight='bold',color=INK,fontsize=10)
 for (a,b) in zip(nodes,nodes[1:]):
  ax.add_patch(FancyArrowPatch((a[1]+a[2]+.12,1.10),(b[1]-.12,1.10),arrowstyle='-|>',mutation_scale=16,linewidth=1.6,color=ORANGE))
 ax.text(5.75,.12,'Conceptual workflow; actual numeric results use original paceval graphs',ha='center',color=GREY,fontsize=9)
 save(fig,folder,'01_workflow')
 def group(where):return [r for r in traces if where(r)]
 # current
 fig,ax=plt.subplots(figsize=(9,4.5))
 for p,(lab,col) in enumerate([('Urban pulses',ORANGE),('Highway load',NAVY),('Charge / rest',TEAL)]):
  rows=group(lambda r:int(r['profile'])==p and int(r['version'])==2 and float(r['ambient_C'])==25)
  ax.step([float(r['time_s'])/60 for r in rows],[float(r['current_A']) for r in rows],where='post',lw=1.65,color=col,label=lab)
 ax.set(title='Deterministic synthetic cell current schedules',xlabel='Elapsed time (min)',ylabel='Cell current (A; discharge positive)');ax.grid(alpha=.17);ax.legend(loc='best');save(fig,folder,'02_current_profiles')
 # Voltages for urban 25
 fig,ax=plt.subplots(figsize=(9,4.6))
 for v,color in [(1,NAVY),(2,ORANGE)]:
  rows=group(lambda r:int(r['profile'])==0 and int(r['version'])==v and float(r['ambient_C'])==25)
  ax.plot([float(r['time_s'])/60 for r in rows],[float(r['terminal_voltage_V']) for r in rows],color=color,lw=1.9,label=f'{v}RC version')
 ax.set(title='Urban current profile: terminal-voltage response',xlabel='Elapsed time (min)',ylabel='Terminal voltage (V)');ax.legend();ax.grid(alpha=.18);save(fig,folder,'03_terminal_voltage')
 # SOC scenarios
 fig,ax=plt.subplots(figsize=(9,4.6))
 for p,(lab,col) in enumerate([('Urban',ORANGE),('Highway',NAVY),('Charge/rest',TEAL)]):
  rows=group(lambda r:int(r['profile'])==p and int(r['version'])==2 and float(r['ambient_C'])==25)
  ax.plot([float(r['time_s'])/60 for r in rows],[float(r['soc']) for r in rows],color=col,lw=1.9,label=lab)
 ax.set(title='State of charge under three synthetic schedules (2RC)',xlabel='Elapsed time (min)',ylabel='SOC (fraction of nominal capacity)');ax.grid(alpha=.18);ax.legend();save(fig,folder,'04_soc_profiles')
 # temp
 fig,ax=plt.subplots(figsize=(9,4.6))
 for amb,col in [(5,TEAL),(25,NAVY),(40,ORANGE)]:
  rows=group(lambda r:int(r['profile'])==1 and int(r['version'])==2 and float(r['ambient_C'])==amb)
  ax.plot([float(r['time_s'])/60 for r in rows],[float(r['temperature_C']) for r in rows],lw=1.9,color=col,label=f'{amb} C ambient')
 ax.set(title='Lumped thermal response under highway load (2RC)',xlabel='Elapsed time (min)',ylabel='Cell temperature (C)');ax.grid(alpha=.18);ax.legend();save(fig,folder,'05_thermal_response')
 # 3D voltage from paceval data
 xs=sorted({float(r['soc']) for r in surf});ys=sorted({float(r['temperature_C']) for r in surf});X,Y=np.meshgrid(xs,ys)
 def matrix(key):
  lut={(float(r['soc']),float(r['temperature_C'])):float(r[key]) for r in surf}
  return np.array([[lut[(x,y)] for x in xs] for y in ys])
 fig=plt.figure(figsize=(9.3,6));ax=fig.add_subplot(111,projection='3d')
 obj=ax.plot_surface(X,Y,matrix('voltage_2rc_V'),cmap='YlOrBr',alpha=.97,linewidth=0,antialiased=True)
 ax.set(xlabel='SOC (-)',ylabel='Cell temperature (C)',zlabel='Loaded voltage (V)',title='paceval-evaluated 2RC terminal-voltage surface')
 ax.view_init(elev=26,azim=-57);fig.colorbar(obj,ax=ax,shrink=.58,pad=.13,label='Voltage (V)');fig.subplots_adjust(left=.04,right=.90,bottom=.07,top=.91)
 save(fig,folder,'06_voltage_surface_3d')
 # R0 heatmap
 fig,ax=plt.subplots(figsize=(9.2,5.5));img=ax.contourf(X,Y,matrix('r0_ohm')*1000,levels=18,cmap='YlOrBr');c=fig.colorbar(img,ax=ax,label='Ohmic resistance (mOhm)')
 ax.set(xlabel='SOC (-)',ylabel='Cell temperature (C)',title='State- and temperature-dependent ohmic resistance');save(fig,folder,'07_ohmic_resistance_map')
 # RC time constants ratio
 fig,ax=plt.subplots(figsize=(9.2,5.5));ratio=matrix('tau2_s')/matrix('tau1_s');img=ax.contourf(X,Y,ratio,levels=18,cmap='viridis');fig.colorbar(img,ax=ax,label='Slow/fast time-constant ratio (-)')
 ax.set(xlabel='SOC (-)',ylabel='Cell temperature (C)',title='Separation of RC relaxation time scales');save(fig,folder,'08_relaxation_time_scales')
 # voltage differences across time
 fig,ax=plt.subplots(figsize=(9,4.5));cmap=[ORANGE,NAVY,TEAL]
 for p,lab in enumerate(['Urban','Highway','Charge/rest']):
  a=group(lambda r:int(r['profile'])==p and int(r['version'])==1 and float(r['ambient_C'])==25)
  b=group(lambda r:int(r['profile'])==p and int(r['version'])==2 and float(r['ambient_C'])==25)
  ax.plot([float(r['time_s'])/60 for r in a],[float(t['terminal_voltage_V'])-float(s['terminal_voltage_V']) for s,t in zip(a,b)],label=lab,lw=1.7,color=cmap[p])
 ax.axhline(0,color=GREY,ls='--',lw=.8);ax.set(title='2RC minus 1RC voltage response: controlled model revision',xlabel='Elapsed time (min)',ylabel='Terminal-voltage difference (V)');ax.grid(alpha=.15);ax.legend();save(fig,folder,'09_formula_version_response')
 # electric energy grouping
 fig,ax=plt.subplots(figsize=(9.4,4.7));s=[r for r in summary if int(r['version'])==2 and float(r['ambient_C'])==25]
 labels=['Urban','Highway','Charge/rest'];centers=np.arange(3);width=.23
 for field,offset,col,lab in [('ocv_energy_Wh',-.23,LIME,'OCV baseline'),('terminal_energy_Wh',0,TEAL,'Terminal'),('ohmic_energy_Wh',.23,ORANGE,'Ohmic')]:
  vals=[float(r[field]) for r in s];ax.bar(centers+offset,vals,width=width,color=col,label=lab)
 ax.axhline(0,color=INK,lw=.6);ax.set_xticks(centers,labels);ax.set(title='Integrated electrical terms across synthetic schedules (2RC)',ylabel='Integrated signed energy (Wh)');ax.legend(ncol=3,loc='upper right');ax.grid(axis='y',alpha=.15)
 save(fig,folder,'10_electrical_energy_terms')
 print('Published 10 PNG and vector PDF figures using original paceval numerical outputs')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=p.parse_args();generate(args.root)
