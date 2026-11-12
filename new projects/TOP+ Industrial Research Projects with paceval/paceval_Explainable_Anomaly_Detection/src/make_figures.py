#!/usr/bin/env python3
"""Generate scientific PNG and SVG figures from published data only."""
from pathlib import Path
import csv, argparse, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({'figure.figsize':(10,5.2),'figure.dpi':145,'font.size':10,
                     'axes.titlesize':14,'axes.labelsize':10,'savefig.bbox':'tight',
                     'grid.alpha':.18,'axes.spines.top':False,'axes.spines.right':False})

def load(path):
    with open(path,encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def save(fig,dir,name):
    fig.tight_layout(pad=2.0)
    for ext in ('png','svg'):fig.savefig(dir/(name+'.'+ext),dpi=190,facecolor='white')
    plt.close(fig)

def build(root):
    examples=root/'examples';dst=root/'figures';dst.mkdir(exist_ok=True)
    signals=load(examples/'signals.csv');scores=load(examples/'selected_scores.csv')
    selection=load(examples/'selection.csv');rules=load(examples/'model_diagnostics.csv')
    events=load(examples/'event_detection.csv');audit=load(examples/'audit_samples.csv')
    change=load(examples/'rule_update.csv');tinc=load(examples/'tinc_samples.csv')
    fig,ax=plt.subplots();group=[r for r in signals if r['channel']=='3'];x=np.array([int(r['minute']) for r in group]);
    ax.plot(x,[float(r['x']) for r in group],label='Measured sensor value',lw=1.7)
    ax.plot(x,[float(r['mu']) for r in group],label='Expected model baseline',lw=1.2)
    for a,b in [(70,76),(160,183)]:ax.axvspan(a,b,alpha=.12,label='Injected synthetic event' if a==70 else None)
    ax.set(title='Synthetic time series: spike and drift',xlabel='Sample index (1-minute intervals)',ylabel='Sensor value (synthetic units)');ax.legend(loc='upper left');ax.grid();save(fig,dst,'01_sensor_events')
    fig,ax=plt.subplots();ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
    steps=[('Sensor streams','Quality and timestamps'),('100 score graphs','paceval batch evaluation'),('Explainability','12 shared component graphs'),('Offline alarm logic','Hysteresis and metrics'),('Independent audit','110-digit reference')]
    for i,(a,b) in enumerate(steps):
        xpos=.1+i*2.02
        patch=FancyBboxPatch((xpos,1.35),1.82,1.35,boxstyle='round,pad=0.08,rounding_size=.08',ec='black',fc='0.96',linewidth=1.2)
        ax.add_patch(patch);ax.text(xpos+.91,2.24,a,ha='center',va='center',fontsize=11,weight='bold',wrap=True)
        ax.text(xpos+.91,1.79,b,ha='center',va='center',fontsize=8,wrap=True)
        if i<4:ax.annotate('',xy=(xpos+2.0,2.0),xytext=(xpos+1.85,2),arrowprops=dict(arrowstyle='->',lw=1.5))
    ax.set_title('Validated processing boundary and reusable mathematical kernels');save(fig,dst,'02_execution_architecture')
    fig,ax=plt.subplots();group=[r for r in scores if r['channel']=='3' and r['quality']=='GOOD'];xx=np.array([int(r['minute']) for r in group]);mask=(xx>=60)&(xx<=95)
    for k,label in [('deviation_component','Deviation'),('derivative_component','Change'),('context_component','Context')]:ax.plot(xx[mask],[float(r[k]) for r,m in zip(group,mask) if m],label=label)
    ax.plot(xx[mask],[float(r['score']) for r,m in zip(group,mask) if m],lw=2.8,label='Total paceval score')
    ax.axhline(float(group[0]['threshold']),linestyle='--',label='Versioned threshold')
    ax.set(title='Explainability: score components around a spike',xlabel='Sample index',ylabel='Dimensionless score');ax.legend(ncol=2);ax.grid();save(fig,dst,'03_explainable_components')
    fig,ax=plt.subplots();families=['Temperature','Vibration','Pressure','Electrical']
    x=np.arange(4);v=[float(r['validation_f1']) for r in selection];t=[float(r['test_f1']) for r in selection]
    ax.bar(x-.18,v,.36,label='Validation');ax.bar(x+.18,t,.36,label='Held-out test');ax.set_xticks(x,families)
    ax.set(ylim=(0,1.12),title='Model selection is separated from held-out evaluation',ylabel='Point-level F1 score');ax.legend();ax.grid(axis='y');save(fig,dst,'04_holdout_f1')
    fig,ax=plt.subplots();v=np.array([float(r['validation_f1']) for r in rules]).reshape(4,25)
    im=ax.imshow(v,aspect='auto',vmin=0,vmax=1,cmap='viridis');ax.set_yticks(range(4),families);ax.set(xlabel='Candidate version within formula family',title='Validation F1 across 100 formula versions')
    fig.colorbar(im,ax=ax,label='Validation F1');save(fig,dst,'05_candidate_score_map')
    fig,ax=plt.subplots();chosen=[r for r in events if r['split']=='test'];delays=[int(r['delay_samples']) for r in chosen]
    labels=[f"Ch {int(r['channel']):02d} {r['event_type']}" for r in chosen]
    ax.barh(np.arange(len(delays)),delays);ax.set_yticks(np.arange(len(delays)),labels);ax.invert_yaxis()
    ax.set(title='Detection delay for eight held-out fault events',xlabel='Samples after event onset (1 minute/sample)');ax.grid(axis='x');save(fig,dst,'06_event_detection_delays')
    fig,ax=plt.subplots();x=[int(r['minute']) for r in change];a=[float(r['old_score']) for r in change];b=[float(r['new_score']) for r in change]
    ax.plot(x,a,marker='o',markersize=3,label='v1.0');ax.plot(x,b,marker='.',label='v2.0')
    ax.set(title='Controlled change of rule 17; other 99 graphs retained',xlabel='Sample index',ylabel='Dimensionless score');ax.legend();ax.grid();save(fig,dst,'07_model_version_update')
    # Independent Decimal reference is intentionally recomputed here.
    import sys
    sys.path.insert(0,str(root/'src'))
    from validate_outputs import expected,d
    from decimal import localcontext
    with localcontext() as ctx:
        ctx.prec=110
        errors=[abs(d(r['paceval_score'])-expected(r)[0]) for r in audit]
    fig,ax=plt.subplots();ax.scatter(np.arange(len(errors)),[float(z) for z in errors],s=13)
    ax.set(title='Independent 110-digit accuracy audit (200 selected combinations)',xlabel='Audited sample',ylabel='Absolute score difference');ax.grid();save(fig,dst,'08_numerical_accuracy')
    fig,ax=plt.subplots();xx=[float(r['x']) for r in tinc]
    yy=[float(r['paceval_result']) for r in tinc]
    ax.plot(xx,yy,'o-',label='Original paceval value')
    ax.scatter(xx,[x*x+1 for x in xx],marker='x',s=22,label='Exact dyadic reference')
    ax.set(title='Separate TINC test: smooth dyadic polynomial (24 samples)',xlabel='Dyadic input x',ylabel='x² + 1');ax.grid();ax.legend();save(fig,dst,'09_tinc_control')
    fig,ax=plt.subplots();counts={'GOOD':0,'MISSING':0,'STALE':0,'BAD':0}
    for r in signals:counts[r['quality']]+=1
    ax.bar(list(counts),list(counts.values()));ax.set(title='Input-quality gating: data screened before paceval evaluation',ylabel='Number of sensor records');ax.grid(axis='y');save(fig,dst,'10_quality_gating')
    print('Saved 10 figures as PNG and SVG to',dst)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    build(p.parse_args().root)
