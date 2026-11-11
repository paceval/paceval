#!/usr/bin/env python3
"""Generate the publication figures from the checked CSV files only."""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BLUE='#0e628d'; CYAN='#00a5bf'; ORANGE='#f09a4d'; PURPLE='#845ab1'; GREEN='#0e816b'

def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.grid':True,'grid.alpha':0.17,
                         'savefig.facecolor':'white','axes.titleweight':'bold'})
def save(fig,folder,name):
    fig.savefig(folder/(name+'.png'),dpi=180,bbox_inches='tight',pad_inches=.16)
    fig.savefig(folder/(name+'.svg'),bbox_inches='tight',pad_inches=.16)
    plt.close(fig)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('data',type=Path);ap.add_argument('figures',type=Path)
    a=ap.parse_args();a.figures.mkdir(parents=True,exist_ok=True);style()
    obs=pd.read_csv(a.data/'observations.csv');cand=pd.read_csv(a.data/'candidates.csv');tr=pd.read_csv(a.data/'heldout_trajectories.csv')
    selection=pd.read_csv(a.data/'selection.csv');updates=pd.read_csv(a.data/'model_updates.csv');tinc=pd.read_csv(a.data/'tinc_samples.csv')
    fig,ax=plt.subplots(figsize=(9.5,4.7));splits=['Training','Validation','Held-out test']
    ax.bar(splits,[3,2,2],color=[BLUE,CYAN,GREEN],width=.58)
    for i,n in enumerate([3,2,2]):ax.text(i,n+.07,f'{n} independent trajectories',ha='center',fontsize=11)
    ax.set_ylim(0,3.9);ax.set_ylabel('Number of trajectories per system');ax.set_title('Whole-trajectory data partitioning prevents adjacent-time leakage')
    save(fig,a.figures,'01_data_splits')
    fig,axs=plt.subplots(1,2,figsize=(12,4.5),sharey=True)
    for ax,(sc,g) in zip(axs,cand.groupby('scenario',sort=False)):
        data=g['train_mse'].to_numpy();ax.scatter(np.arange(len(data)),data,c=np.where(g['id'].to_numpy()==0,ORANGE,BLUE),s=10,alpha=.55)
        ax.set_yscale('log');ax.set_ylim(1e-9,10);ax.set_xlabel('Candidate ID');ax.set_title(sc.replace('_',' ').title())
    axs[0].set_ylabel('Training derivative MSE (log scale)');fig.suptitle('3,000 tested candidate models: independent coefficient variations',fontweight='bold')
    save(fig,a.figures,'02_candidate_error_landscape')
    fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for ax,(sc,g) in zip(axs,tr[(tr.trajectory==5)].groupby('scenario',sort=False)):
        ax.plot(g.t,g.x_truth,color=BLUE,lw=2.4,label='Reference trajectory')
        ax.plot(g.t,g.x_paceval,color=ORANGE,lw=1.2,ls='--',label='Selected paceval model')
        ax.set_ylabel('Displacement x');ax.set_title(sc.replace('_',' ').title());ax.legend(loc='upper right',fontsize=9)
    axs[-1].set_xlabel('Time');fig.suptitle('Unseen trajectories: reference and selected model',fontweight='bold')
    save(fig,a.figures,'03_heldout_displacement')
    fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for ax,(sc,g) in zip(axs,tr[(tr.trajectory==6)].groupby('scenario',sort=False)):
        ax.plot(g.t,g.v_truth,color=BLUE,lw=2.4,label='Reference velocity')
        ax.plot(g.t,g.v_paceval,color=ORANGE,lw=1.2,ls='--',label='paceval-integrated model')
        ax.set_ylabel('Velocity v');ax.set_title(sc.replace('_',' ').title());ax.legend(loc='upper right',fontsize=9)
    axs[-1].set_xlabel('Time');fig.suptitle('Independent held-out excitation: velocity prediction',fontweight='bold')
    save(fig,a.figures,'04_heldout_velocity')
    fig,ax=plt.subplots(figsize=(10.8,4.8))
    for sc,g in tr[tr.trajectory==5].groupby('scenario',sort=False):
        ax.plot(g.t,1e6*(g.x_paceval-g.x_truth),label=sc.replace('_',' ').title(),lw=1.8)
    ax.set_ylabel('Displacement residual (micro-units)');ax.set_xlabel('Time');ax.set_title('Numerical integration residuals on unseen trajectories');ax.legend()
    save(fig,a.figures,'05_heldout_residuals')
    fig,ax=plt.subplots(figsize=(10.8,4.8))
    for sc,g in updates.groupby('scenario',sort=False):ax.plot(g.step,g.delta,marker='o',ms=4,label=sc.replace('_',' ').title())
    ax.set_xlabel('Held-out input sample');ax.set_ylabel('Output change from approved coefficient update');
    ax.set_title('Model version change without rebuilding the mathematical graph');ax.legend()
    save(fig,a.figures,'06_parameter_update')
    fig,axs=plt.subplots(1,2,figsize=(12,4.6))
    for ax,(sc,g) in zip(axs,tinc.groupby('scenario',sort=False)):
        x=np.arange(len(g));w=(g.upper-g.lower).to_numpy()
        ax.bar(x,w*1e12,color=GREEN,width=.7);ax.set_xlabel('TINC audit sample');ax.set_title(sc.replace('_',' ').title())
        ax.set_ylabel('Reported interval width (10^-12)')
    fig.suptitle('Pointwise TINC interval diagnostics (not global certification)',fontweight='bold')
    save(fig,a.figures,'07_tinc_interval_widths')
    fig,ax=plt.subplots(figsize=(10.3,4.7))
    labels=selection.scenario.str.replace('_',' ',regex=False).str.title().tolist()
    xx=np.arange(len(selection));width=.25
    for k,(field,name,color) in enumerate([('train_mse','Training',BLUE),('validation_mse','Validation',CYAN),('test_derivative_mse','Held-out',ORANGE)]):
        ax.bar(xx+(k-1)*width,selection[field],width,label=name,color=color)
    ax.set_xticks(xx,labels);ax.set_yscale('log');ax.set_ylabel('Derivative-target mean squared error (log)')
    ax.set_title('Model-selection protocol: training and validation precede the final test');ax.legend()
    save(fig,a.figures,'08_split_errors')
    print('Generated 8 scientific diagrams (PNG + SVG)')
if __name__=='__main__':main()
