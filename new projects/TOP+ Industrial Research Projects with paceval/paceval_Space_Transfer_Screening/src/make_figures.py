#!/usr/bin/env python3
"""Eight scientific visuals, sourced from executed paceval CSVs (except indicated geometry sketch)."""
from pathlib import Path
import csv, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
records=list(csv.DictReader((ROOT/'examples'/'transfer_candidates.csv').open()))
surface=list(csv.DictReader((ROOT/'examples'/'cost_surface.csv').open()))
trade=list(csv.DictReader((ROOT/'examples'/'bielliptic_trade.csv').open()))
version=list(csv.DictReader((ROOT/'examples'/'policy_versions.csv').open()))
N=61
ratio=np.array([float(x['r2_r1_ratio']) for x in surface]).reshape(N,N)
angle=np.array([float(x['plane_change_deg']) for x in surface]).reshape(N,N)
dv=np.array([float(x['total_dv_kms']) for x in surface]).reshape(N,N)
fuel=np.array([float(x['propellant_kg']) for x in surface]).reshape(N,N)
days=np.array([float(x['time_days']) for x in surface]).reshape(N,N)
D='#162d44';TEAL='#147c81';ORANGE='#e18b45';BLUE='#306ca1'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelcolor':D,'text.color':D,'axes.titleweight':'bold','axes.edgecolor':'#8b9baa','grid.alpha':.18,'savefig.facecolor':'white'})
def save(fig,stem):
 fig.savefig(FIG/(stem+'.png'),dpi=190,bbox_inches='tight',facecolor='white')
 fig.savefig(FIG/(stem+'.pdf'),bbox_inches='tight',facecolor='white')
 plt.close(fig)
# 1. Orbit geometry: a geometric schematic based on orbit parameter values, NOT propagated ephemerides.
fig,ax=plt.subplots(figsize=(9,5.7));ax.set_facecolor('#fafcfe');r1=7000.;r2=42164.;earth=6378.137
ang=np.linspace(0,2*np.pi,600);norm=r2
ax.fill((earth/norm)*np.cos(ang),(earth/norm)*np.sin(ang),color='#92bed9',alpha=.9,zorder=4,label='Earth radius (schematic)')
ax.plot(r1/norm*np.cos(ang),r1/norm*np.sin(ang),color=BLUE,lw=1.9,label='Initial circular orbit')
ax.plot(np.cos(ang),np.sin(ang),color=TEAL,lw=2,label='Target circular orbit')
a=(r1+r2)/2;e=(r2-r1)/(r2+r1);nu=np.linspace(0,np.pi,280)
r=(a*(1-e*e)/(1+e*np.cos(nu)))/norm
ax.plot(r*np.cos(nu),r*np.sin(nu),color=ORANGE,lw=3,label='Half-ellipse transfer arc')
ax.scatter([r1/norm,-1],[0,0],color=ORANGE,s=70,zorder=10)
ax.annotate('Burn 1: injection',(r1/norm,0),(0.4,.27),arrowprops={'arrowstyle':'->','color':D},fontsize=9)
ax.annotate('Burn 2: circularization',(-1,0),(-1.15,.48),arrowprops={'arrowstyle':'->','color':D},fontsize=9)
ax.set(xlabel='Earth-centered x / target orbit radius',ylabel='Earth-centered y / target orbit radius')
ax.set_aspect('equal');ax.set_xlim(-1.33,1.29);ax.set_ylim(-1.13,1.18)
ax.set_title('Circular-orbit transfer geometry • illustrative host reconstruction');ax.legend(loc='lower right',frameon=False,fontsize=8);ax.grid(True,alpha=.15)
fig.tight_layout();save(fig,'01_orbital_transfer_geometry')
# 2 actual paceval computed response surface
fig=plt.figure(figsize=(8.5,6));ax=fig.add_subplot(111,projection='3d')
s=ax.plot_surface(ratio,angle,dv,cmap='viridis',lw=0,antialiased=True,rstride=1,cstride=1)
ax.set(xlabel='Target / initial radius',ylabel='Plane change (degrees)',zlabel='Total delta-v (km/s)')
ax.set_title('Hohmann + arrival plane change | paceval computed')
ax.view_init(elev=29,azim=-132);fig.colorbar(s,ax=ax,shrink=.64,pad=.12,label='km/s');fig.subplots_adjust(left=.00,right=.86,bottom=.01,top=.92)
save(fig,'02_deltav_surface_3d')
# 3 paceval contour
fig,ax=plt.subplots(figsize=(8.6,5.7));q=ax.contourf(ratio,angle,dv,levels=24,cmap='viridis');co=ax.contour(ratio,angle,dv,levels=[1.5,2,3,4,5,6],colors='white',alpha=.8,linewidths=.7);ax.clabel(co,inline=True,fontsize=7)
fig.colorbar(q,ax=ax,label='Total delta-v (km/s)');ax.set(xlabel='Target / initial radius',ylabel='Plane change (degrees)',title='Analytical delta-v screening region | paceval')
fig.tight_layout();save(fig,'03_deltav_contours')
# 4 fuel surface
fig=plt.figure(figsize=(8.5,6));ax=fig.add_subplot(111,projection='3d');s=ax.plot_surface(ratio,angle,fuel,cmap='plasma',lw=0,antialiased=True)
ax.set(xlabel='Target / initial radius',ylabel='Plane change (degrees)',zlabel='Propellant mass (kg)');ax.view_init(elev=27,azim=-128)
ax.set_title('Ideal rocket-equation fuel cost | 1,200 kg, Isp 340 s');fig.colorbar(s,ax=ax,shrink=.65,pad=.12,label='kg');fig.subplots_adjust(left=.00,right=.86,bottom=.01,top=.92)
save(fig,'04_propellant_surface_3d')
# 5 time-delta-v trade
fig,ax=plt.subplots(figsize=(8.6,5.2));select=[0,15,30,45,60];colors=plt.cm.viridis(np.linspace(.15,.9,5))
for k,c in zip(select,colors):ax.plot(ratio[k],dv[k],lw=2.1,color=c,label=f'{angle[k,0]:.0f}° plane change')
ax.set(xlabel='Target / initial radius',ylabel='Two-impulse delta-v (km/s)',title='Transfer radius and arrival-plane trade')
ax.legend(fontsize=8,ncol=2,frameon=False);ax.grid(True);fig.tight_layout();save(fig,'05_plane_change_sensitivity')
# 6 bielliptic comparison
x=np.array([float(q['r2_r1_ratio']) for q in trade]);ho=np.array([float(q['hohmann_coplanar_kms']) for q in trade]);bi=np.array([float(q['bielliptic_coplanar_kms']) for q in trade]);th=np.array([float(q['hohmann_days']) for q in trade]);tb=np.array([float(q['bielliptic_days']) for q in trade])
fig,ax=plt.subplots(figsize=(8.8,5.2));ax.plot(x,ho,color=TEAL,lw=2.4,label='Hohmann (two impulses)');ax.plot(x,bi,color=ORANGE,lw=2.4,label='Bi-elliptic (three impulses)');ax.fill_between(x,ho,bi,where=bi<ho,color=TEAL,alpha=.13,label='Bi-elliptic lower delta-v')
ax.set(xlabel='Target / initial radius',ylabel='Coplanar total delta-v (km/s)',title='Bi-elliptic comparison • intermediate apoapsis = 20 × target radius')
ax2=ax.twinx();ax2.plot(x,tb,ls='--',color='#7b6ca0',alpha=.6,label='Bi-elliptic flight time');ax2.plot(x,th,ls='--',color='#8a9ca5',alpha=.7,label='Hohmann flight time');ax2.set_ylabel('Transfer time (days)',color='#6b5e89')
ax.legend(loc='upper right',fontsize=8,frameon=False);ax.grid(True,alpha=.13);fig.tight_layout();save(fig,'06_bielliptic_trade')
# 7 screening decisions from *actual* candidate CSV
r=np.array([float(q['r2_km'])/float(q['r1_km']) for q in records]);vv=np.array([float(q['total_with_plane_kms']) for q in records]);good=np.array([int(q['screen_pass']) for q in records],dtype=bool)
fig,ax=plt.subplots(figsize=(8.6,5.2));ax.scatter(r[~good],vv[~good],s=8,alpha=.2,color='#c88b62',label='Host policy: review/reject');ax.scatter(r[good],vv[good],s=13,alpha=.48,color=TEAL,label='Host policy: preliminary pass');ax.axhline(5,color=D,ls='--',lw=1.1,label='Example 5 km/s constraint')
ax.set(xlabel='Target / initial radius',ylabel='Computed delta-v (km/s)',title=f'Synthetic screening: {good.sum():,} passes / {len(good):,} candidates');ax.legend(fontsize=8,frameon=False);ax.grid(True);fig.tight_layout();save(fig,'07_candidate_screening')
# 8 policy version
x=np.array([float(q['target_radius_ratio']) for q in version]);p1=np.array([float(q['policy_v1']) for q in version]);p2=np.array([float(q['policy_v2']) for q in version]);fig,ax=plt.subplots(figsize=(8.6,5.2));ax.plot(x,p1,label='Version 1: delta-v / fuel emphasis',color=TEAL,lw=2.4);ax.plot(x,p2,label='Version 2: stronger flight-time penalty',color=ORANGE,lw=2.4)
ax.fill_between(x,p1,p2,alpha=.12,color=ORANGE);ax.set(xlabel='Target / initial radius',ylabel='Dimensionless screening score',title='Two independently retained paceval policy graph versions');ax.legend(frameon=False);ax.grid(True);fig.tight_layout();save(fig,'08_policy_versions')
# 9 histogram distribution from actual cases
fig,ax=plt.subplots(figsize=(8.6,5.2));ax.hist([float(q['propellant_fraction']) for q in records],bins=48,color=TEAL,alpha=.82,edgecolor='white');ax.set(xlabel='Ideal rocket-equation propellant fraction',ylabel='Number of synthetic candidates',title='Fuel-demand distribution under declared propulsion assumptions');ax.grid(axis='y');fig.tight_layout();save(fig,'09_fuel_fraction_distribution')
print('PASS nine scientific charts (PNG and vector PDF) from real paceval data and labeled orbit geometry')
