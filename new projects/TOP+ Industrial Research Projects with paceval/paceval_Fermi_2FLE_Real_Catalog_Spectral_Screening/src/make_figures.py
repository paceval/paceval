#!/usr/bin/env python3
"""Scientific plots: ONLY data exported from the actual NASA 2FLE FITS and paceval SDK. Concept art separately labeled."""
from pathlib import Path
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib import cm
ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
all_=pd.read_csv(ROOT/'examples/real_450_original_fits.csv').fillna({'ASSOC1':'','ASSOC3':'','class':''})
new=pd.read_csv(ROOT/'examples/real_60_original_fits.csv').fillna({'ASSOC1':'','ASSOC3':'','class':''})
curves=pd.read_csv(ROOT/'examples/real_60_paceval_spectral_samples.csv')
checks=pd.read_csv(ROOT/'examples/real_450_paceval_consistency.csv')
surface=pd.read_csv(ROOT/'examples/paceval_curvature_sensitivity_surface_HYPOTHETICAL.csv')
NAVY='#182943';BLUE='#247e9a';ORANGE='#ee9441';TEAL='#169b91'
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.titleweight':'bold','axes.labelsize':10,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','axes.grid':True,'grid.alpha':.18,'grid.linestyle':':'})
def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.16)
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',pad_inches=.16)
    plt.close(fig)

# 1 Mollweide map real sky positions -- avoid conceptual background map
fig=plt.figure(figsize=(10.5,5.15));ax=fig.add_subplot(111,projection='mollweide');ax.grid(True,alpha=.28)
lon=np.radians(((180-all_['GLON_deg'].to_numpy()+180)%360)-180);lat=np.radians(all_['GLAT_deg'].to_numpy());ax.scatter(lon,lat,s=9,c='#97abb8',alpha=.5,label='All 450 FITS entries',rasterized=True)
lonn=np.radians(((180-new['GLON_deg'].to_numpy()+180)%360)-180);latn=np.radians(new['GLAT_deg'].to_numpy());
sc=ax.scatter(lonn,latn,c=np.log10(new['TS'].to_numpy()),cmap='plasma',s=32,edgecolor='white',linewidth=.35,zorder=4,label='60 previously reported new sources');fig.colorbar(sc,ax=ax,orientation='horizontal',pad=.08,shrink=.55,label='log10 published TS (not a probability)')
ax.set_title('NASA 2FLE: original FITS galactic sky positions');ax.legend(loc='lower center',bbox_to_anchor=(.5,-.26),ncol=2,frameon=False,fontsize=8);save(fig,'01_real_fits_allsky')

# 2 60 by group real FITS
fig,ax=plt.subplots(figsize=(10.5,5.2));m=new['ASSOC3'].fillna('').str.strip().ne('');
for mask,color,label in [(~m,ORANGE,'No ASSOC3 hint (22)'),(m,TEAL,'ASSOC3 hint, unconfirmed (38)')]:
 ax.scatter(np.abs(new.loc[mask,'GLAT_deg']),new.loc[mask,'TS'],s=24+5*np.maximum(1,np.log10(new.loc[mask,'TS'])),alpha=.83,label=label,color=color,edgecolors='white',linewidth=.4)
ax.set_yscale('log');ax.set(xlabel='Absolute Galactic latitude |b| (deg)',ylabel='Original catalog detection statistic TS',title='The 60 original-FITS sources: TS versus latitude');ax.legend();save(fig,'02_real_60_TS_latitude')

# 3 reported indexes
fig,ax=plt.subplots(figsize=(10,4.9));bins=np.linspace(-3,4.5,31);ax.hist(all_['photon_index'],bins=bins,color='#b7d4dc',label='All 450',edgecolor='white');ax.hist(new['photon_index'],bins=bins,color=ORANGE,label='Selected 60',alpha=.85,edgecolor='white');ax.axvline(2,color=NAVY,linestyle='--',linewidth=1,label='Index = 2 (reference)');ax.set(xlabel='Published fitted PowerLaw_Index',ylabel='Number of sources',title='Original spectral-index parameter distributions');ax.legend();save(fig,'03_real_catalog_index_histogram')

# 4 ellipse sky area
ellipse=np.pi*new['95_ellipse_major_deg']*new['95_ellipse_minor_deg'];fig,ax=plt.subplots(figsize=(10,4.9));sc=ax.scatter(new['TS'],ellipse,c=np.abs(new['GLAT_deg']),cmap='viridis',s=44,edgecolors='white',linewidth=.4);fig.colorbar(sc,ax=ax,label='|b| (deg)');ax.set(xscale='log',yscale='log',xlabel='Original catalog TS',ylabel='Planar 95% ellipse area (deg$^2$)',title='Original 2FLE localization ellipses (planar approximation)');save(fig,'04_real_localization_ellipse_area')

# 5 example real derived spectra
fig,ax=plt.subplots(figsize=(10.5,5.4));sel=new.nlargest(7,'TS')['source_name'].tolist();colors=plt.cm.viridis(np.linspace(.09,.95,len(sel)))
for s,col in zip(sel,colors):
 d=curves[curves.source_name==s].sort_values('E_MeV');ax.plot(d.E_MeV,d.paceval_powerlaw_flux,label=s,color=col,lw=1.8)
ax.set(xscale='log',yscale='log',xlabel='Energy (MeV)',ylabel='Fitted differential photon flux (ph cm$^{-2}$ s$^{-1}$ MeV$^{-1}$)',title='paceval evaluation of real FITS fitted source spectra');ax.legend(fontsize=7,ncol=2,loc='upper right');save(fig,'05_real_paceval_spectral_curves')

# 6 real spectrum 3D source energy vs measured index? surface logs log10 flux
from mpl_toolkits.mplot3d import Axes3D
ordered=new.sort_values('TS',ascending=False).head(30)['source_name'].tolist();rows=curves[curves.source_name.isin(ordered)].copy();rows['rank']=rows.source_name.map({s:i for i,s in enumerate(ordered)});a=rows.pivot(index='rank',columns='E_MeV',values='paceval_powerlaw_flux').sort_index();XX=np.tile(a.columns.to_numpy(),(a.shape[0],1));YY=np.tile(a.index.to_numpy().reshape(-1,1),(1,a.shape[1]));Z=np.log10(a.to_numpy());fig=plt.figure(figsize=(10,5.6));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(np.log10(XX),YY,Z,cmap='viridis',linewidth=0,antialiased=True,rstride=1,cstride=2);ax.set(xlabel='log10 energy (MeV)',ylabel='Source rank by TS',zlabel='log10 fitted flux',title='Real catalog parameters evaluated by paceval (top 30 TS)');ax.view_init(elev=29,azim=-63);save(fig,'06_real_paceval_spectral_surface')

# 7 direct real catalog fitted-model integral consistency
fig,axes=plt.subplots(1,2,figsize=(11,4.9));
for ax,k,label in [(axes[0],'relative_photon_residual','Photon flux'),(axes[1],'relative_energy_residual','Energy flux')]:
 d=100*checks[k].to_numpy();ax.hist(d,bins=35,color=TEAL if 'photon' in k else ORANGE,edgecolor='white');ax.set(xlabel='(paceval formula integral / catalog field − 1) × 100 (%)',ylabel='Entries',title=label+' consistency');
fig.suptitle('Internal fitted-power-law consistency: 450 FITS sources');fig.tight_layout();save(fig,'07_real_integral_consistency')

# 8 TS bands from original FITS counts
b=np.array([new[f'TS_band_{i}'].to_numpy() for i in [1,2,3]]).T
fig,ax=plt.subplots(figsize=(10.2,4.8));counts=[int(np.sum(b[:,i]>=4)) for i in range(3)];bars=ax.bar(['FITS band 1','FITS band 2','FITS band 3'],counts,color=[BLUE,ORANGE,TEAL]);ax.bar_label(bars,padding=3);ax.set(xlabel='Three published 2FLE broad spectral bands',ylabel='Sources (of 60) with band TS ≥ 4',title='Published per-band TS availability (not line sensitivity)');ax.set_ylim(0,65);save(fig,'08_real_band_TS_availability')

# 9 purely hypothetical q surface; vivid label
E=np.sort(surface.E_MeV.unique());qs=np.sort(surface.toy_curvature_q.unique());dat=surface.pivot(index='toy_curvature_q',columns='E_MeV',values='paceval_log_ratio').sort_index();fig,ax=plt.subplots(figsize=(10.2,5));cf=ax.contourf(E,qs,dat.to_numpy(),levels=25,cmap='magma');fig.colorbar(cf,ax=ax,label='log curved / catalog power-law (hypothetical)');ax.set(xlabel='Energy (MeV)',ylabel='Hypothetical curvature parameter q',title='Mathematical what-if sensitivity, NOT fitted 2FLE curvature');save(fig,'09_hypothetical_curvature_contours')

# 10 error diag
fig,ax=plt.subplots(figsize=(10.2,5));for_names=new.nlargest(4,'TS').source_name.tolist()
for s in for_names:
 d=curves[curves.source_name==s].sort_values('E_MeV');ax.plot(d.E_MeV,100*d.paceval_fractional_error_diagnostic,lw=1.6,label=s)
ax.set(xlabel='Energy (MeV)',ylabel='Quadrature diagnostic (%)',title='Real fit parameter sensitivity; N-index covariance NOT available');ax.legend(fontsize=8);save(fig,'10_real_independent_error_diagnostic')
print('Generated 10 scientific figure pairs. FITS-real and hypothetical sources explicitly differentiated.')
