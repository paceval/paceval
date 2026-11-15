#!/usr/bin/env python3
"""Produce figures solely from recorded paceval output CSVs and traceable model metadata."""
from pathlib import Path
import csv,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches
from mpl_toolkits.mplot3d import Axes3D  # noqa
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'figures';OUT.mkdir(exist_ok=True)
R=BASE/'results'
def read(f):
 with (R/f).open(newline='',encoding='utf-8') as g:return list(csv.DictReader(g))
S=read('candidate_search.csv');M=read('selected_models.csv');P=read('holdout_predictions.csv');C=read('model_temperature_and_saturation_curves.csv');Z=read('integrated_reaction_profiles.csv');Q=read('model_response_surface.csv')
DARK='#122238';NAVY='#234768';TEAL='#007b85';COPPER='#e37747';GREEN='#15836e';GRAY='#64748b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':DARK,'text.color':DARK,'axes.titleweight':'bold','axes.titlesize':13,'figure.facecolor':'white','axes.grid':False})
def save(fig,name):
 fig.savefig(OUT/f'{name}.png',dpi=180,bbox_inches='tight',facecolor='white')
 fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight',facecolor='white')
 plt.close(fig)
def figax(w=8,h=4):
 fig,ax=plt.subplots(figsize=(w,h));fig.subplots_adjust(left=.11,right=.96,bottom=.14,top=.86);return fig,ax
labels=['Mass-action / thermal','B-saturation','A-saturation','B-quadratic saturation','Cross saturation']
# Architecture. Conceptual nonnumerical diagram with explicitly marked host/pavceval.
fig,ax=plt.subplots(figsize=(11,3.0));ax.set_xlim(0,11);ax.set_ylim(0,3);ax.axis('off')
boxes=[(0.13,0.52,2.0,1.9,'Synthetic data\n& source provenance','Host (C++)','#ebf0f5'),(2.36,0.52,2.1,1.9,'1,000 candidate\nrate graphs','paceval','#dff3f0'),(4.7,0.52,2.0,1.9,'Parameter fit\n& loss kernels','paceval + host','#dff3f0'),(6.95,0.52,1.84,1.9,'Constrained\nmodel selection','Host (C++)','#ebf0f5'),(9.03,0.52,1.84,1.9,'Integrated\nA + B -> P','paceval + RK4','#fcefe7')]
for x,y,w,h,txt,sub,color in boxes:
 ax.add_patch(patches.FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',linewidth=1.15,edgecolor=TEAL,facecolor=color))
 ax.text(x+w/2,y+h*.59,txt,ha='center',va='center',size=10.5,weight='bold')
 ax.text(x+w/2,y+.26,sub,ha='center',color=GRAY,size=8)
for i in range(len(boxes)-1):
 x=boxes[i][0]+boxes[i][2]+.10;xe=boxes[i+1][0]-.07
 ax.annotate('',(xe,1.45),(x,1.45),arrowprops={'arrowstyle':'->','lw':1.5,'color':TEAL})
ax.set_title('Documented function ownership and execution pathway',pad=2)
save(fig,'01_execution_architecture')
# Candidate score ranked scatter
fig,ax=figax(8,4.3)
sortedscore=np.sort(np.array([float(x['selection_score']) for x in S]))
ax.semilogy(np.arange(1,len(S)+1),sortedscore,lw=1.8,color=TEAL)
for m,color in zip(M,[COPPER,GREEN]):
 v=float(m['selection_score']);ax.axhline(v,color=color,ls='--',lw=1.5,label=m['model'])
ax.set(xlabel='Candidate rank (lowest score first)',ylabel='Validation loss + complexity penalty',title='Chemically constrained search across 1,000 rate laws')
ax.legend(frameon=False,fontsize=9);ax.grid(alpha=.16);save(fig,'02_candidate_score_landscape')
# Candidate families grouped
fig,ax=figax(9,4.4)
for i in range(5):
 values=np.array([float(x['selection_score']) for x in S if int(x['family'])==i])
 ax.boxplot(values,positions=[i],showfliers=False,patch_artist=True,boxprops={'facecolor':['#dce6ef','#d8eee9','#f5dfcf','#e2e8ef','#ede1e8'][i],'edgecolor':NAVY},medianprops={'color':COPPER,'lw':2},whiskerprops={'color':NAVY},capprops={'color':NAVY})
ax.set_xticks(range(5),labels=['Mass-action','B-saturation','A-saturation','B²-saturation','Cross'],rotation=12)
ax.set_yscale('log');ax.grid(axis='y',alpha=.15);ax.set(ylabel='Validation score, log scale',title='Evaluation landscape by constrained reaction family');save(fig,'03_model_family_scores')
# predicted vs observed (two panels)
fig,axs=plt.subplots(1,2,figsize=(10,4.2));fig.subplots_adjust(left=.08,right=.97,wspace=.27,top=.84,bottom=.18)
for ax,m,col in zip(axs,M,[COPPER,TEAL]):
 sub=[r for r in P if r['version']==m['model']];x=np.array([float(r['observed_rate']) for r in sub]);y=np.array([float(r['predicted_rate']) for r in sub]);maxval=max(x.max(),y.max())
 ax.scatter(x,y,c=col,s=15,alpha=.6,lw=0);ax.plot([0,maxval],[0,maxval],ls='--',c=NAVY,lw=1.2);ax.set_xlabel('Synthetic observed rate (mol L$^{-1}$ h$^{-1}$)');ax.set_ylabel('paceval-predicted rate');ax.set_title(m['model'].replace('_',' '),fontsize=11);ax.grid(alpha=.12)
fig.suptitle('Locked high-temperature holdout predictions, 256 cases per version',y=.985,fontsize=14,fontweight='bold');save(fig,'04_holdout_rate_predictions')
# residual vs temp
fig,ax=figax(8.5,4.3)
for m,col in zip(M,[COPPER,TEAL]):
 sub=[r for r in P if r['version']==m['model']];t=np.array([float(r['temperature_K']) for r in sub]);y=np.array([float(r['predicted_rate'])-float(r['observed_rate']) for r in sub]);ax.scatter(t,y,s=12,c=col,alpha=.56,label=m['model'].replace('_',' '))
ax.axhline(0,color=GRAY,lw=.9);ax.set(title='Holdout residuals across unseen temperatures',xlabel='Temperature (K)',ylabel='Predicted minus observed rate (mol L$^{-1}$ h$^{-1}$)');ax.legend(frameon=False);ax.grid(alpha=.15);save(fig,'05_holdout_residual_temperature')
# 3D surface two versions (data strictly paceval outputs)
fig=plt.figure(figsize=(10.2,4.9));fig.subplots_adjust(left=.02,right=.98,bottom=.07,top=.85,wspace=.04)
for j,m in enumerate(M):
 ax=fig.add_subplot(1,2,j+1,projection='3d');sub=[r for r in Q if r['version']==m['model'] and abs(float(r['temperature_K'])-340)<1e-6];x=np.array([float(r['ca_mol_L']) for r in sub]).reshape(41,41);y=np.array([float(r['cb_mol_L']) for r in sub]).reshape(41,41);v=np.array([float(r['rate_mol_L_h']) for r in sub]).reshape(41,41)
 ax.plot_surface(x,y,v,cmap='viridis',linewidth=0,alpha=.92,rstride=2,cstride=2);ax.set(xlabel='$C_A$ (mol/L)',ylabel='$C_B$ (mol/L)',zlabel='Rate',title=m['model'].replace('_',' '));ax.view_init(elev=24,azim=-58)
fig.suptitle('paceval response surfaces at 340 K',fontsize=14,fontweight='bold');save(fig,'06_rate_surfaces_3d')
# saturation scan
fig,ax=figax()
for m,col in zip(M,[COPPER,TEAL]):
 v=[r for r in C if r['version']==m['model'] and r['scan']=='saturation'];ax.plot([float(r['cb_mol_L']) for r in v],[float(r['rate_mol_L_h']) for r in v],c=col,lw=2,label=m['model'].replace('_',' '))
ax.set(title='Concentration dependence at 310 K and $C_A=1$',xlabel='$C_B$ (mol/L)',ylabel='Reaction rate (mol L$^{-1}$ h$^{-1}$)');ax.legend(frameon=False);ax.grid(alpha=.15);save(fig,'07_saturating_reactant_response')
fig,ax=figax()
for m,col in zip(M,[COPPER,TEAL]):
 v=[r for r in C if r['version']==m['model'] and r['scan']=='temperature'];ax.plot([float(r['temperature_K']) for r in v],[float(r['rate_mol_L_h']) for r in v],c=col,lw=2,label=m['model'].replace('_',' '))
ax.axvspan(341,360,color='#d8f1f1',alpha=.5,label='Holdout temperature domain');ax.set(title='Arrhenius sensitivity and out-of-training temperature region',xlabel='Temperature (K)',ylabel='Reaction rate (mol L$^{-1}$ h$^{-1}$)');ax.legend(frameon=False);ax.grid(alpha=.15);save(fig,'08_arrhenius_temperature_scan')
# concentration trajectories
fig,axs=plt.subplots(1,2,figsize=(10,4.3));fig.subplots_adjust(left=.08,right=.97,wspace=.25,top=.82,bottom=.17)
for ax,m in zip(axs,M):
 v=[r for r in Z if r['model']==m['model'] and int(r['scenario'])==1];t=[float(r['time_h']) for r in v]
 for key,col,title in [('ca_mol_L',COPPER,'Reactant A'),('cb_mol_L',NAVY,'Reactant B'),('cp_mol_L',GREEN,'Product P')]:ax.plot(t,[float(r[key]) for r in v],lw=2,color=col,label=title)
 ax.set(title=m['model'].replace('_',' '),xlabel='Reaction time (h)',ylabel='Concentration (mol/L)');ax.grid(alpha=.13)
axs[1].legend(frameon=False,loc='best');fig.suptitle('Stoichiometric A + B -> P trajectories driven by paceval RHS',fontsize=13,fontweight='bold');save(fig,'09_integrated_reaction_trajectories')
# stoichiometric conserved sum across both
fig,ax=figax()
for m,col in zip(M,[COPPER,TEAL]):
 v=[r for r in Z if r['model']==m['model'] and int(r['scenario'])==1];ax.plot([float(r['time_h']) for r in v],[float(r['ca_plus_cp']) for r in v],color=col,lw=2,label=m['model'].replace('_',' ')+' $C_A+C_P$')
ax.set(title='Integrated stoichiometric invariants',xlabel='Reaction time (h)',ylabel='Conserved total concentration (mol/L)');ax.legend(frameon=False);ax.grid(alpha=.15);save(fig,'10_stoichiometric_conservation')
# sensitivity field
fig,ax=figax(8.4,4.6)
v=[r for r in Q if r['version']==M[1]['model'] and abs(float(r['temperature_K'])-340)<1e-6];
x=np.array([float(r['ca_mol_L']) for r in v]).reshape(41,41);y=np.array([float(r['cb_mol_L']) for r in v]).reshape(41,41);z=np.array([float(r['sensitivity_cb']) for r in v]).reshape(41,41)
m=ax.contourf(x,y,z,levels=24,cmap='viridis');fig.colorbar(m,ax=ax,label='$\\partial r/\\partial C_B$ (h$^{-1}$)');ax.set(title='Selected kinetic model: analytical sensitivity to B',xlabel='$C_A$ (mol/L)',ylabel='$C_B$ (mol/L)');save(fig,'11_rate_sensitivity_map')
# margin masks
fig,axs=plt.subplots(1,2,figsize=(10.5,4.2));fig.subplots_adjust(left=.07,right=.94,wspace=.18,bottom=.17,top=.82)
for ax,m in zip(axs,M):
 v=[r for r in Q if r['version']==m['model'] and abs(float(r['temperature_K'])-340)<1e-6];x=np.array([float(r['ca_mol_L']) for r in v]).reshape(41,41);y=np.array([float(r['cb_mol_L']) for r in v]).reshape(41,41);z=np.array([float(r['rate_margin']) for r in v]).reshape(41,41);im=ax.contourf(x,y,z,levels=30,cmap='RdYlGn');ax.contour(x,y,z,levels=[0],colors='black',linewidths=1);ax.set(title=m['model'].replace('_',' '),xlabel='$C_A$ (mol/L)',ylabel='$C_B$ (mol/L)')
fig.colorbar(im,ax=axs.ravel().tolist(),label='Surrogate rate limit margin',fraction=.025,pad=.035);fig.suptitle('Hypothetical rate-envelope margins, not plant safety approvals',fontweight='bold',fontsize=13);save(fig,'12_rate_envelope_margins')
# selection score decompositions
fig,ax=figax(8,4)
mse=[float(r['holdout_normalized_loss']) for r in M];xs=np.arange(2)
ax.bar(xs,mse,color=[COPPER,TEAL],width=.56);ax.set_xticks(xs,['Restricted mass-action','Saturating selected rate']);ax.set_yscale('log');ax.set(title='Independent holdout model evaluation',ylabel='Normalized mean squared loss (log scale)');ax.grid(axis='y',alpha=.16);save(fig,'13_holdout_model_selection')
print('GENERATED',len(list(OUT.glob('[0-9][0-9]_*.png'))),'published charts + vector PDFs')
