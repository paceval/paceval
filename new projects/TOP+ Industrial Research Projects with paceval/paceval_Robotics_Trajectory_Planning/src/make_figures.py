#!/usr/bin/env python3
"""Rebuild publication plots from the repository's verified synthetic CSV data.

Uses only numpy/matplotlib plus Python standard library, not paceval.
None of the graphs represents a measured industrial robot or performance data.
"""
import argparse,csv,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,FancyBboxPatch,FancyArrowPatch
plt.rcParams.update({'font.size':10,'savefig.dpi':165,'axes.spines.top':False,'axes.spines.right':False})
NAVY='#143b65';BLUE='#177bb8';TEAL='#008f91';ORANGE='#df8641';RED='#c94d55';GREY='#6c7b89'

def save(fig,out,name):
    fig.savefig(out/name,bbox_inches='tight',facecolor='white')
    plt.close(fig)

def load_csv(p):
    return list(csv.DictReader(open(p,encoding='utf-8')))

def fig_arch(out):
    fig,ax=plt.subplots(figsize=(10.6,2.8));ax.set_xlim(0,11);ax.set_ylim(0,3.5);ax.axis('off')
    boxes=[(.1,1.2,2.0,1.0,'Synthetic waypoints\n+ two-link geometry'),(2.9,1.2,2.1,1,'C++ host\ncandidate generation'),(5.8,1.2,2.1,1,'paceval SDK\n15 reusable graphs'),(8.7,1.2,2.0,1,'C++ host\nfeasibility and selection')]
    for i,(x,y,w,h,text) in enumerate(boxes):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.09',edgecolor=TEAL if i==2 else NAVY,facecolor='#eaf7f9' if i==2 else '#eef4fb',linewidth=1.5))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10,color=NAVY,weight='bold' if i==2 else 'normal')
    for a,b in [(2.2,2.75),(5.13,5.67),(8.0,8.55)]:
        ax.add_patch(FancyArrowPatch((a,1.7),(b,1.7),arrowstyle='->',mutation_scale=19,color=BLUE,lw=1.6))
    ax.add_patch(FancyBboxPatch((5.9,.1),1.9,.65,boxstyle='round,pad=.1',facecolor='#f0f8f4',edgecolor=TEAL))
    ax.text(6.85,.43,'TINC: 2 extra graphs',ha='center',va='center',fontsize=9,color=TEAL)
    ax.annotate('',xy=(6.85,1.14),xytext=(6.85,.83),arrowprops={'arrowstyle':'->','color':TEAL})
    ax.text(5.6,3.04,'API: paceval_main.h + paceval_main.cpp; external original Linux runtime',ha='center',color=NAVY,fontsize=10)
    save(fig,out,'01_execution_architecture.png')

def fig_arm(out,rows):
    fig,ax=plt.subplots(figsize=(8.0,5.4));
    for x,y,r in [(0.48,1.14,.13),(1.19,-.14,.15)]:
        ax.add_patch(Circle((x,y),r,facecolor='#ffd5cf',edgecolor=RED,lw=2,alpha=.8))
        ax.add_patch(Circle((x,y),r+.035,fill=False,edgecolor=RED,ls='--',lw=1.4,alpha=.6))
    for k,color in [(0,BLUE),(9,ORANGE),(19,TEAL)]:
        row=rows[k];q1=float(row['q1']);q2=float(row['q2']);e=(math.cos(q1),math.sin(q1));tip=(float(row['endpoint_x']),float(row['endpoint_y']))
        ax.plot([0,e[0],tip[0]],[0,e[1],tip[1]],'-o',lw=2.5,ms=5,color=color,label=f'Selected configuration at step {k}')
    ax.plot([float(r['target_x']) for r in rows],[float(r['target_y']) for r in rows],'.-',color=GREY,alpha=.7,label='Synthetic target path')
    ax.set(xlabel='x (m)',ylabel='y (m)',title='Two-link arm and sampled circular-obstacle clearance')
    ax.axis('equal');ax.grid(alpha=.18);ax.legend(fontsize=8,loc='lower left');save(fig,out,'02_planar_robot_geometry.png')

def fig_path(out,rows):
    fig,ax=plt.subplots(figsize=(7.6,4.3));
    ax.plot([float(r['target_x']) for r in rows],[float(r['target_y']) for r in rows],'--o',ms=3,color=GREY,label='Synthetic target positions')
    ax.plot([float(r['endpoint_x']) for r in rows],[float(r['endpoint_y']) for r in rows],'-o',ms=4,color=BLUE,label='Offline paceval-scored selections')
    for x,y,r in [(0.48,1.14,.13),(1.19,-.14,.15)]:ax.add_patch(Circle((x,y),r+.035,facecolor='#fce9e7',edgecolor=RED,alpha=.55))
    ax.set(xlabel='x (m)',ylabel='y (m)',title='Waypoints and selected end-effector positions')
    ax.axis('equal');ax.grid(alpha=.2);ax.legend(fontsize=9);save(fig,out,'03_waypoint_tracking.png')

def fig_angles(out,rows):
    t=np.arange(len(rows));a=np.array([float(r['q1']) for r in rows]);b=np.array([float(r['q2']) for r in rows]);
    fig,ax=plt.subplots(figsize=(8,3.8));ax.plot(t,a,'-o',ms=3,label='q1',color=BLUE);ax.plot(t,b,'-o',ms=3,label='q2',color=TEAL)
    ax.set(xlabel='Waypoint index',ylabel='Angle (rad)',title='Selected planar joint configurations')
    ax.grid(alpha=.2);ax.legend();save(fig,out,'04_joint_angles.png')

def fig_margin(out,rows):
    t=np.arange(len(rows));m=np.array([float(r['min_circle_margin_sq']) for r in rows]);
    fig,ax=plt.subplots(figsize=(8,3.7));ax.plot(t,m,'-o',color=TEAL,ms=3);ax.axhline(0,color=RED,ls='--',lw=1,label='Zero squared-clearance threshold')
    ax.set(xlabel='Waypoint index',ylabel='Minimum squared clearance (m²)',title='Planar segment/circle clearance at selected configurations')
    ax.legend(fontsize=8);ax.grid(alpha=.2);save(fig,out,'05_clearance_margins.png')

def fig_cost(out,rows):
    t=np.arange(len(rows));c=np.array([float(r['cost']) for r in rows]);e=np.array([math.hypot(float(r['endpoint_x'])-float(r['target_x']),float(r['endpoint_y'])-float(r['target_y'])) for r in rows]);
    fig,ax=plt.subplots(figsize=(8,3.7));ax.plot(t,c,color=BLUE,marker='o',ms=3,label='Tracking + joint-change cost');ax.set(xlabel='Waypoint index',ylabel='Weighted objective (illustrative units)',title='Synthetic objective and end-effector tracking error')
    ax2=ax.twinx();ax2.plot(t,e,color=ORANGE,ls='--',label='Endpoint tracking error');ax2.set_ylabel('Endpoint error (m)')
    ax.grid(alpha=.15);ax.legend(loc='upper left',fontsize=8);ax2.legend(loc='upper center',fontsize=8);save(fig,out,'06_cost_and_tracking_error.png')

def fig_jac(out,rows):
    t=np.arange(len(rows));d=np.array([float(r['jacobian_determinant']) for r in rows]);
    fig,ax=plt.subplots(figsize=(8,3.4));ax.plot(t,d,color=BLUE,marker='o',ms=3)
    ax.axhline(0,color=RED,ls='--',lw=1,label='Planar singularity: det(J)=0')
    ax.set(xlabel='Waypoint index',ylabel='det(J) (m² / rad²)',title='Analytic two-link kinematic singularity indicator')
    ax.grid(alpha=.2);ax.legend(fontsize=9);save(fig,out,'07_jacobian_determinant.png')

def fig_tinc(out,rows):
    width=np.array([float(r['tinc_upper'])-float(r['tinc_lower']) for r in rows]);
    mid=np.array([float(r['paceval_result']) for r in rows]);
    fig,ax=plt.subplots(figsize=(8,3.7));ax.semilogy(np.arange(len(rows)),width,'o-',ms=4,color=TEAL,label='Reported TINC width')
    ax.set(xlabel='Sample index',ylabel='Reported interval width (m)',title='24 pointwise TINC interval outputs (not a general certification)')
    ax.grid(alpha=.2);ax.legend(fontsize=9);save(fig,out,'08_tinc_widths.png')

def main():
    p=argparse.ArgumentParser();p.add_argument('--trajectory',required=True,type=Path);p.add_argument('--tinc',required=True,type=Path);p.add_argument('--out-dir',required=True,type=Path);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    rows=load_csv(a.trajectory);iv=load_csv(a.tinc);assert rows and len(iv)==24
    fig_arch(a.out_dir);fig_arm(a.out_dir,rows);fig_path(a.out_dir,rows);fig_angles(a.out_dir,rows);fig_margin(a.out_dir,rows);fig_cost(a.out_dir,rows);fig_jac(a.out_dir,rows);fig_tinc(a.out_dir,iv)
    print(f'PASS: created 8 mathematical/workflow diagrams from {len(rows)} trajectory rows and {len(iv)} pointwise TINC records')
if __name__=='__main__':main()
