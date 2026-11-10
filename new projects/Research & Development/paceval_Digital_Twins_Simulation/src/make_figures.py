#!/usr/bin/env python3
"""Recreate the explanatory charts used in the README and white paper.

Requires: matplotlib, numpy, mpmath. Use from repository root:
python3 src/make_figures.py
Charts describe synthetic models and recorded demo output, not device data.
"""
from pathlib import Path
import csv
import numpy as np
import mpmath as mp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures'
FIG.mkdir(exist_ok=True)
NAVY='#16334a';BLUE='#0c77ac';CYAN='#15b4ca';ORANGE='#e07e35';GREEN='#0e8f76';RED='#bd3a3a';MUTED='#65798b'
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'axes.labelsize':10,'figure.facecolor':'white','axes.edgecolor':'#d4dfe5','axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':170})

def save(name):
    plt.tight_layout(pad=2)
    plt.savefig(FIG/name,bbox_inches='tight',facecolor='white')
    plt.close()

def cases():
    with (ROOT/'examples/scenarios.csv').open(newline='') as f:
        return list(csv.DictReader(f))

def vec(x):
    return {k:float(v) for k,v in x.items() if k!='scenario_id'}

def rhs(T,x):
    a,b=T;ta=x['tamb']
    coupling=x['k12']*(a-b)
    loss=x['h2']*(b-ta)+x['krad']*((b/300.)**4-(ta/300.)**4)
    return np.array(((x['power']-coupling-x['h1']*(a-ta))/x['c1'],(coupling-loss)/x['c2']))

def trace(x,dt=2.,steps=180):
    T=np.array((x['t1'],x['t2']),dtype=float)
    tr=[T.copy()]
    for _ in range(steps):
        k1=rhs(T,x);k2=rhs(T+dt*k1/2.,x);k3=rhs(T+dt*k2/2.,x);k4=rhs(T+dt*k3,x)
        T=T+dt*(k1+2*k2+2*k3+k4)/6.;tr.append(T.copy())
    return np.array(tr)

# 01 - boundary diagram, showing NO FMU / FMI implementation claim.
fig,ax=plt.subplots(figsize=(11.2,3.0));ax.set_xlim(0,11.2);ax.set_ylim(0,3);ax.axis('off')
blocks=[(.18,.8,2.35,1.35,'Digital-twin host','States • scenarios\nRK4 time integrator',NAVY),(3.33,.8,2.45,1.35,'paceval runtime','Reusable formulas\nBatch + multiple graphs',BLUE),(6.48,.8,2.05,1.35,'Mathematical results','dT/dt • sensor\nheat exchange',GREEN),(9.15,.8,1.85,1.35,'Validation','Analytic reference\nSciPy • TINC audit',NAVY)]
for x,y,w,h,title,body,col in blocks:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.13,rounding_size=.14',fc=col,ec='none'))
    ax.text(x+w/2,y+h*.68,title,ha='center',va='center',fontsize=10.7,weight='bold',color='white')
    ax.text(x+w/2,y+h*.32,body,ha='center',va='center',fontsize=9,color='white',linespacing=1.55)
for x0,x1 in ((2.67,3.18),(5.91,6.33),(8.65,9.0)):
    ax.add_patch(FancyArrowPatch((x0,1.48),(x1,1.48),arrowstyle='-|>',mutation_scale=19,lw=2,color=CYAN))
ax.text(5.6,2.68,'A reusable mathematics layer inside a conventional time-integration workflow',ha='center',color=NAVY,weight='bold',fontsize=12)
ax.text(5.6,.25,'FMI Model Exchange is an integration reference; this project is not an FMU.',ha='center',color=MUTED,fontsize=9)
save('01_execution_architecture.png')

# 02 - exact one-state reference
v=vec(cases()[0]);v['t1']=293.15;v['tamb']=293.15;v['power']=100.;v['c1']=500.;v['h1']=5.
t=np.linspace(0,600,301);steady=v['tamb']+v['power']/v['h1'];exact=steady+(v['t1']-steady)*np.exp(-v['h1']*t/v['c1'])
fig,ax=plt.subplots(figsize=(9,4.2));ax.plot(t,exact,color=BLUE,lw=2.4,label='Exact analytic temperature')
ax.axhline(steady,color=ORANGE,ls='--',lw=1.6,label='Steady state')
ax.set(xlabel='Simulation time (s)',ylabel='Temperature (K)',title='Single-zone thermal model: exact reference solution')
ax.legend(frameon=False);ax.grid(alpha=.18);save('02_single_zone_analytic.png')

# 03 - two-zone simulation: paceval verified at final endpoint
v=vec(cases()[0]);tr=trace(v);t=np.arange(len(tr))*2.
with (ROOT/'examples/trajectories.csv').open() as f:outrow=next(csv.DictReader(f))
fig,ax=plt.subplots(figsize=(9,4.2));ax.plot(t,tr[:,0],color=ORANGE,lw=2,label='Zone 1 • host RK4')
ax.plot(t,tr[:,1],color=BLUE,lw=2,label='Zone 2 • host RK4')
ax.scatter([360,360],[float(outrow['paceval_T1_K']),float(outrow['paceval_T2_K'])],color=[ORANGE,BLUE],marker='o',s=65,edgecolor='black',linewidth=.5,zorder=3,label='paceval-validated endpoint')
ax.set(xlabel='Simulation time (s)',ylabel='Temperature (K)',title='Coupled two-zone digital twin (synthetic scenario 00)')
ax.legend(frameon=False);ax.grid(alpha=.18);save('03_two_zone_trajectory.png')

# 04 - variation without rebuilding mathematical graphs
v=vec(cases()[0]);levels=np.array([.8,.9,1.,1.1,1.2]);out=[]
for fac in levels:
    x=v.copy();x['power']*=fac;x['h2']*=1.+.25*(fac-.8)
    out.append(trace(x)[-1])
out=np.array(out)
fig,ax=plt.subplots(figsize=(9,4.2));ax.plot(levels*100,out[:,0],'-o',lw=2.2,color=ORANGE,label='Zone 1')
ax.plot(levels*100,out[:,1],'-s',lw=2.2,color=BLUE,label='Zone 2')
ax.set(xlabel='Input power relative to baseline (%)',ylabel='Final temperature after 360 s (K)',title='Five model scenarios using the same explicit graph definitions')
ax.legend(frameon=False);ax.grid(alpha=.18);save('04_parameter_study.png')

# 05 - first-law identity over a trajectory and physically meaningful heat flows
v=vec(cases()[0]);tr=trace(v);t=np.arange(len(tr))*2.
q12=v['k12']*(tr[:,0]-tr[:,1]);q1=v['h1']*(tr[:,0]-v['tamb']);q2=v['h2']*(tr[:,1]-v['tamb'])+v['krad']*((tr[:,1]/300.)**4-(v['tamb']/300.)**4)
fig,ax=plt.subplots(figsize=(9,4.2));ax.plot(t,q12,lw=2,color=BLUE,label='Inter-zone heat flow')
ax.plot(t,q1,lw=2,color=ORANGE,label='Zone 1 environmental loss')
ax.plot(t,q2,lw=2,color=GREEN,label='Zone 2 linear + nonlinear loss')
ax.axhline(v['power'],ls='--',lw=1.5,color=NAVY,label='Input power')
ax.set(xlabel='Simulation time (s)',ylabel='Thermal power (W)',title='Interpretable energy-flow components of the digital twin')
ax.legend(frameon=False,fontsize=9);ax.grid(alpha=.18);save('05_thermal_energy_flows.png')

# 06 - independently checked intervals in ULPs, incl. the two non-enclosures
mp.mp.dps=110
with (ROOT/'examples/tinc_samples.csv').open(newline='') as f:rows=list(csv.DictReader(f))
def check_formula(name,z):
    a,b,ta,p,c1,c2,k,h1,h2,krad,g,off=(z[n] for n in ['t1','t2','tamb','power','c1','c2','k12','h1','h2','krad','gain','offset'])
    q=h2*(b-ta)+krad*((b/mp.mpf(300))**4-(ta/mp.mpf(300))**4)
    if name=='single':return (p-h1*(a-ta))/c1
    if name=='two_rhs1':return (p-k*(a-b)-h1*(a-ta))/c1
    if name=='two_rhs2':return (k*(a-b)-q)/c2
    raise Exception(name)
fig,ax=plt.subplots(figsize=(9,4.5));in_count=0
for i,row in enumerate(rows):
    vals={k:mp.mpf(float(row[k])) for k in ['t1','t2','tamb','power','c1','c2','k12','h1','h2','krad','gain','offset']}
    ref=check_formula(row['formula'],vals)
    lo=mp.mpf(float(row['tinc_lower']));hi=mp.mpf(float(row['tinc_upper']))
    width=float(hi-lo)
    ok=lo<=ref<=hi;in_count+=ok
    ax.scatter(i,width if width else 1e-17,s=55,marker='o' if ok else 'X',
               color=GREEN if ok else RED,zorder=3)
ax.set_yscale('log')
ax.axvline(7.5,color=MUTED,ls=':',alpha=.6)
ax.axvline(15.5,color=MUTED,ls=':',alpha=.6)
ax.set(xlabel='Validation case ID (0–7: single zone; 8–15: zone 1; 16–23: zone 2)',
       ylabel='TINC interval width (K/s, log scale)',
       title='TINC diagnostic intervals and independent 110-digit inclusion checks')
ax.set_xticks(range(0,24,2));ax.grid(axis='y',alpha=.18)
ax.legend(handles=[Line2D([0],[0],marker='o',color='none',markerfacecolor=GREEN,markeredgecolor=GREEN,label='Reference enclosed (22/24)'),
                   Line2D([0],[0],marker='X',color='none',markerfacecolor=RED,markeredgecolor=RED,label='Point-interval exception (2/24)')],
          loc='lower right',frameon=False,fontsize=9)
save('06_tinc_reference_audit.png')
