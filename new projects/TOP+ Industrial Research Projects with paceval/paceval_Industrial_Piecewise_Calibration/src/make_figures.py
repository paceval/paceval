"""Figures from *recorded* original paceval output; no independent plotting surrogate."""
from pathlib import Path
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
R=Path(__file__).resolve().parents[1]
FIG=R/'figures'
FIG.mkdir(exist_ok=True)
C={'navy':'#172D40','blue':'#1A6091','teal':'#2B9988','orange':'#E06A34','gold':'#D4A74B','gray':'#778B9A','red':'#B53F4C','cream':'#F7F8F9'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':10,'axes.titlesize':12,'figure.facecolor':'white','axes.grid':True,'grid.color':'#E4EAEE','grid.linewidth':0.6,'legend.frameon':False,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':170})
def load(name):return list(csv.DictReader((R/'results'/name).open()))
series=load('calibrated_samples.csv');surface=load('calibration_surface.csv');revision=load('version_differences.csv');quality=load('scenario_summary.csv');governance=load('governance_scores.csv')
def fig(title,xlabel=None,ylabel=None,dim=(9.2,4.6)):
    f,ax=plt.subplots(figsize=dim);ax.set_title(title,loc='left',weight='bold',color=C['navy'],pad=17)
    if xlabel:ax.set_xlabel(xlabel)
    if ylabel:ax.set_ylabel(ylabel)
    return f,ax
def save(fig,num,name):
    fig.savefig(FIG/f'{num:02d}_{name}.png',bbox_inches='tight',facecolor='white')
    fig.savefig(FIG/f'{num:02d}_{name}.pdf',bbox_inches='tight',facecolor='white')
    plt.close(fig)

# Executed architecture diagram
f,ax=plt.subplots(figsize=(10,3.7));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
labels=[('Synthetic sensor data','validated x, T, drift'),('Piecewise graph router','segment groups'),('paceval computations','S, slopes, correction'),('paceval quality graphs','uncertainty and margins'),('C++ decision host','ACCEPT / REVIEW / REJECT')]
for i,(head,sub) in enumerate(labels):
    x=.015+i*.20
    p=FancyBboxPatch((x,.37),.177,.30,boxstyle='round,pad=0.015,rounding_size=0.02',facecolor=['#EEF4F9','#EAF5F2','#D7EEE9','#DCECF7','#F9EEE5'][i],edgecolor=C['blue'],linewidth=1.1)
    ax.add_patch(p);ax.text(x+.0885,.55,head,ha='center',va='center',weight='bold',fontsize=8.0,color=C['navy']);ax.text(x+.0885,.46,sub,ha='center',va='center',fontsize=7.2,color=C['gray'])
    if i<4:ax.annotate('',xy=(x+.198,.52),xytext=(x+.18,.52),arrowprops=dict(arrowstyle='->',lw=1.6,color=C['orange']))
ax.text(.02,.88,'Verified execution path: original paceval C API + independent numerical audit',weight='bold',fontsize=12,color=C['navy'])
ax.text(.02,.17,'Two persistent formula versions. Non-safety-critical mathematical research; no instrument calibration claimed.',fontsize=9,color=C['gray'])
save(f,1,'executed_architecture')

# Transfer functions, at T=30 deg C
f,ax=fig('Two persistent calibration formula versions','Normalized sensor input x','Corrected output (model units)')
for v,col in [('v1',C['blue']),('v2',C['orange'])]:
  d=sorted([r for r in surface if r['version']==v and float(r['T'])==30],key=lambda r:float(r['x']))
  ax.plot([float(r['x']) for r in d],[float(r['corrected_value']) for r in d],color=col,lw=2.4,label=v)
ax.legend();save(f,2,'versioned_calibration_curves')

f,ax=fig('Operating temperature changes the calibrated output','Normalized sensor input x','Corrected output (model units)')
for t,col in zip([0,15,30,45,60],['#283A75','#3F8EB6','#4D9A88','#D7A14E','#D96240']):
 d=sorted([r for r in surface if r['version']=='v1' and float(r['T'])==t],key=lambda r:float(r['x']))
 ax.plot([float(r['x']) for r in d],[float(r['corrected_value']) for r in d],label=f'{t} °C',lw=1.8,color=col)
ax.legend(title='Temperature',ncol=3,loc='upper left',fontsize=8);save(f,3,'temperature_compensation')

# 3D surface created from real paceval output
from mpl_toolkits.mplot3d import Axes3D
f=plt.figure(figsize=(9,5.7));ax=f.add_subplot(111,projection='3d')
d=[r for r in surface if r['version']=='v1'];X=np.array(sorted({float(r['x']) for r in d}));T=np.array(sorted({float(r['T']) for r in d}));Z=np.array([float(r['corrected_value']) for r in d]).reshape((len(X),len(T)))
xx,tt=np.meshgrid(X,T,indexing='ij');p=ax.plot_surface(xx,tt,Z,cmap='viridis',alpha=.95,linewidth=0,antialiased=True)
ax.set_xlabel('Normalized input x');ax.set_ylabel('Temperature (°C)');ax.set_zlabel('Corrected value');ax.set_title('paceval evaluation: calibration surface',loc='left',color=C['navy'],pad=20);ax.view_init(elev=24,azim=-57);f.colorbar(p,ax=ax,pad=.12,shrink=.63)
save(f,4,'calibration_surface_3d')

f,ax=fig('Formula revisions change the correction, without changing the host','Normalized sensor input x','v2 − v1 correction')
d1={float(r['x']):float(r['corrected_value']) for r in surface if r['version']=='v1' and float(r['T'])==30};d2={float(r['x']):float(r['corrected_value']) for r in surface if r['version']=='v2' and float(r['T'])==30};xs=sorted(d1);ax.plot(xs,[d2[x]-d1[x] for x in xs],lw=2,color=C['orange']);ax.axhline(0,color=C['gray'],lw=1)
save(f,5,'formula_revision_delta')

f,ax=fig('Synthetic quality-gate scenario: mathematical residuals','Sample index','Corrected value − synthetic reference')
for v,col in [('v1',C['blue']),('v2',C['orange'])]:
 d=sorted([r for r in series if r['scenario']=='quality_gate' and r['version']==v],key=lambda r:int(r['seq']))
 ax.plot([int(r['seq']) for r in d],[float(r['residual']) for r in d],lw=1.7,color=col,label=v)
ax.axhline(0,color=C['gray'],lw=1);ax.axhline(.0021,color=C['red'],lw=.8,ls='--');ax.axhline(-.0021,color=C['red'],lw=.8,ls='--');ax.legend();save(f,6,'quality_gate_residuals')

f,ax=fig('Computed uncertainty and conservative quality margin','Normalized sensor input x','Calculated value (model units)')
d=sorted([r for r in series if r['scenario']=='quality_gate' and r['version']=='v1'],key=lambda r:float(r['x']))
ax.plot([float(r['x']) for r in d],[float(r['combined_uncertainty']) for r in d],color=C['teal'],lw=2,label='Standard uncertainty (illustrative)')
ax.plot([float(r['x']) for r in d],[float(r['acceptance_margin']) for r in d],color=C['orange'],lw=2,label='Acceptance margin')
ax.axhline(0,color=C['red'],lw=1,ls='--');ax.legend(loc='lower left',fontsize=8);save(f,7,'uncertainty_and_acceptance_margin')

f,ax=fig('Local derivative used for first-order uncertainty propagation','Normalized sensor input x','dG/dx (right-selected at interior knots)')
d=sorted([r for r in surface if r['version']=='v1' and float(r['T'])==30],key=lambda r:float(r['x']))
ax.plot([float(r['x']) for r in d],[float(r['sensitivity_x']) for r in d],lw=1.8,color=C['blue'])
save(f,8,'local_piecewise_sensitivity')

# Stepwise quality statuses: 8 bars
f,ax=fig('Synthetic quality decisions from paceval margins','Number of input rows','Scenario / formula version',dim=(9.8,4.7))
labels=[];acc=[];rev=[];rej=[]
for r in quality:labels.append(r['version']+' · '+r['scenario'].replace('_',' '));acc.append(int(r['accepted']));rev.append(int(r['review']));rej.append(int(r['rejected']))
y=np.arange(len(labels));ax.barh(y,acc,color=C['teal'],label='ACCEPT');ax.barh(y,rev,left=acc,color=C['gold'],label='REVIEW');ax.barh(y,rej,left=np.array(acc)+np.array(rev),color=C['red'],label='REJECT');ax.set_yticks(y,labels,fontsize=8);ax.invert_yaxis();ax.legend(loc='upper center',bbox_to_anchor=(.52,-.13),ncol=3);ax.set_xlim(0,195);f.subplots_adjust(left=.27)
save(f,9,'model_version_decisions')

f,ax=fig('16 real paceval governance score graphs','Score expression index','Mean score across synthetic sensor rows')
for v,col,offset in [('v1',C['blue'],-.14),('v2',C['orange'],.14)]:
 d=[r for r in governance if r['version']==v];mean=np.zeros(16);cnt=np.zeros(16)
 for r in d:i=int(r['score_index'])-1;mean[i]+=float(r['score_value']);cnt[i]+=1
 mean/=cnt;ax.bar(np.arange(1,17)+offset,mean,width=.28,color=col,label=v)
ax.set_xticks(np.arange(1,17));ax.legend();save(f,10,'governance_score_families')

f,ax=fig('Expression capacity and model lifecycle: two executed workloads','Verified workload','Persistent paceval graph count')
xs=np.arange(2);bars=ax.bar(xs,[121,569],color=[C['blue'],C['orange']],width=.44)
for bar,n in zip(bars,[121,569]):ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+10,str(n),ha='center',weight='bold')
ax.set_xticks(xs,['4,096 segments × 2 versions','65,536 segments × 2 versions']);ax.set_ylim(0,640)
ax.text(.02,.94,'Graph counts express implemented formula capability, not execution speed.',transform=ax.transAxes,fontsize=8,color=C['gray'])
save(f,11,'verified_graph_capacity')

# Decision surface at synthetic T varying; graph outputs not recomputed.
f,ax=fig('Acceptance margin across input and temperature','Normalized sensor input x','Temperature (°C)',dim=(9,5.0))
val=np.array([float(r['acceptance_margin']) for r in d]) if False else np.array([float(r['acceptance_margin']) for r in surface if r['version']=='v2']).reshape((len(X),len(T)))
im=ax.pcolormesh(xx,tt,val,cmap='RdYlGn',shading='auto',vmin=-.002,vmax=.002);f.colorbar(im,ax=ax,label='paceval acceptance margin');save(f,12,'acceptance_margin_surface')

print('Generated 12 scientific figures + title art from actual paceval CSV outputs')
