#!/usr/bin/env python3
"""Regenerate scientific diagrams from published synthetic example CSV files.

The hero marketing art is an illustrative graphic, not measured plant data.
These diagrams make no timing or hardware-speed claims. Requires matplotlib.
"""
from pathlib import Path
import argparse,csv,math
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
import numpy as np

NAVY='#102943'; BLUE='#1879a9'; TEAL='#168f95'; ORANGE='#d97a26'; GRAY='#5c7487'

def format_ax(ax):
    ax.grid(alpha=.20);ax.spines[['top','right']].set_visible(False)

def save(fig,path):
    fig.savefig(path,dpi=190,bbox_inches='tight',facecolor='white')
    plt.close(fig)

def main(inp,out):
    out.mkdir(parents=True,exist_ok=True)
    with inp.open(newline='') as f:rows=list(csv.DictReader(f))
    d=defaultdict(list)
    for row in rows:d[row['scenario']].append({k:(float(v) if k not in ('scenario',) else v) for k,v in row.items()})
    # 01: strict architecture boundary avoids claiming paceval is an MPC solver.
    fig,ax=plt.subplots(figsize=(12,3.9));ax.set_xlim(0,12);ax.set_ylim(0,3.8);ax.axis('off')
    boxes=[(0.3,1.4,2.2,1.0,'Measurements\nSynthetic plant','white',NAVY),
           (3.0,1.4,2.25,1.0,'C++ candidate\nbeam search','#edf4f7',NAVY),
           (5.8,1.4,2.5,1.0,'paceval\n8 reusable graphs','#d9f4f2',TEAL),
           (8.85,1.4,2.8,1.0,'C++ selection\n& offline update','#edf4f7',NAVY)]
    for x,y,w,h,t,face,edge in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.12',fc=face,ec=edge,lw=1.8))
        ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11,color=NAVY,weight='semibold')
    for a,b in ((2.6,3.0),(5.3,5.8),(8.35,8.85)):
        ax.annotate('',xy=(b,1.9),xytext=(a,1.9),arrowprops=dict(arrowstyle='->',lw=2,color=BLUE))
    ax.add_patch(FancyBboxPatch((5.85,0.08),2.4,.67,boxstyle='round,pad=0.1',fc='white',ec=TEAL,lw=1.3))
    ax.text(7.05,.42,'TINC: two\nquadratic checks',ha='center',va='center',fontsize=10,color=NAVY)
    ax.annotate('',xy=(7.0,1.28),xytext=(7.0,.78),arrowprops=dict(arrowstyle='->',lw=1.4,color=TEAL))
    ax.text(6,3.35,'OFFLINE RESEARCH ARCHITECTURE',color=NAVY,ha='center',fontsize=15,weight='bold')
    ax.text(6,2.87,'paceval evaluates formulas; C++ owns optimization, policies, and model scheduling',ha='center',color=GRAY,fontsize=10)
    save(fig,out/'01_execution_architecture.png')
    # 02: illustrative cost landscape of x,u for a fixed uprev.
    fig,ax=plt.subplots(figsize=(8.2,5.3));x=np.linspace(-1.2,1.2,220);u=np.linspace(-1,1,210)
    X,U=np.meshgrid(x,u); NX=.93*X+.23*U+.005-.045*X**3
    Z=4*(NX-.55)**2 + .10*U**2+.08*U**2
    cf=ax.contourf(X,U,Z,levels=22,cmap='YlGnBu_r');ax.contour(X,U,Z,levels=9,colors='white',linewidths=.4,alpha=.5)
    fig.colorbar(cf,ax=ax,label='Synthetic one-step stage cost')
    ax.set(xlabel='Normalized state x',ylabel='Normalized candidate action u',title='Explicit stage-cost surface (synthetic coefficients)');format_ax(ax)
    save(fig,out/'02_stage_cost_surface.png')
    # 03: actual closed-loop paths from real paceval run, not scientific plant measurements.
    fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True)
    for ax,(scenario,items) in zip(axs.flat,d.items()):
        t=[int(r['step'])+1 for r in items];ref=items[0]['target']
        ax.plot(t,[r['x_after'] for r in items],label='paceval-evaluated offline loop',color=BLUE,lw=2.3)
        ax.plot(t,[r['zero_input_reference_x'] for r in items],ls=':',color=GRAY,label='zero-input mathematical reference',lw=1.6)
        ax.axhline(ref,color=ORANGE,ls='--',label='setpoint',lw=1.3)
        ax.set_title(scenario.replace('_',' ').title());ax.set_ylabel('Normalized state');format_ax(ax)
    axs[-1,0].set_xlabel('Discrete simulation step');axs[-1,1].set_xlabel('Discrete simulation step')
    h,l=axs[0,0].get_legend_handles_labels();fig.legend(h,l,loc='upper center',bbox_to_anchor=(.5,1.01),ncol=3,fontsize=9)
    fig.suptitle('Offline predictive-control feasibility: four synthetic scenarios',y=1.085,fontsize=14,color=NAVY)
    fig.tight_layout();save(fig,out/'03_closed_loop_trajectories.png')
    # 04: action grid and rate constraint trajectory for one scenario
    items=d['heating_ramp'];fig,ax=plt.subplots(figsize=(9.8,4.2));k=[int(r['step']) for r in items]
    ax.step(k,[r['control'] for r in items],where='post',color=TEAL,lw=2.3,label='Selected finite-grid action')
    ax.axhline(1,ls=':',color=ORANGE,label='Actuator bound ±1');ax.axhline(-1,ls=':',color=ORANGE)
    ax.set(xlabel='Discrete simulation step',ylabel='Action u',title='Host-selected actions from paceval-scored candidates');ax.set_ylim(-1.2,1.2)
    format_ax(ax);ax.legend();save(fig,out/'04_control_actions.png')
    # 05: positive constraint margins: state and action constraints
    fig,ax=plt.subplots(figsize=(10,4.5));k=np.arange(len(items))
    for label,color in [('state_margin',BLUE),('actuation_margin',TEAL),('slew_margin',ORANGE)]:
        ax.plot(k,[r[label] for r in items],lw=1.8,label=label.replace('_',' '),color=color)
    ax.axhline(0,ls='--',color='black',lw=1)
    ax.set(xlabel='Discrete simulation step',ylabel='Squared-constraint margin',title='Nonnegative synthetic constraint margins (heating scenario)')
    ax.legend();format_ax(ax);save(fig,out/'05_constraint_margins.png')
    # 06: transparent pointwise interval plot, use a scale with clear widths.
    with (inp.parent/'tinc_samples.csv').open(newline='') as f:iv=list(csv.DictReader(f))
    fig,axs=plt.subplots(1,2,figsize=(11,4.4))
    for ax,graph in zip(axs,['actuation_cost','quadratic_state_energy']):
        vals=[r for r in iv if r['graph']==graph];t=np.arange(len(vals))
        center=np.array([float(r['paceval_result']) for r in vals]);lo=np.array([float(r['tinc_lower']) for r in vals]);hi=np.array([float(r['tinc_upper']) for r in vals]);
        ax.errorbar(t,center,yerr=[np.maximum(0,center-lo),np.maximum(0,hi-center)],fmt='o',ms=4,capsize=2,color=TEAL)
        ax.set(title=graph.replace('_',' ').title(),xlabel='Reference sample',ylabel='Mathematical value');format_ax(ax)
    fig.suptitle('TINC pointwise intervals for selected quadratic functions (not a general certification)',fontsize=12,color=NAVY)
    fig.tight_layout();save(fig,out/'06_tinc_pointwise.png')
    # 07: summary of the actual eight graph outputs in the source model
    labels=['State transition','Tracking objective','Actuator effort','Action slew','State envelope','Actuator envelope','Slew envelope','Transition derivative']
    fig,ax=plt.subplots(figsize=(10.2,4.8));ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(0,5.2)
    for j,label in enumerate(labels):
        col=j%4;row=j//4;xx=.2+col*2.53;yy=3.2-row*1.65
        ax.add_patch(FancyBboxPatch((xx,yy),2.18,.9,fc=('#eaf5f8' if row==0 else '#e9f7f3'),ec=BLUE if row==0 else TEAL,boxstyle='round,pad=0.08'))
        ax.text(xx+1.09,yy+.45,label,ha='center',va='center',color=NAVY,fontsize=9.8,weight='medium')
    ax.text(5,4.78,'Eight persistent paceval computation graphs',ha='center',color=NAVY,fontsize=15,weight='bold')
    ax.text(5,.7,'Two additional TINC-enabled quadratic graphs are evaluated separately',ha='center',color=GRAY,fontsize=10)
    save(fig,out/'07_graph_inventory.png')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--trajectory',default=str(Path(__file__).parent.parent/'examples/closed_loop.csv'));p.add_argument('--out-dir',default=str(Path(__file__).parent.parent/'figures'))
    a=p.parse_args();main(Path(a.trajectory),Path(a.out_dir))
