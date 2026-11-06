"""Presentation figures only (external Python; no dependency in C++ executables)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'figures'
def save(name):
    plt.tight_layout();plt.savefig(OUT/name,dpi=175,bbox_inches='tight');plt.close()

# 1: wave propagation Fourier mode in dynamic brane, multiple depths.
d=pd.read_csv(ROOT/'results/test_pulse161.csv')
fig,ax=plt.subplots(figsize=(9,4.5))
for col,label in [('h_brane','At moving brane (y=0)'),('h_yquart','y=0.75'),('h_yhalf','y=1.50')]:
    ax.plot(d['T'],d[col],label=label,lw=2)
ax.axvspan(.15,.45,alpha=.08,color='gray',label='Boundary source active')
ax.set(xlabel='Conformal bulk time T',ylabel='Dimensionless tensor-mode amplitude',
       title='v1.4: 5D wave operator on a moving FLRW brane (k=0)')
ax.grid(alpha=.2);ax.legend(fontsize=9)
save('01_moving_brane_waveform.png')

# 2: time convergence static analytic control
s=json.loads((ROOT/'validation/iteration_summary.json').read_text())['v14']
dt=np.array([.006,.003,.0015]);er=np.array([s[f'static_dt_{x}']['max_error'] for x in dt])
fig,ax=plt.subplots(figsize=(7.5,4.5))
ax.loglog(dt,er,'o-',lw=2,label='Measured max error')
ax.loglog(dt,er[0]*(dt/dt[0])**4,'--',label='Fourth-order slope')
ax.set(xlabel='Time step (requested)',ylabel='Maximum |numerical - cos(3T)|',title='v1.4 static-brane analytic control')
ax.grid(alpha=.25,which='both');ax.legend()
save('02_v14_rk4_convergence.png')

# 3: planar pulse near arrival and threshold dependence
p=pd.read_csv(ROOT/'results/planar_n61.csv')
ch=json.loads((ROOT/'validation/planar_characteristic_comparison.json').read_text())
fig,ax=plt.subplots(figsize=(9,4.7))
ax.plot(p.T if False else p['T'],np.abs(p.field_receiver),label='Numerical |field| at x=1, y=0 (61x61)')
ax.axvline(ch['ray_characteristics']['closest_edge']['bulk_T'],ls='--',label='Bulk geometric edge T=1.2584')
ax.axvline(ch['ray_characteristics']['closest_edge']['brane_T'],ls=':',label='Brane geometric edge T=1.3175')
ax.set_yscale('log');ax.set_ylim(1e-14,.01);ax.set_xlim(.75,1.56)
ax.set(xlabel='Conformal bulk time T',ylabel='|field| (arbitrary source normalization)',
       title='v1.4b: planar source, numerical precursor and geometric fronts')
ax.grid(alpha=.23,which='both');ax.legend(fontsize=8)
save('03_planar_pulse_and_characteristics.png')

# 4: explicit threshold sensitivity / not an arrival proof
fig,ax=plt.subplots(figsize=(8,4.5))
for r in ch['threshold_times_are_not_wavefront_proofs']:
  thresholds=np.array([1e-12,1e-9,1e-7,1e-6,1e-5]); times=[r[f'T_first_abs_greater_{z}'] for z in thresholds]
  ax.semilogx(thresholds,times,'o-',label=f"{r['grid']}x{r['grid']} grid")
ax.axhline(ch['ray_characteristics']['closest_edge']['bulk_T'],ls='--',label='Geometric bulk edge')
ax.axhline(ch['ray_characteristics']['closest_edge']['brane_T'],ls=':',label='Geometric brane edge')
ax.set(xlabel='Arbitrary detection amplitude threshold',ylabel='First sampled time exceeding threshold',
       title='Threshold dependence prevents a validated signal arrival claim')
ax.legend(fontsize=9);ax.grid(alpha=.23,which='both')
save('04_threshold_sensitivity.png')

# 5: model-only physical scaled geometric advance
f=pd.read_csv(ROOT/'results/cosmo_scan_13.csv');hp=json.loads((ROOT/'validation/v15_highprecision.json').read_text())
fig,ax=plt.subplots(figsize=(8,4.5))
ax.plot(f.ell_Mpc,f.geometric_advance_seconds,'o-',label='paceval stable-pair prediction')
ax.scatter([float(z['ell_Mpc']) for z in hp],[float(z['seconds']) for z in hp],s=50,
           marker='x',label='Independent 68-digit receiver roots')
ax.axhline(1.74,ls='--',label='GW170817 observed EM-GW lag 1.74 s')
ax.set(xlabel='Illustrative AdS5 curvature length ell (Mpc)',ylabel='Geometric advance (seconds)',
       title='v1.5: geometry only, NOT a physical GW arrival prediction')
ax.grid(alpha=.25);ax.legend(fontsize=9)
save('05_model_delay_vs_ell.png')

# 6: v1.5 high-precision convergence
q=summ=json.loads((ROOT/'validation/iteration_summary.json').read_text())['v15']
fig,ax=plt.subplots(figsize=(8,4.5))
for ell in ['0.1','0.535']:
    n=np.array([int(n) for n in q]);errors=np.array([q[str(x)][ell]['absolute_error_seconds'] for x in n]);
    ax.loglog(n,errors,'o-',label=f'ell={ell} Mpc')
ax.set(xlabel='Midpoint quadrature cells N',ylabel='|paceval result - high precision| (seconds)',
       title='v1.5 stable pair-integral convergence (second-order)')
ax.grid(alpha=.25,which='both');ax.legend()
save('06_v15_convergence.png')

# 7: observation nuisance profiles
fig,ax=plt.subplots(figsize=(8,4.5))
ax.semilogy(f.ell_Mpc, np.maximum(f.chi2_fixed_intrinsic0,1e-6),label='Intrinsic lag fixed to zero')
ax.semilogy(f.ell_Mpc,np.maximum(f.chi2_intrinsic_0_to_max,1e-6),label='Intrinsic lag profiled in [0, 10] s')
ax.semilogy(f.ell_Mpc,np.maximum(f.chi2_intrinsic_unrestricted,1e-6),label='Unrestricted intrinsic lag')
ax.set(xlabel='ell (Mpc)',ylabel='Illustrative chi-squared (log scale)',
       title='v1.5: assumed source-emission lag dominates the inference')
ax.grid(alpha=.22,which='both');ax.legend(fontsize=8)
save('07_emission_nuisance_degeneracy.png')

# 8: source v brane position in high-energy run
p=pd.read_csv(ROOT/'results/planar_n61.csv')
fig,ax=plt.subplots(figsize=(8.5,4.5))
ax.plot(p['T'],p.z_brane,label='Brane z(T)=1/a(T)')
ax.plot(p['T'],p.brane_comoving_x,label='Brane photon comoving reach, from T=0')
ax.axhline(1,ls=':',alpha=.65,label='Target x=1')
ax.set(xlabel='Bulk conformal T',ylabel='Dimensionless coordinate',
       title='v1.4b high-energy FLRW geometry used by the wave solver')
ax.grid(alpha=.2);ax.legend()
save('08_dynamic_background.png')
print('Generated',len(list(OUT.glob('*.png'))),'figures')
