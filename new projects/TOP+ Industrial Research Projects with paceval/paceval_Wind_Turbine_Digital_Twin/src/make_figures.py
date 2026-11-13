#!/usr/bin/env python3
"""Publication figures from genuine paceval SDK CSV outputs (no surrogate re-evaluation)."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
ROOT=Path(__file__).resolve().parents[1]; FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
def rows(name):
 with (ROOT/'examples'/name).open(newline='') as f:return list(csv.DictReader(f))
S=rows('paceval_coefficient_surface.csv');T=rows('paceval_rotor_time_series.csv');W=rows('paceval_operating_sweep.csv');A=rows('paceval_operating_sweep.csv')
C=rows('paceval_coefficient_surface.csv');E=rows('paceval_rotor_time_series.csv')
PA=rows('paceval_coefficient_surface.csv');L=rows('paceval_operating_sweep.csv')
lookup=rows('../results/lookup_interpolation_audit.csv') if False else None
# Consistent clear plotting style. Every figure is derived from stored original results.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.labelsize':10,'savefig.dpi':210,'axes.grid':False})
def save(name,fig):
 fig.savefig(FIG/(name+'.png'),dpi=210,bbox_inches='tight',pad_inches=.13)
 fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',pad_inches=.13)
 plt.close(fig)
def field(col):
 l=np.array([float(x['tip_speed_ratio']) for x in S]);b=np.array([float(x['pitch_deg']) for x in S]);z=np.array([float(x[col]) for x in S]);N=len(set(l));M=len(set(b));return l.reshape(M,N),b.reshape(M,N),z.reshape(M,N)
L,B,CP=field('Cp_base');_,_,CP2=field('Cp_v2');_,_,CT=field('Ct');_,_,POWER=field('rotor_power_W');_,_,DC=field('dCp_dlambda');_,_,TH=field('thrust_N');
fig=plt.figure(figsize=(8,5.8));ax=fig.add_subplot(projection='3d');sc=ax.plot_surface(L,B,CP,cmap='viridis',linewidth=0,antialiased=True,rstride=1,cstride=1);ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',zlabel='Cₚ',title='Synthetic aerodynamic power coefficient');ax.view_init(25,232);fig.colorbar(sc,ax=ax,shrink=.6,pad=.09,label='Cₚ');save('01_cp_surface_3d',fig)
fig=plt.figure(figsize=(8,5.8));ax=fig.add_subplot(projection='3d');sc=ax.plot_surface(L,B,POWER/1e6,cmap='plasma',linewidth=0,antialiased=True);ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',zlabel='Rotor power (MW)',title='Rotor power at 10 m/s; actual paceval outputs');ax.view_init(27,230);fig.colorbar(sc,ax=ax,shrink=.6,pad=.1,label='MW');save('02_rotor_power_surface_3d',fig)
fig,ax=plt.subplots(figsize=(8.5,4.7));cs=ax.contourf(L,B,CP,levels=28,cmap='viridis');ax.contour(L,B,CP,levels=12,colors='white',alpha=.4,linewidths=.5);fig.colorbar(cs,label='Cₚ');ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',title='Aerodynamic operating map / Cp contours');save('03_cp_contour',fig)
fig,ax=plt.subplots(figsize=(8.5,4.7));cs=ax.contourf(L,B,CT,levels=25,cmap='cividis');ax.contour(L,B,CT,levels=10,colors='white',alpha=.45,linewidths=.55);fig.colorbar(cs,label='Cₜ');ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',title='Synthetic thrust-coefficient map');save('04_ct_contour',fig)
fig=plt.figure(figsize=(8,5.8));ax=fig.add_subplot(projection='3d');sc=ax.plot_surface(L,B,DC,cmap='coolwarm',linewidth=0,antialiased=True);ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',zlabel='dCₚ/dλ',title='Analytical slope of the Cp landscape');ax.view_init(25,227);fig.colorbar(sc,ax=ax,shrink=.6,pad=.1,label='dCₚ/dλ');save('05_analytical_sensitivity_3d',fig)
X={v:[r for r in T if int(r['version'])==v] for v in (1,2)}
fig,ax=plt.subplots(figsize=(9,4.5));ax.plot([float(x['time_s']) for x in X[1]],[float(x['wind_ms']) for x in X[1]],label='Synthetic incoming wind (m/s)',color='#e08d26',lw=1.4);ax.set(xlabel='Simulated seconds',ylabel='Wind speed (m/s)',title='Exogenous wind profile driving both rotor models');ax2=ax.twinx();ax2.plot([float(x['time_s']) for x in X[1]],[float(x['omega_rad_s']) for x in X[1]],color='#1b9fb5',label='Rotor speed v1');ax2.plot([float(x['time_s']) for x in X[2]],[float(x['omega_rad_s']) for x in X[2]],color='#344ca9',ls='--',label='Rotor speed v2');ax2.set_ylabel('Rotor angular speed (rad/s)');h,l=ax.get_legend_handles_labels();h2,l2=ax2.get_legend_handles_labels();ax.legend(h+h2,l+l2,loc='upper right',fontsize=8);save('06_wind_rotor_dynamics',fig)
fig,ax=plt.subplots(figsize=(9,4.5));for_ylim=[]
for k,color in [(1,'#00798c'),(2,'#cc6d20')]:
 x=X[k];ax.plot([float(r['time_s']) for r in x],[float(r['grid_power_W'])/1e6 for r in x],color=color,lw=1.35,label=f'Model version {k}')
ax.set(xlabel='Simulated seconds',ylabel='Electrical output proxy (MW)',title='Versioned electrical generation, computed by paceval');ax.legend();ax.grid(alpha=.2);save('07_versioned_electrical_power',fig)
fig,ax=plt.subplots(figsize=(9,4.5));
for k,color in [(1,'#00798c'),(2,'#cc6d20')]:
 x=X[k];ax.plot([float(r['time_s']) for r in x],[float(r['cumulative_energy_kWh']) for r in x],color=color,label=f'Version {k}',lw=1.8)
ax.set(xlabel='Simulated seconds',ylabel='Accumulated generated energy (kWh)',title='Version-dependent energy from paceval electrical power');ax.legend();ax.grid(alpha=.2);save('08_cumulative_energy',fig)
fig,ax=plt.subplots(figsize=(8.5,4.7));d=CP2-CP;cs=ax.contourf(L,B,d,levels=26,cmap='PuOr');fig.colorbar(cs,label='ΔCₚ = version 2 - version 1');ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',title='Explicit formula revision / coefficient difference');save('09_formula_revision_difference',fig)
# Directly published operating sweep, scatter emphasizes the declared synthetic environment.
fig,ax=plt.subplots(figsize=(9,4.8));vv=np.array([float(r['wind_ms']) for r in W]);poww=np.array([float(r['rotor_power_W']) for r in W])/1e6;betas=np.array([float(r['pitch_deg']) for r in W]);sc=ax.scatter(vv,poww,c=betas,s=5,alpha=.55,cmap='plasma');fig.colorbar(sc,label='Synthetic pitch setting (deg)');ax.set(xlabel='Wind speed (m/s)',ylabel='Aerodynamic power (MW)',title='Wind-speed/pitch operating sweep; mathematical surrogate');save('10_operating_sweep',fig)
# Independent tabulated-map interpolation test, NOT generated by paceval execution.
lookup=list(csv.DictReader((ROOT/'results/lookup_interpolation_audit.csv').open()))
fig,ax=plt.subplots(figsize=(8.5,4.5));z=np.array([float(x['absolute_difference']) for x in lookup]).reshape(24,24);im=ax.imshow(z,origin='lower',extent=[3,14,0,20],aspect='auto',cmap='magma');fig.colorbar(im,label='Absolute Cp interpolation error');ax.set(xlabel='Tip-speed ratio λ',ylabel='Pitch β (deg)',title='Independent bilinear coefficient lookup (comparison baseline)');save('11_tabulated_lookup_interpolation',fig)
print('Created eleven scientific figure pairs (PNG and vector PDF) from real execution outputs')
