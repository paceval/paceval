"""Scientific figures from actual exported paceval values, without invented observations."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
root=Path(__file__).resolve().parents[1]
out=root/'figures';out.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/'examples/gravity_surface.csv').open()))
o=list(csv.DictReader((root/'examples/synthetic_observations.csv').open()))
fit={r['fit']:r for r in csv.DictReader((root/'examples/inversion_summary.csv').open())}
def a(k):return np.array([float(r[k]) for r in rows]).reshape(61,61)
def finish(fig,name):
    fig.savefig(out/(name+'.png'),dpi=190,bbox_inches='tight',facecolor='white')
    fig.savefig(out/(name+'.pdf'),bbox_inches='tight',facecolor='white')
    plt.close(fig)
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'figure.facecolor':'white'})
rr=a('r_km')-6378.137;c=a('cos_colatitude');g=a('radial_km_s2')*1000
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');p=ax.plot_surface(rr,c,g,cmap='viridis',linewidth=0,antialiased=True);ax.set(xlabel='Altitude (km)',ylabel='cos(colatitude)',zlabel='Radial gravity (m/s²)',title='Degree-2 radial gravitational field');fig.colorbar(p,shrink=.60,pad=.13,label='m/s²');finish(fig,'01_radial_gravity_surface')
fig,ax=plt.subplots(figsize=(9,5.3));z=ax.contourf(rr,c,g,24,cmap='viridis');fig.colorbar(z,ax=ax,label='Radial gravity (m/s²)');ax.set(xlabel='Altitude (km)',ylabel='cos(colatitude)',title='Radial gravity: elevation and latitude dependence');finish(fig,'02_gravity_contours')
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');p=ax.plot_surface(rr,c,a('potential_km2_s2'),cmap='cividis',linewidth=0);ax.set(xlabel='Altitude (km)',ylabel='cos(colatitude)',zlabel='Potential (km²/s²)',title='Model potential from paceval');fig.colorbar(p,shrink=.65,pad=.1);finish(fig,'03_potential_surface')
fig,ax=plt.subplots(figsize=(9,5.2));q=(a('radial_km_s2')-a('monopole_km_s2'))*1e5;cs=ax.contourf(rr,c,q,24,cmap='coolwarm');fig.colorbar(cs,ax=ax,label='J2 contribution (10⁻⁵ km/s²)');ax.set(xlabel='Altitude (km)',ylabel='cos(colatitude)',title='Quadrupole correction relative to monopole');finish(fig,'04_quadrupole_contours')
fig,ax=plt.subplots(figsize=(9,5));m=a('d_g_d_j');cont=ax.contourf(rr,c,m,25,cmap='RdBu_r');fig.colorbar(cont,ax=ax,label='∂g/∂J2 (km/s² per unit J2)');ax.set(xlabel='Altitude (km)',ylabel='cos(colatitude)',title='Analytical J2 sensitivity evaluated by paceval');finish(fig,'05_j2_sensitivity')
fig,ax=plt.subplots(figsize=(9,5));truth=np.array([float(x['radial_clean_km_s2']) for x in o]);obs=np.array([float(x['radial_observed_km_s2']) for x in o]);ax.scatter(truth*1000,obs*1000,s=9,alpha=.5,label='Synthetic samples');lo=min(truth.min(),obs.min())*1000;hi=max(truth.max(),obs.max())*1000;ax.plot([lo,hi],[lo,hi],color='black',linestyle='--',label='Identity');ax.set(xlabel='Clean radial field (m/s²)',ylabel='Perturbed field (m/s²)',title='960 deterministic synthetic observations');ax.legend();finish(fig,'06_synthetic_observations')
fig,ax=plt.subplots(figsize=(9,4.9));labels=['True','Recovered (perturbed)','Recovered (clean)'];j0=np.array([float(fit[k]['j2']) for k in ['true','noisy','noiseless']]);ax.bar(labels,j0*1000,color=['#1b758b','#df9b55','#5ba591']);ax.set(ylabel='J2 (×10⁻³)',title='Two-parameter inverse recovery of the degree-2 coefficient');ax.ticklabel_format(axis='y',style='plain',useOffset=False);finish(fig,'07_recovered_j2')
fig,ax=plt.subplots(figsize=(9,5));idx=44;ax.plot(rr[:,idx],g[:,idx],label='Original degree-2 formula');ax.plot(rr[:,idx],a('scaled_version_km_s2')[:,idx]*1000,label='Revised quadrupole term (×1.1)');ax.plot(rr[:,idx],a('monopole_km_s2')[:,idx]*1000,'--',label='Monopole');ax.set(xlabel='Altitude (km)',ylabel='Radial gravity (m/s²)',title='Immutable formula variants on identical inputs');ax.legend();finish(fig,'08_versioned_forward_models')
print('Created eight genuine numerical figures as PNG and PDF')
