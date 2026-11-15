#!/usr/bin/env python3
"""Research figures are derived exclusively from the executed SDK CSV artifacts."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
p=Path(__file__).resolve().parents[1]; out=p/'figures';out.mkdir(exist_ok=True)
def load(name):return list(csv.DictReader((p/'results'/name).open()))
site=load('site_summary.csv');spec=load('spectral_samples.csv');profiles=load('objective_profiles.csv');alias=load('alias_case.csv')[0]
def arr(k):return np.array([float(r[k]) for r in site])
x=arr('pixel_x').astype(int);y=arr('pixel_y').astype(int);truth=arr('true_nm');beer=arr('beer_fit_nm');film=arr('film_fit_nm'); ub=arr('beer_uncertainty_nm');uf=arr('film_local_uncertainty_nm')

def save(fig,name):
 fig.savefig(out/f'{name}.png',dpi=180,bbox_inches='tight',facecolor='white');fig.savefig(out/f'{name}.pdf',bbox_inches='tight');plt.close(fig)

def figbase(title,xlabel='',ylabel=''):
 f,ax=plt.subplots(figsize=(9,5.0));ax.set_title(title,weight='bold',pad=14);ax.set_xlabel(xlabel);ax.set_ylabel(ylabel);ax.grid(True,alpha=.2);return f,ax

# 1: actual synthetic observed optical spectra at the same site.
a=[r for r in spec if r['site_id']=='S0000'];w=np.array([float(z['wavelength_nm']) for z in a]);vt=np.array([float(z['transmission_observed']) for z in a]);vr=np.array([float(z['reflectance_observed']) for z in a]);f,ax=figbase('Two distinct optical measurement channels','Wavelength (nm)','Normalized sensor response');ax.plot(w,vt,'o-',label='Absorption transmission (measured synthetic)');ax.plot(w,vr,'s-',label='Single-layer reflectance (measured synthetic)');ax.legend();save(f,'fig01_synthetic_optical_spectra')
# 2 truth field
f,ax=figbase('Synthetic wafer coating thickness field','Wafer-grid X','Wafer-grid Y');im=ax.imshow(truth.reshape(12,12),origin='lower',interpolation='nearest',extent=[-.5,11.5,-.5,11.5]);f.colorbar(im,ax=ax,label='True thickness (nm)');save(f,'fig02_truth_thickness_map')
# 3 reconstruction field
f,ax=figbase('Recovered thickness: nine-wavelength interference fit','Wafer-grid X','Wafer-grid Y');im=ax.imshow(film.reshape(12,12),origin='lower',interpolation='nearest',extent=[-.5,11.5,-.5,11.5]);f.colorbar(im,ax=ax,label='Recovered thickness (nm)');save(f,'fig03_reconstructed_thickness_map')
# 4 objective curves
f,ax=figbase('Inverse spectral objective: search ambiguity and global candidates','Candidate film thickness (nm)','Total normalized squared residual');
for siteid in ['S0000','S0001','S0002']:
 a=[r for r in profiles if r['site_id']==siteid];ax.plot([float(r['thickness_nm']) for r in a],[float(r['normalized_objective']) for r in a],label=siteid)
ax.set_yscale('symlog',linthresh=5);ax.legend();save(f,'fig04_spectral_objective_profiles')
# 5 exactly equal one-wavelength aliases, use saved original first-site optical indexes from input
curve=load('alias_curve.csv');ds=np.array([float(r['thickness_nm']) for r in curve]);RR=np.array([float(r['reflectance']) for r in curve])
f,ax=figbase('Single-wavelength thickness alias: non-unique inverse','Candidate thickness (nm)','Reflectance at 525 nm');ax.plot(ds,RR,label='Single-band reflection model');ax.scatter([float(alias['thickness_a_nm']),float(alias['thickness_b_nm'])],[float(alias['reflectance_a']),float(alias['reflectance_b'])],s=75,zorder=5,label='Two indistinguishable thicknesses');ax.legend();save(f,'fig05_one_wavelength_alias')
# 6 sensitivity derivative map computed from recorded SDK formula and measured data reference formula grid? Requirement figures from actual paceval data, sample dR/dd from spectra across 144 sites & wavelengths; plot by sample vs wavelength.
mat=np.array([[float(r['film_dR_dd_at_truth']) for r in spec[i*9:(i+1)*9]] for i in range(144)])
f,ax=figbase('Executed paceval sensitivity across sites and wavelengths','Wavelength channel','Site index');im=ax.imshow(mat,origin='lower',aspect='auto');ax.set_xticks(range(9),[str(int(float(t['wavelength_nm']))) for t in spec[:9]],rotation=30);f.colorbar(im,ax=ax,label='dR/dd (1/nm)');save(f,'fig06_reflectance_sensitivity_map')
# 7 errors
f,ax=figbase('Thickness recovery residuals: two measurement models','Recovered minus true thickness (nm)','Number of synthetic sites');ax.hist(beer-truth,bins=25,alpha=.65,label='Beer absorption inverse');ax.hist(film-truth,bins=25,alpha=.65,label='Spectral interference inverse');ax.legend();save(f,'fig07_thickness_recovery_errors')
# 8 uncertainty map
f,ax=figbase('Model-local uncertainty proxies (assumed sensor uncertainties)','True thickness (nm)','Local uncertainty proxy (nm)');ax.scatter(truth,ub,s=17,alpha=.7,label='Beer intensity sensitivity');ax.scatter(truth,uf,s=17,alpha=.7,label='Spectral Fisher information');ax.legend();save(f,'fig08_local_uncertainty')
# 9 3D true and inverse surface
f=plt.figure(figsize=(9,6));ax=f.add_subplot(111,projection='3d');X,Y=np.meshgrid(np.arange(12),np.arange(12));ax.plot_surface(X,Y,film.reshape(12,12),cmap='viridis',edgecolor='none',alpha=.94);ax.set(xlabel='Grid X',ylabel='Grid Y',zlabel='Recovered thickness (nm)',title='Reconstructed wafer thickness landscape');ax.view_init(elev=27,azim=-62);save(f,'fig09_3d_wafer_thickness')
# 10 acceptance and margins using signed values from existing SDK outputs? Classification booleans in site_summary derived from film fit and truth target. margins = 35-abs(film-235) host computation in plotting not SDK (bad). Instead show accepted site booleans directly.
f,ax=figbase('Thickness tolerance screen by optical channel','Site index','Pass indicator (illustrative)');ax.step(range(144),arr('beer_tolerance_pass'),where='mid',label='Beer tolerance',alpha=.7);ax.step(range(144),arr('film_tolerance_pass')-.05,where='mid',label='Film tolerance (offset for clarity)',alpha=.7);ax.set_ylim(-.15,1.2);ax.legend();save(f,'fig10_illustrative_quality_window')
print('FIGURES',len(list(out.glob('fig*.png'))),'PNG and PDF')
