#!/usr/bin/env python3
"""Render only actual paceval-produced CSV data to scientific PNG and vector PDF.
No numerical reference differences are shown in publication figures.
"""
from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'figures';DATA=ROOT/'results'
OUT.mkdir(exist_ok=True)
p=pd.read_csv(DATA/'profile.csv');r=pd.read_csv(DATA/'equilibria.csv');s=pd.read_csv(DATA/'scenario_surface.csv');f=pd.read_csv(DATA/'phase_plane.csv');tr=pd.read_csv(DATA/'trajectories.csv')
NAVY='#153c5a';CYAN='#037c98';ORANGE='#de752b';PURPLE='#8065af';RED='#b83a49';LIGHT='#edf4f7'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.titleweight':'bold','axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','figure.facecolor':'white','axes.grid':True,'grid.alpha':0.16,'lines.linewidth':2.15})

def save(fig,id):
 fig.savefig(OUT/(id+'.png'),dpi=220,bbox_inches='tight',pad_inches=.14)
 fig.savefig(OUT/(id+'.pdf'),bbox_inches='tight',pad_inches=.14)
 plt.close(fig)

def axbase(title,x,y):
 fig,ax=plt.subplots(figsize=(9.2,5.35));ax.set_title(title,loc='left',pad=14);ax.set_xlabel(x);ax.set_ylabel(y);return fig,ax

# 01: energy root crossing, actual reduced energy residual in K/s.
fig,ax=axbase('Steady-state thermal balance: two cooling models','Reactor temperature (K)','Reduced energy residual dT/dt (K/s)')
for v,color,lab in [(1,CYAN,'V1 | constant UA'),(2,ORANGE,'V2 | variable UA')]:
 sub=p[p.model==v];ax.plot(sub.T_K,sub.reduced_energy_K_s,color=color,label=lab)
 rr=r[(r.scenario_id=='S04_04')&(r.model==v)]
 ax.scatter(rr.root_T_K,[0]*len(rr),s=78,color=color,edgecolors='white',linewidths=1.4,zorder=4)
ax.axhline(0,color=NAVY,linewidth=1,linestyle=':');ax.set_xlim(285,377);ax.legend(frameon=False,loc='upper right');save(fig,'fig01_thermal_residual')

# 02: complete plant energy balance, exactly from graph results.
fig,ax=axbase('Heat generation, cooling and feed enthalpy','Reactor temperature (K)','Heat power (kW)')
q=p[p.model==1];ax.plot(q.T_K,q.heat_generation_W/1000,label='Reaction heat generation',color=ORANGE)
ax.plot(q.T_K,q.heat_removal_W/1000,label='Jacket heat removal',color=CYAN)
ax.plot(q.T_K,(q.heat_generation_W+q.Qflow_W)/1000,label='Reaction + sensible feed duty',color=PURPLE)
ax.axhline(0,color=NAVY,lw=1,ls=':');ax.set_xlim(290,370);ax.set_ylim(-150,1850);ax.legend(frameon=False,loc='upper left');save(fig,'fig02_energy_components')

# 03: equilibrium branches versus coolant T, shows stable and unstable statuses.
fig,ax=axbase('Equilibrium branches across coolant temperature','Coolant temperature (K)','Equilibrium reactor temperature (K)')
map_tc=s[['scenario_id','Tc_K','UA_W_per_K']].drop_duplicates();x=r.merge(map_tc,on='scenario_id')
sel=x[np.isclose(x.UA_W_per_K,16000)]
for v,color in [(1,CYAN),(2,ORANGE)]:
 for stable,m,lab in [(True,'o','Locally stable'),(False,'x','Unstable')]:
  sub=sel[(sel.model==v)&((sel.trace_s_inv<0)&(sel.det_s_inv2>0)==stable)]
  ax.scatter(sub.Tc_K,sub.root_T_K,c=color,marker=m,s=58 if stable else 56,alpha=.88,label=f'V{v}: {lab}')
ax.legend(ncol=2,frameon=False,fontsize=9);save(fig,'fig03_equilibrium_branches')

# 04: multiplicity map for each model.
fig,axs=plt.subplots(1,2,figsize=(10,4.65),sharex=True,sharey=True)
fig.suptitle('Count of stationary states across synthetic operating conditions',fontweight='bold',fontsize=13)
for v,ax in [(1,axs[0]),(2,axs[1])]:
 sub=s[s.model==v];g=sub.pivot(index='Tc_K',columns='UA_W_per_K',values='root_count').sort_index()
 im=ax.imshow(g.values,aspect='auto',origin='lower',cmap='YlGnBu',vmin=1,vmax=3,extent=[min(g.columns)-600,max(g.columns)+600,min(g.index)-1,max(g.index)+1])
 ax.set_title('V1: fixed cooling coefficient' if v==1 else 'V2: temperature-dependent coefficient',fontsize=10)
 ax.set_xlabel('UA (W/K)');ax.set_ylabel('Coolant temperature (K)')
 ax.grid(False)
cbar=fig.colorbar(im,ax=axs,fraction=.033,pad=.03);cbar.set_label('Number of equilibria');cbar.set_ticks([1,2,3]);save(fig,'fig04_multiplicity_maps')

# 05: streamlines based on genuine batch paceval RHS values.
fig,ax=axbase('Coupled species-temperature dynamics | V1','Reactor temperature (K)','Reactant concentration (mol/m³)')
sub=f[f.model==1].copy();temps=np.sort(sub.T_K.unique());cs=np.sort(sub.C_mol_m3.unique());A=sub.sort_values(['C_mol_m3','T_K'])
u=A.dT_dt_K_s.to_numpy().reshape(len(cs),len(temps));w=A.dC_dt_mol_m3_s.to_numpy().reshape(len(cs),len(temps))
# Plot vectors normalized for readability; directions originate only from paceval field.
norm=np.sqrt((u/0.05)**2+(w/2)**2)+1e-12
ax.streamplot(temps,cs,u/norm,w/norm,color=NAVY,density=1.18,linewidth=.85,arrowsize=1.1)
br=r[(r.scenario_id=='S04_04')&(r.model==1)]
for stable,m,color in [(True,'o',CYAN),(False,'X',RED)]:
 sub=br[((br.trace_s_inv<0)&(br.det_s_inv2>0))==stable];ax.scatter(sub.root_T_K,sub.C_mol_m3,s=140,color=color,marker=m,zorder=5,label='Stable equilibrium' if stable else 'Unstable equilibrium')
ax.set_xlim(290,390);ax.set_ylim(0,3000);ax.legend(frameon=False,loc='upper right');save(fig,'fig05_phase_plane')

# 06: transients plotted as genuine host-integrated paceval RHS trajectories.
fig,axs=plt.subplots(1,2,figsize=(10.25,4.45));fig.suptitle('Two-state startup transients from reusable paceval RHS graphs',fontweight='bold',fontsize=13)
for ver,ls in [(1,'-'),(2,'--')]:
 for case,color in [('IC1',CYAN),('IC2',ORANGE),('IC3',PURPLE)]:
  a=tr[(tr.model==ver)&(tr.initial_case==case)];lab=f'{case}, V{ver}'
  axs[0].plot(a.time_s,a.T_K,color=color,ls=ls,label=lab,lw=1.65)
  axs[1].plot(a.time_s,a.C_mol_m3,color=color,ls=ls,lw=1.65)
for ax,y in [(axs[0],'Temperature (K)'),(axs[1],'Concentration (mol/m³)')]:ax.set_xlabel('Time (s)');ax.set_ylabel(y)
axs[0].legend(frameon=False,fontsize=8,ncol=2);save(fig,'fig06_transients')

# 07: two independent differential sensitivity graph families.
fig,axs=plt.subplots(1,2,figsize=(10.1,4.45));fig.suptitle('Temperature-dependent sensitivities from paceval execution graphs',fontweight='bold',fontsize=13)
for ver,col in [(1,CYAN),(2,ORANGE)]:
 q=p[p.model==ver]
 axs[0].plot(q.T_K,q.dT_dUA_K_s_per_W_K*1e6,label=f'V{ver}',color=col)
 axs[1].plot(q.T_K,q.dT_dTc_per_s,label=f'V{ver}',color=col)
axs[0].set_ylabel('∂(dT/dt)/∂UA  (×10⁻⁶ K²/(s·W))')
axs[1].set_ylabel('∂(dT/dt)/∂Tc  (1/s)')
for ax in axs:ax.set_xlabel('Reactor temperature (K)');ax.set_xlim(285,390);ax.legend(frameon=False)
save(fig,'fig07_sensitivity')

# 08: single 3D plot with stable low-branch state from actual equilibrium roots.
fig=plt.figure(figsize=(8.9,5.75));ax=fig.add_subplot(111,projection='3d')
fig.suptitle('Lowest stable equilibrium in each scenario: branch transitions',fontweight='bold',fontsize=13)
x=r.merge(map_tc,on='scenario_id');q=x[(x.model==1)&(x.trace_s_inv<0)&(x.det_s_inv2>0)].sort_values('root_T_K').drop_duplicates('scenario_id')
ax.plot_trisurf(q.Tc_K,q.UA_W_per_K/1000,q.root_T_K,cmap='viridis',alpha=.90,linewidth=0.2,antialiased=True)
ax.set_xlabel('Coolant T (K)',labelpad=7);ax.set_ylabel('UA (kW/K)',labelpad=7);ax.set_zlabel('Equilibrium T (K)',labelpad=5)
ax.view_init(23,-130);save(fig,'fig08_stable_equilibrium_surface')

# 09: scores of every actual found equilibrium, cross-version comparison.
fig,ax=axbase('Mathematical screening score and equilibrium branch','Equilibrium reactor temperature (K)','Composite dimensionless screening margin')
for v,col in [(1,CYAN),(2,ORANGE)]:
 q=r[r.model==v];ax.scatter(q.root_T_K,q.screen_score,s=19,color=col,alpha=.53,label=f'V{v}')
ax.axhline(0,color=NAVY,ls=':');ax.axvline(345,color=RED,ls='--',alpha=.85,label='Illustrative T limit (345 K)')
ax.legend(frameon=False);save(fig,'fig09_screening_score')

# 10: full Jacobian criteria, mapped to actual global scenario candidate solutions.
fig,ax=axbase('Coupled Jacobian diagnostic at all equilibrium candidates','Jacobian trace (1/s)','Jacobian determinant (1/s²)')
for cond,color,lab in [((r.trace_s_inv<0)&(r.det_s_inv2>0),CYAN,'Locally asymptotically stable'),(~((r.trace_s_inv<0)&(r.det_s_inv2>0)),RED,'Not locally asymptotically stable')]:
 a=r[cond];ax.scatter(a.trace_s_inv,a.det_s_inv2,s=20,c=color,label=lab,alpha=.55)
ax.axhline(0,color=NAVY,ls=':');ax.axvline(0,color=NAVY,ls=':');ax.legend(frameon=False,fontsize=9);save(fig,'fig10_jacobian_stability')
print('Rendered 10 empirical paceval figures to',OUT)
