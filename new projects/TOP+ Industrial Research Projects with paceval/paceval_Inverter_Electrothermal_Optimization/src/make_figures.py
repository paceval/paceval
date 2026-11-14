#!/usr/bin/env python3
"""Create print-ready figures exclusively from executed paceval result CSVs.
Figure 01 is a conceptual architecture diagram, explicitly marked as such.
"""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd
P=argparse.ArgumentParser();P.add_argument('--results',type=Path,default=Path(__file__).resolve().parents[1]/'results');P.add_argument('--figures',type=Path,default=Path(__file__).resolve().parents[1]/'figures');args=P.parse_args()
F=args.figures;F.mkdir(parents=True,exist_ok=True)
D=pd.read_csv(args.results/'operating_surface.csv'); R=pd.read_csv(args.results/'inverter_results.csv');TR=pd.read_csv(args.results/'transient_profiles.csv')
assert len(D)==3362 and D.solverStatus.eq('OK').all()
BLUE='#163657';TEAL='#088C96';ORANGE='#E58335';MAGENTA='#9A5BB9';GREEN='#348C73';GRAY='#5C6672';PAL=['#17608A','#1DA8A1','#E88A3F','#8C58A3']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,'axes.titlesize':11,'axes.titleweight':'bold','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','figure.facecolor':'white','pdf.fonttype':42})
def finish(name,fig):
    fig.savefig(F/f'{name}.pdf',bbox_inches='tight')
    fig.savefig(F/f'{name}.png',dpi=190,bbox_inches='tight')
    plt.close(fig)
def surf(v,col):
    s=D[D.version==v]
    z=s.pivot(index='frequencyHz',columns='currentA',values=col).sort_index().sort_index(axis=1)
    return z.columns.to_numpy(),z.index.to_numpy(),z.to_numpy()
# Conceptual architecture; never described as an executed numerical result.
fig,ax=plt.subplots(figsize=(10,3.0));ax.set(xlim=(0,10),ylim=(0,2.6));ax.axis('off')
steps=[('Synthetic device\ninputs','I, V, f, ambient,\ncooling'),
       ('paceval\nloss graphs','Conduction, switching,\nthermal balance'),
       ('C++ root solver\nand state','Newton bracket,\nEuler sequence'),
       ('paceval\nquality graphs','Sensitivities, scores,\nmathematical margins'),
       ('Validated CSV\nresearch output','Model comparison,\nexecution trace')]
for j,(a,b) in enumerate(steps):
    x=.10+j*1.95;w=1.77
    rect=FancyBboxPatch((x,.50),w,1.36,boxstyle='round,pad=.06',facecolor='#EAF5F7' if j in (1,3) else '#F0F2F6',edgecolor=TEAL if j in (1,3) else '#9AADC0',lw=1.4)
    ax.add_patch(rect)
    ax.text(x+w/2,1.51,a,ha='center',va='center',fontsize=8.5,weight='bold',color=BLUE,linespacing=1.25)
    ax.text(x+w/2,.89,b,ha='center',va='center',fontsize=7.15,color=GRAY,linespacing=1.2)
    if j<4:ax.annotate('',xy=(x+1.96,1.15),xytext=(x+w+0.005,1.15),arrowprops={'arrowstyle':'->','color':ORANGE,'lw':1.8})
ax.text(.15,2.26,'Persistent graph versions  •  real paceval batch calls  •  independently checked outcomes',color=TEAL,fontsize=9.0)
ax.text(.15,.20,'Conceptual architecture; not a numerical research result',color=GRAY,fontsize=8,style='italic')
finish('01_architecture_concept',fig)
# All further figures are from genuine paceval-produced CSVs.
fig,ax=plt.subplots(figsize=(8.4,4.2))
r=R[R.version==2].sample(n=min(20000,len(R)//2),random_state=170)
sc=ax.scatter(r.currentA,r.frequencyHz/1000,c=r.junctionTempC,cmap='viridis',s=3,alpha=.50,vmin=20,vmax=220)
cb=fig.colorbar(sc,ax=ax);cb.set_label('Solved junction temperature (°C)')
ax.set(xlabel='Per-switch RMS current (A)',ylabel='Switching frequency (kHz)',title='Sampled synthetic operating points, model v2');finish('02_synthetic_operating_coverage',fig)
fig,ax=plt.subplots(figsize=(8.4,4.2))
s=D[(D.version==2)&(D.frequencyHz==16000)].sort_values('currentA')
ax.plot(s.currentA,s.conductionW,label='Conduction',color=TEAL,lw=2.3)
ax.plot(s.currentA,s.switchingW,label='Switching',color=ORANGE,lw=2.3)
ax.plot(s.currentA,s.totalLossW,label='Combined',color=BLUE,lw=2.4)
ax.axhline(220,color=MAGENTA,ls='--',label='Synthetic loss threshold, 220 W')
ax.set(xlabel='Per-switch RMS current (A)',ylabel='Per-switch electrical losses (W)',title='Loss composition, 16 kHz, 750 V, 35 °C, model v2');ax.legend(frameon=False,ncol=2,fontsize=8);finish('03_conduction_and_switching_loss',fig)
for v in (1,2):
    x,y,z=surf(v,'junctionTempC');X,Y=np.meshgrid(x,y)
    fig=plt.figure(figsize=(8.2,5.2));ax=fig.add_subplot(111,projection='3d')
    m=ax.plot_surface(X,Y/1000,z,cmap='turbo',linewidth=0,antialiased=True,alpha=.97)
    ax.view_init(elev=25,azim=-120);ax.set(xlabel='Current (A)',ylabel='Switching freq. (kHz)',zlabel='T junction (°C)',title=f'Steady electrothermal solution, model v{v}')
    fig.colorbar(m,ax=ax,shrink=.62,pad=.1,label='Temperature (°C)');finish(f'0{3+v}_junction_temperature_surface_v{v}',fig)
for name,col,title,cm in [('06_temperature_margin','tempMarginK','Remaining junction-temperature margin, model v2','RdYlGn'),('07_loss_margin','lossMarginW','Remaining electrical-loss allowance, model v2','RdYlGn'),('09_thermal_sensitivity','currentSensitivityKperA','Implicit dTj/dI sensitivity, model v2','viridis')]:
    x,y,z=surf(2,col);fig,ax=plt.subplots(figsize=(8.3,4.6))
    cf=ax.contourf(x,y/1000,z,levels=35,cmap=cm);fig.colorbar(cf,ax=ax,label={'tempMarginK':'Temperature margin (K)','lossMarginW':'Loss margin (W)','currentSensitivityKperA':'Thermal sensitivity (K/A)'}[col])
    if col in ('tempMarginK','lossMarginW') and z.min()<0<z.max():ax.contour(x,y/1000,z,levels=[0],colors=[BLUE],linewidths=1.5)
    ax.set(xlabel='Current (A)',ylabel='Switching frequency (kHz)',title=title);finish(name,fig)
a=D[D.version==1].set_index(['currentA','frequencyHz']);b=D[D.version==2].set_index(['currentA','frequencyHz']);delta=(b.junctionTempC-a.junctionTempC).unstack(0)
fig,ax=plt.subplots(figsize=(8.2,4.6));h=ax.contourf(delta.columns.to_numpy(),delta.index.to_numpy()/1000,delta.to_numpy(),levels=35,cmap='coolwarm');fig.colorbar(h,ax=ax,label='Tj(v2) - Tj(v1), K');ax.set(xlabel='Current (A)',ylabel='Switching frequency (kHz)',title='Direct comparison of simultaneously retained graph versions');finish('08_temperature_model_revision',fig)
fig,ax=plt.subplots(figsize=(8.3,4.2))
for v,color in [(1,TEAL),(2,ORANGE)]:
    s=D[(D.version==v)&(D.frequencyHz==16000)].sort_values('currentA')
    ax.plot(s.currentA,100*s.switchingShare,label=f'Model v{v}',color=color,lw=2)
ax.set(xlabel='Per-switch RMS current (A)',ylabel='Switching contribution to total loss (%)',title='Distribution of conduction and switching loss, 16 kHz');ax.legend(frameon=False);finish('10_switching_fraction_versioned',fig)
fig,ax=plt.subplots(figsize=(8.5,4.3));categories=['ACCEPT','REVIEW','REJECT'];barx=np.arange(3)
for v,delt,color in [(1,-.19,TEAL),(2,.19,ORANGE)]:
  s=R[R.version==v].decision.value_counts();ax.bar(barx+delt,[s.get(i,0) for i in categories],width=.36,color=color,label=f'v{v}')
ax.set_xticks(barx,categories);ax.set(ylabel='Synthetic operating cases',title='Two model versions yield distinct engineering classifications');ax.legend(frameon=False);finish('11_model_decision_distributions',fig)
fig,ax=plt.subplots(figsize=(8.5,4.2))
for v,color in [(1,TEAL),(2,ORANGE)]:
    for p,style in [(0,'-'),(1,'--'),(2,':')]:
        t=TR[(TR.version==v)&(TR.profile==p)&(TR.cooling==0)]
        ax.plot(t.timeS,t.junctionTempC,color=color,linestyle=style,label=f'v{v}, drive {p+1}',lw=1.7)
ax.set(xlabel='Simulated time (s)',ylabel='Junction temperature (°C)',title='Executed 1st-order electrothermal trajectories, cooling 0.12 K/W');ax.legend(ncol=3,fontsize=8,frameon=False);finish('12_transient_junction_temperature',fig)
fig,ax=plt.subplots(figsize=(8.4,4.1))
for v,color in [(1,TEAL),(2,ORANGE)]:
    s=TR[(TR.version==v)&(TR.profile==1)&(TR.cooling==1)]
    ax.plot(s.timeS,s.cumulativeLossJ/1000,label=f'Model v{v}',color=color,lw=2)
ax.set(xlabel='Simulated time (s)',ylabel='Cumulative per-switch loss energy (kJ)',title='Loss-energy accumulation in dynamic load profile 2');ax.legend(frameon=False);finish('13_transient_energy',fig)
fig,ax=plt.subplots(figsize=(8.3,4.5));x,y,tm=surf(2,'tempMarginK');_,_,lm=surf(2,'lossMarginW');_,_,guard=surf(2,'booleanGuard')
from matplotlib.colors import ListedColormap
z=np.where((tm<0)|(lm<0),2,np.where((tm<20)|(lm<35),1,0));X,Y=np.meshgrid(x,y)
ax.pcolormesh(X,Y/1000,z,shading='auto',cmap=ListedColormap(['#2F9D87','#EFB365','#D66266']),vmin=-.5,vmax=2.5)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#2F9D87',label='Wide positive margins'),Patch(color='#EFB365',label='Near a limit'),Patch(color='#D66266',label='Outside a limit')],frameon=False,fontsize=8,loc='upper left')
ax.set(xlabel='Current (A)',ylabel='Switching frequency (kHz)',title='Illustrative threshold-map derived from paceval operating margins');finish('14_operating_margin_regions',fig)
print(f'Generated {len(list(F.glob("*.png")))-1} plotted PNGs (plus any hero) from verified paceval CSV inputs')
