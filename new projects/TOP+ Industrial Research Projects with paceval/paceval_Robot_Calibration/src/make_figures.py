#!/usr/bin/env python3
"""Figures from actual published CSV results; no synthetic chart values added."""
from pathlib import Path
import csv,json,argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY='#102b3c';TEAL='#087e93';GOLD='#dd7b38';GREY='#71808a';GREEN='#238e67'
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.titlesize':13,
                     'axes.labelsize':10,'figure.facecolor':'white','axes.spines.top':False,
                     'axes.spines.right':False,'savefig.facecolor':'white'})
def read(p):
    with open(p,newline='') as f:return list(csv.DictReader(f))
def save(fig,target,name):
    fig.savefig(target/(name+'.png'),dpi=190,bbox_inches='tight',pad_inches=.22)
    fig.savefig(target/(name+'.svg'),bbox_inches='tight',pad_inches=.22)
    plt.close(fig)
def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    trace=read(root/'calibration_trace.csv');pred=read(root/'holdout_predictions.csv')
    parm=read(root/'parameters.csv');spec=read(root/'observability.csv');tinc=read(root/'tinc_samples.csv')
    audit=json.loads((root/'high_precision_audit.json').read_text())
    # 01: architecture diagram, showing boundaries of engine versus host.
    fig,ax=plt.subplots(figsize=(11,3.4));ax.set_xlim(0,11);ax.set_ylim(0,3.4);ax.axis('off')
    modules=[(.1,'Measured 6R poses','q1..q6, TCP xyz',NAVY),(2.85,'paceval graphs','FK xyz + 3 residuals',TEAL),
             (5.63,'C++ calibration','LM, Jacobian, SVD',NAVY),(8.37,'Independent audit','100-digit, holdout',GREEN)]
    for x,title,sub,c in modules:
        ax.add_patch(FancyBboxPatch((x,.82),2.45,1.85,boxstyle='round,pad=.1,rounding_size=.16',facecolor=c,edgecolor='none'))
        ax.text(x+1.22,1.93,title,color='white',ha='center',fontsize=10.7,weight='bold')
        ax.text(x+1.22,1.42,sub,color='white',ha='center',fontsize=9.2)
    for x in [2.54,5.30,8.08]:
        ax.add_patch(FancyArrowPatch((x+0.02,1.73),(x+0.33,1.73),arrowstyle='-|>',mutation_scale=18,
                                     color=GOLD,linewidth=2.3))
    ax.set_title('Research workflow: reusable equations and independent calibration logic',color=NAVY,weight='bold')
    save(fig,out,'01_execution_architecture')
    # 02: 3D volume covered by training and holdout measurements.
    tr=read(root/'training_observations.csv');ho=read(root/'holdout_observations.csv')
    fig=plt.figure(figsize=(8.8,5.6));ax=fig.add_subplot(111,projection='3d')
    for rows,c,label in [(tr,TEAL,'Calibration poses'),(ho,GOLD,'Held-out poses')]:
        xyz=np.array([[float(row['m'+s+'_m']) for s in 'xyz'] for row in rows]);
        ax.scatter(xyz[:,0],xyz[:,1],xyz[:,2],s=19,c=c,alpha=.76,label=label)
    ax.set(xlabel='TCP x (m)',ylabel='TCP y (m)',zlabel='TCP z (m)')
    ax.set_title('Independent pose groups in 3D workspace',color=NAVY,weight='bold');ax.legend()
    save(fig,out,'02_workspace_poses')
    # 03: actual LM convergence.
    fig,ax=plt.subplots(figsize=(8.5,4.4))
    its=[int(r['iteration']) for r in trace];mm=[1000*float(r['training_rmse_m']) for r in trace]
    ax.plot(its,mm,color=TEAL,marker='o',lw=2.5);ax.set_yscale('log')
    ax.set(xlabel='Accepted calibration step',ylabel='Training coordinate RMSE (mm)')
    ax.grid(alpha=.22);ax.set_title('Measured Levenberg-Marquardt convergence',color=NAVY,weight='bold')
    save(fig,out,'03_calibration_convergence')
    # 04: holdout nominal vs calibrated pointwise error.
    n=np.arange(len(pred));a=np.array([float(row['nominal_error_mm']) for row in pred]);
    b=np.array([float(row['fitted_error_mm']) for row in pred])
    fig,ax=plt.subplots(figsize=(9,4.3))
    ax.plot(n,a,'.-',label='Nominal robot',color=GOLD,lw=1.5,ms=4)
    ax.plot(n,b,'.-',label='Calibrated robot',color=TEAL,lw=1.3,ms=4)
    ax.set(xlabel='Held-out pose index',ylabel='TCP error magnitude (mm)');ax.legend();ax.grid(alpha=.2)
    ax.set_title('Position error on 48 independent poses',color=NAVY,weight='bold')
    save(fig,out,'04_holdout_position_errors')
    # 05: nine fitted parameter values vs truth, normalized for units.
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(10.5,4.2))
    x=np.arange(6);trv=np.array([float(r['true']) for r in parm[:6]])*1000
    fitv=np.array([float(r['fitted']) for r in parm[:6]])*1000
    ax1.bar(x-.18,trv,.36,color=GOLD,label='True');ax1.bar(x+.18,fitv,.36,color=TEAL,label='Recovered')
    ax1.set_xticks(x,[f'J{i+1}' for i in x]);ax1.set(ylabel='Encoder offset (mrad)',title='Six encoder offsets');ax1.legend()
    x=np.arange(3);t=np.array([float(r['true']) for r in parm[6:]])*1000
    f=np.array([float(r['fitted']) for r in parm[6:]])*1000
    ax2.bar(x-.18,t,.36,color=GOLD);ax2.bar(x+.18,f,.36,color=TEAL)
    ax2.set_xticks(x,['L2','L3','L6']);ax2.set(ylabel='Length correction (mm)',title='Three link corrections')
    fig.suptitle('Recovery of the known synthetic calibration parameters',color=NAVY,weight='bold')
    fig.tight_layout();save(fig,out,'05_parameter_recovery')
    # 06: singular values independent pose design vs degenerate design.
    i=np.arange(1,10);sv=np.array([float(r['training_singular_value']) for r in spec])
    ds=np.array([float(r['degenerate_singular_value']) for r in spec])
    fig,ax=plt.subplots(figsize=(8.5,4.5))
    ax.semilogy(i,sv,'o-',color=TEAL,label='120 diverse poses',lw=2.2)
    ax.semilogy(i,np.maximum(ds,1e-12),'x--',color=GOLD,label='24 identical poses (floor at 1e-12)',lw=2)
    ax.set(xlabel='Ordered singular-value index',ylabel='Sensitivity-matrix singular value (log)');ax.legend()
    ax.grid(alpha=.22);ax.set_title('Identifiability depends on the measurement pose set',color=NAVY,weight='bold')
    save(fig,out,'06_observability_spectrum')
    # 07: distributions for evaluation across holdout.
    fig,ax=plt.subplots(figsize=(8.5,4.5))
    ax.hist(a,bins=14,color=GOLD,alpha=.67,label='Nominal error')
    ax.hist(b,bins=14,color=TEAL,alpha=.72,label='Calibrated error')
    ax.set(xlabel='TCP error magnitude (mm)',ylabel='Number of held-out poses')
    ax.set_title('Error distribution without and with calibration',color=NAVY,weight='bold');ax.legend()
    save(fig,out,'07_error_distributions')
    # 08: zero-centered pointwise interval width diagnostics; not a general proof.
    d=np.array([float(r['upper_m'])-float(r['lower_m']) for r in tinc]);
    fig,ax=plt.subplots(figsize=(8.5,4.4))
    ax.plot(np.arange(len(d)),d*1e15,'.-',color=TEAL,lw=2)
    ax.set(xlabel='Sample index',ylabel='TINC reported width (10^-15 m)')
    ax.set_title('24 raw pointwise TINC intervals for one smooth subexpression',color=NAVY,weight='bold')
    ax.grid(alpha=.2);save(fig,out,'08_tinc_widths')
    # 09: close-up of high-precision coordinate residual audit.
    fig,ax=plt.subplots(figsize=(8.5,4.3))
    ax.bar(['Absolute max difference\n100-digit reference', 'Configured tolerance'],
           [audit['max_absolute_coordinate_residual_difference_m'],3e-12],color=[TEAL,GREY])
    ax.set_yscale('log');ax.set_ylabel('Absolute difference in metres (log)')
    ax.set_title('Independent verification of all 1,008 residual components',color=NAVY,weight='bold')
    ax.grid(alpha=.2,axis='y');save(fig,out,'09_high_precision_audit')
    print('Generated 9 figures as PNG + SVG in',out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--examples',type=Path,required=True);p.add_argument('--figures',type=Path,required=True)
    a=p.parse_args();main(a.examples,a.figures)
