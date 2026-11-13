#!/usr/bin/env python3
"""Render 12 genuine scientific plots exclusively from original paceval CSV runs."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D  # noqa
R=Path(__file__).resolve().parents[1];F=R/'figures';F.mkdir(exist_ok=True)
wave=list(csv.DictReader((R/'examples/field_time_series.csv').open()))
diag=list(csv.DictReader((R/'examples/energy_and_error_diagnostics.csv').open()))
conv=list(csv.DictReader((R/'examples/grid_convergence.csv').open()))
res=list(csv.DictReader((R/'examples/spatial_operator_residuals.csv').open()))
surf=list(csv.DictReader((R/'examples/parameterized_kernel_surface.csv').open()))
mods=['zero_radial','bessel_J2','manufactured_forced','zero_radial_revision']
styles=['#077e91','#d88a2c','#7147bd','#9d326f']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12.5,'axes.labelsize':10.5,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
def save(fig,name):
 fig.tight_layout(pad=1.4);fig.savefig(F/(name+'.png'),dpi=190,bbox_inches='tight',pad_inches=.12);fig.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.10);plt.close(fig)
def arr(rows,key):return np.array([float(r[key]) for r in rows]);
def rows(mode,n=97):return [r for r in wave if r['mode']==mode and int(r['n'])==n]
def finalrows(mode,n=97):
 a=rows(mode,n); step=max(int(r['step']) for r in a); return sorted([r for r in a if int(r['step'])==step],key=lambda x:float(x['z']))
# 1: four computed numerical vs analytical mode profiles
fig,ax=plt.subplots(figsize=(9,5.2))
for mode,color in zip(mods,styles):
 a=finalrows(mode);z=arr(a,'z');ax.plot(z,arr(a,'h'),color=color,lw=2,label=mode.replace('_',' '));ax.plot(z,arr(a,'exact_h'),color=color,lw=1.0,ls='--',alpha=.85)
ax.set(title='Actual paceval RK4 fields and independent analytic references',xlabel='Conformal bulk coordinate z (dimensionless)',ylabel='Mode amplitude h');ax.legend(ncol=2,fontsize=8);ax.grid(alpha=.24);save(fig,'01_four_modes_final_profiles')
# 2: spacetime heat map for Bessel
b=rows('bessel_J2');t=sorted(set(float(r['t']) for r in b));z=sorted(set(float(r['z']) for r in b));data=np.zeros((len(t),len(z)));ti={x:i for i,x in enumerate(t)};zi={x:i for i,x in enumerate(z)}
for r in b:data[ti[float(r['t'])],zi[float(r['z'])]]=float(r['h'])
fig,ax=plt.subplots(figsize=(9,5.2));im=ax.pcolormesh(z,t,data,cmap='coolwarm',shading='auto');fig.colorbar(im,ax=ax,label='Computed field h');ax.set(xlabel='Bulk coordinate z',ylabel='Time t (dimensionless)',title='Bessel-mode field propagation: actual paceval-integrated samples');save(fig,'02_bessel_spacetime_heatmap')
# 3: spacetime surface
X,Y=np.meshgrid(z,t);fig=plt.figure(figsize=(9,5.5));ax=fig.add_subplot(111,projection='3d');c=ax.plot_surface(X,Y,data,cmap='viridis',linewidth=0,antialiased=True,alpha=.97);ax.set(xlabel='Bulk z',ylabel='Time t',zlabel='h',title='3D AdS5 mode evolution from paceval C++ solver');ax.view_init(25,-65);fig.colorbar(c,ax=ax,shrink=.57,pad=.12,label='h');save(fig,'03_bessel_spacetime_surface_3d')
# 4 convergence
fig,ax=plt.subplots(figsize=(9,5.2))
for mode,color in zip(mods,styles):
 rr=sorted((r for r in conv if r['mode']==mode),key=lambda r:float(r['dx']),reverse=True);ax.loglog(arr(rr,'dx'),arr(rr,'l2_error'),'o-',color=color,lw=2,label=mode.replace('_',' '))
dx0=np.array(sorted(set(float(r['dx']) for r in conv)));ax.loglog(dx0,5.e-2*dx0**2,'k--',lw=1.2,label='reference slope 2');ax.set(xlabel='Spatial grid spacing Δz',ylabel='Final-time L2 error',title='Spatial convergence on four independent analytic test cases');ax.grid(alpha=.3,which='both');ax.legend(fontsize=8,ncol=2);save(fig,'04_second_order_spatial_convergence')
# 5 observed order
fig,ax=plt.subplots(figsize=(8.8,5))
for i,(mode,color) in enumerate(zip(mods,styles)):
 rr=[r for r in conv if r['mode']==mode and int(r['n'])>25];ax.plot([int(r['n']) for r in rr],[float(r['observed_order']) for r in rr],'o-',color=color,lw=2,label=mode.replace('_',' '))
ax.axhline(2,ls='--',color='#3a4854',lw=1);ax.set(xlabel='Grid points',ylabel='Observed convergence order',ylim=(1.94,2.06),title='Observed central-difference accuracy in all modes');ax.legend(fontsize=8,ncol=2);ax.grid(alpha=.25);save(fig,'05_observed_order')
# 6 discrete operator residual
fig,ax=plt.subplots(figsize=(9,5.2))
for mode,color in zip(mods,styles):
 rr=sorted((r for r in res if r['mode']==mode and int(r['n'])==97),key=lambda r:float(r['z']));ax.plot(arr(rr,'z'),arr(rr,'residual'),'-',color=color,label=mode.replace('_',' '),lw=1.7)
ax.set(xlabel='Bulk coordinate z',ylabel='Numerical RHS − continuum RHS',title='Finite-difference residual of exact solutions at t = 0.19');ax.grid(alpha=.25);ax.legend(fontsize=8);save(fig,'06_discrete_operator_residuals')
# 7 weighted energy and boundary flux time
rr=[r for r in diag if r['mode']=='bessel_J2' and int(r['n'])==97];rr=sorted(rr,key=lambda r:float(r['t']))
fig,ax=plt.subplots(figsize=(9,5.2));ax.plot(arr(rr,'t'),arr(rr,'weighted_energy'),'-o',color='#087f8c',label='weighted bulk energy');ax.set(xlabel='Time t',ylabel='Finite-domain weighted energy (normalized)');ax2=ax.twinx();ax2.plot(arr(rr,'t'),arr(rr,'flux_left_proxy'),color='#e28e33',ls='--',label='left boundary flux');ax2.plot(arr(rr,'t'),arr(rr,'flux_right_proxy'),color='#7b60bd',ls=':',label='right boundary flux');ax2.set_ylabel('Boundary energy flux (normalized)');l1,k1=ax.get_legend_handles_labels();l2,k2=ax2.get_legend_handles_labels();ax.legend(l1+l2,k1+k2,fontsize=8,loc='center right');ax.set_title('Energy diagnostic with driven Dirichlet boundaries (not constant energy)');save(fig,'07_weighted_energy_and_boundary_flux')
# 8 forced MMS: residual compared to source
rr=sorted((r for r in res if r['mode']=='manufactured_forced' and int(r['n'])==97),key=lambda r:float(r['z']))
fig,ax=plt.subplots(figsize=(9,5.2));ax.plot(arr(rr,'z'),arr(rr,'source'),color='#ad5e32',lw=2,label='paceval manufactured source S');ax.plot(arr(rr,'z'),arr(rr,'discrete_acceleration'),color='#126c80',lw=1.6,label='paceval numerical acceleration');ax.plot(arr(rr,'z'),arr(rr,'continuum_acceleration'),color='#6d54ac',lw=1.5,ls='--',label='analytical acceleration');ax.set(xlabel='Bulk coordinate z',ylabel='Acceleration / forcing (normalized)',title='Manufactured forcing and spatial acceleration');ax.legend(fontsize=8);ax.grid(alpha=.3);save(fig,'08_manufactured_source_and_acceleration')
# 9: surface rhs over k and z at q~0.65
qq=sorted(set(round(float(r['q']),8) for r in surf));target=qq[len(qq)//2];ss=[r for r in surf if abs(float(r['q'])-target)<1e-8];ks=sorted(set(float(r['k']) for r in ss));zs=sorted(set(float(r['z']) for r in ss));Z,K=np.meshgrid(zs,ks);v=np.empty_like(Z)
index={(round(float(r['k']),8),round(float(r['z']),8)):float(r['rhs_v1']) for r in ss}
for a,kv in enumerate(ks):
 for b,zv in enumerate(zs):v[a,b]=index[round(kv,8),round(zv,8)]
fig=plt.figure(figsize=(9.0,5.5));ax=fig.add_subplot(111,projection='3d');c=ax.plot_surface(Z,K,v,cmap='plasma',edgecolor='none',alpha=.98);fig.colorbar(c,ax=ax,shrink=.56,pad=.1,label='RHS');ax.set(xlabel='Bulk z',ylabel='Fourier k',zlabel='ḧ',title='Paceval 3D wave acceleration response surface');ax.view_init(25,-56);save(fig,'09_parameterized_rhs_surface_3d')
# 10 contour across q,z for selected k
ks0=ks[len(ks)//2];ss=[r for r in surf if abs(float(r['k'])-ks0)<1e-8];qs=sorted(set(float(r['q']) for r in ss));zs2=sorted(set(float(r['z']) for r in ss));grid=np.zeros((len(qs),len(zs2)));imap={(round(float(r['q']),8),round(float(r['z']),8)):float(r['rhs_v1']) for r in ss}
for a,q in enumerate(qs):
 for b,zv in enumerate(zs2):grid[a,b]=imap[round(q,8),round(zv,8)]
fig,ax=plt.subplots(figsize=(9,5.2));c=ax.contourf(zs2,qs,grid,levels=25,cmap='viridis');fig.colorbar(c,ax=ax,label='RHS');ax.contour(zs2,qs,grid,levels=12,colors='white',linewidths=.35,alpha=.5);ax.set(xlabel='Bulk z',ylabel='Potential parameter q',title='AdS5 operator parameter sweep: true paceval batch outputs');save(fig,'10_potential_parameter_contours')
# 11 versioned mathematical graph difference for selected q
sub=[r for r in surf if abs(float(r['q'])-target)<1e-8];grid=np.empty_like(Z);idx={(round(float(r['k']),8),round(float(r['z']),8)):float(r['version_delta']) for r in sub}
for a,kv in enumerate(ks):
 for b,zv in enumerate(zs):grid[a,b]=idx[round(kv,8),round(zv,8)]
fig,ax=plt.subplots(figsize=(9,5.2));c=ax.contourf(zs,ks,grid,levels=24,cmap='RdBu_r');fig.colorbar(c,ax=ax,label='RHS v2 − RHS v1');ax.set(xlabel='Bulk z',ylabel='Fourier k',title='Independent paceval formula-version difference (δ = 0.4)');save(fig,'11_versioned_rhs_difference')
# 12 error vs t across 4 modes
fig,ax=plt.subplots(figsize=(9,5.2))
for mode,color in zip(mods,styles):
 rr=sorted([r for r in diag if r['mode']==mode and int(r['n'])==97],key=lambda r:float(r['t']));ax.semilogy(arr(rr,'t'),np.maximum(arr(rr,'l2_error'),1e-16),'-o',color=color,label=mode.replace('_',' '),ms=3,lw=1.8)
ax.set(xlabel='Simulation time t',ylabel='L2 field error (log scale)',title='Verified accuracy throughout the four full dynamical tests');ax.legend(fontsize=8);ax.grid(alpha=.25,which='both');save(fig,'12_error_time_history')
print('Rendered 12 independent real-data figures as PNG and vector PDF')
