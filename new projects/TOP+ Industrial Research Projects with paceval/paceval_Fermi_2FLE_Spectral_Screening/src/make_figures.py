#!/usr/bin/env python3
"""Generate numbered scientific figures from REAL paceval output CSVs and user PDF metadata.
All model-dependent spectral figures concern synthetic mock spectra ONLY.
No sky map in this project is presented as a measured gamma-ray intensity map.
"""
from pathlib import Path
import csv, numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import MaxNLocator
R=Path(__file__).resolve().parents[1];D=R/'examples';F=R/'figures';F.mkdir(exist_ok=True)
metadata=list(csv.DictReader((D/'unidentified_60_from_user_whitepaper.csv').open()))
recovery=list(csv.DictReader((D/'synthetic_injection_recovery.csv').open()))
scan=list(csv.DictReader((D/'synthetic_curvature_parameter_scan.csv').open()))
surface=list(csv.DictReader((D/'synthetic_spectral_surface.csv').open()))
mock=list(csv.DictReader((D/'synthetic_photon_counts.csv').open()))
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'figure.dpi':115,'savefig.dpi':220,'axes.grid':True,'grid.alpha':.2})
def save(fig,name):
 fig.savefig(F/(name+'.png'),bbox_inches='tight',pad_inches=.2,dpi=220)
 fig.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.2)
 plt.close(fig)
 print(name)

# Genuine catalog metadata derived from user supplied report, NOT original FITS.
fig,ax=plt.subplots(figsize=(8.5,5.4))
for flag,mark,color,label in [('no_ASSOC3','o','#F1A64E','No ASSOC3 hint (22)'),('has_ASSOC3','s','#1DAFA5','ASSOC3 hint, unconfirmed (38)')]:
 a=[r for r in metadata if r['ASSOC3_flag']==flag]
 ax.scatter([abs(float(r['galactic_latitude_deg'])) for r in a],[float(r['catalog_TS']) for r in a],marker=mark,s=57,c=color,edgecolors='#202F42',lw=.5,alpha=.83,label=label)
ax.set(yscale='log',xlabel='Absolute Galactic latitude |b| (degrees)',ylabel='Published catalog test statistic TS',title='All 60 source metadata records transcribed from the user paper')
ax.legend(loc='best',fontsize=9);fig.text(.02,.01,'ASSOC3 is a follow-up hint, not a confirmed identification or origin label.',fontsize=8,color='#555')
save(fig,'01_catalog_TS_vs_latitude')

fig,ax=plt.subplots(figsize=(8,5.3))
bands=[1,2,3];a=[sum(int(x['usable_band_count_TS_ge_4'])==i and x['ASSOC3_flag']=='no_ASSOC3' for x in metadata) for i in bands];b=[sum(int(x['usable_band_count_TS_ge_4'])==i and x['ASSOC3_flag']=='has_ASSOC3' for x in metadata) for i in bands]
x=np.arange(len(bands));ax.bar(x-.18,a,.36,label='No ASSOC3 hint',color='#EEA64D');ax.bar(x+.18,b,.36,label='Unconfirmed ASSOC3 hint',color='#26A7A5')
ax.set_xticks(x,bands);ax.set(xlabel='Number of usable broad spectral bands (band TS >= 4)',ylabel='Catalog metadata source count',title='Spectral information is limited to at most three broad bands')
for k,v in enumerate(a):ax.text(k-.18,v+.3,str(v),ha='center',fontsize=9)
for k,v in enumerate(b):ax.text(k+.18,v+.3,str(v),ha='center',fontsize=9)
ax.legend();save(fig,'02_catalog_band_availability')

E=np.array([float(r['energy_MeV']) for r in surface]).reshape(65,65)
Q=np.array([float(r['curvature_q']) for r in surface]).reshape(65,65)
Z=np.array([float(r['flux_lp_v1']) for r in surface]).reshape(65,65)
RATIO=np.array([float(r['log_flux_ratio']) for r in surface]).reshape(65,65)
fig=plt.figure(figsize=(8.2,5.9));ax=fig.add_subplot(111,projection='3d');pl=ax.plot_surface(E,Q,np.log10(Z),cmap='viridis',rstride=2,cstride=2,linewidth=0,antialiased=True)
ax.view_init(elev=27,azim=-61);ax.set(xlabel='Energy (MeV)',ylabel='Synthetic curvature q',zlabel='log10(model flux)',title='Computed log-parabolic spectrum: 65 x 65 paceval evaluations');fig.colorbar(pl,ax=ax,shrink=.72,pad=.12,label='log10(arb. synthetic flux)');save(fig,'03_synthetic_logparabola_surface')

fig,ax=plt.subplots(figsize=(8,5.25));p=ax.contourf(E,Q,RATIO,levels=24,cmap='magma');ax.contour(E,Q,RATIO,levels=7,colors='white',linewidths=.55,alpha=.6);fig.colorbar(p,ax=ax,label='ln[ F_logparabola / F_powerlaw ]')
ax.set(xlabel='Energy (MeV)',ylabel='Synthetic curvature q',title='Analytic flux-ratio contours computed by paceval');save(fig,'04_synthetic_curvature_contours')

fig,ax=plt.subplots(figsize=(8,5.25));qidx=32;sl=slice(qidx,65*65,65) # selected q index in each energy row
ax.plot(E[:,qidx],np.array([float(r['flux_powerlaw']) for r in surface]).reshape(65,65)[:,qidx],lw=2,label='Power law')
for key,label in [('flux_lp_v1','Log parabola v1'),('flux_lp_v2','Log parabola v2')]:ax.plot(E[:,qidx],np.array([float(r[key]) for r in surface]).reshape(65,65)[:,qidx],lw=2,label=label)
ax.set(xscale='log',yscale='log',xlabel='Energy (MeV)',ylabel='Synthetic model flux (arbitrary units)',title='Mathematical model families at q = 0.30');ax.legend();save(fig,'05_synthetic_model_families')

fig,ax=plt.subplots(figsize=(8.2,5.2))
for i in [0,1,2]:
 name=metadata[i]['source_name'];rows=[r for r in scan if r['source_name']==name]
 xx=np.array([float(r['trial_q']) for r in rows]);yy=np.array([float(r['synthetic_loglikelihood_lp']) for r in rows]);yy=2*(yy.max()-yy)
 ax.plot(xx,yy,lw=2,label=f'Synthetic truth q={float(rows[0]["truth_q"]):.2f}')
ax.set(xlabel='Trial curvature q',ylabel='2 [max toy log-likelihood - toy log-likelihood(q)]',title='Fixed-grid curvature objectives on three synthetic mock spectra');ax.legend();save(fig,'06_synthetic_curvature_likelihood_scans')

fig,ax=plt.subplots(figsize=(8,5.3));truth=np.array([float(x['truth_q']) for x in recovery]);found=np.array([float(x['best_grid_q']) for x in recovery]);ax.scatter(truth,found,c='#178F9D',s=58,alpha=.75,edgecolors='white');ax.plot([0,.55],[0,.55],'k--',lw=1,label='Perfect recovery');ax.set(xlim=(-.03,.52),ylim=(-.03,.58),xlabel='Injected synthetic curvature',ylabel='Best fitted curvature on fixed grid',title='Synthetic injection-recovery using paceval Poisson contributions');ax.legend();save(fig,'07_synthetic_injection_recovery')

fig,ax=plt.subplots(figsize=(8,5.2));for_plot={0:[],.17:[],.4:[]}
for r in recovery:for_plot[float(r['truth_q'])].append(float(r['best_grid_q']))
positions=[0,.17,.4];ax.boxplot([for_plot[k] for k in positions],positions=np.arange(3),widths=.5,showmeans=True,patch_artist=True,boxprops={'facecolor':'#75CBD0'});ax.set_xticks(np.arange(3),[str(x) for x in positions]);ax.set(xlabel='Injected synthetic curvature q',ylabel='Recovered curvature q',title='Recovery variability across 20 synthetic sources per group');save(fig,'08_synthetic_recovery_by_group')

fig,ax=plt.subplots(figsize=(8.2,5.25));rows=[r for r in mock if r['source_name']==metadata[0]['source_name']];energy=[float(r['energy_center_MeV']) for r in rows];counts=[float(r['synthetic_observed_counts']) for r in rows];ax.scatter(energy,counts,label='Poisson-drawn synthetic counts',c='#F2A951',s=27,zorder=3)
mu=np.array([float(r['paceval_expected_counts_truth']) for r in rows]);ax.plot(energy,mu,c='#0B839D',lw=2,label='True mock expectation evaluated by paceval')
ax.set(xscale='log',xlabel='Synthetic energy-bin center (MeV)',ylabel='Synthetic counts / bin',title='Synthetic mock example (not observed 2FLE photon counts)');ax.legend();save(fig,'09_synthetic_photon_bin_example')

fig,ax=plt.subplots(figsize=(8,5.2));d=np.array([float(r['sensitivity_logflux_dq']) for r in surface]).reshape(65,65);ax.plot(E[:,0],d[:,0],color='#AD5FDD',lw=2.5);ax.axhline(0,c='gray',lw=1);ax.set(xscale='log',xlabel='Energy (MeV)',ylabel='Derivative d ln F / dq',title='Analytic curvature sensitivity evaluated with paceval');save(fig,'10_analytical_curvature_sensitivity')
print('PASS: 10 plots from paceval results or transcribed PDF metadata')
