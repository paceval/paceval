#!/usr/bin/env python3
"""Independent 80-digit mpmath audit of actual paceval CSV outputs (no SDK calls)."""
from pathlib import Path
import csv,json
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parent.parent
R=ROOT/'results';E=ROOT/'examples';errors=[];cases=0

def audit(observed,reference,tag):
 global cases
 a=mp.mpf(str(observed)); b=mp.mpf(reference);delta=abs(a-b)/(1+abs(b))
 errors.append(float(delta));cases+=1
 if delta > mp.mpf('4e-12'):
  raise AssertionError(f'{tag} mismatch: observed={a} computed={b} error={delta}')
with (E/'real_450_paceval_consistency.csv').open() as f:
 rows=list(csv.DictReader(f))
for r in rows[::5]:
 s=next(x for x in csv.DictReader((E/'real_450_original_fits.csv').open()) if x['source_name']==r['source_name'])
 N,P,g=map(mp.mpf,[s['flux_density_ph_cm2_MeV_s'],s['pivot_MeV'],s['photon_index']])
 I=N*P/(1-g)*((mp.mpf(200)/P)**(1-g)-(mp.mpf(20)/P)**(1-g))
 J=mp.mpf('1.602176634e-6')*N*P*P/(2-g)*((mp.mpf(200)/P)**(2-g)-(mp.mpf(20)/P)**(2-g))
 audit(r['pv_integrated_photon_flux'],I,'integrated photon flux')
 audit(r['pv_integrated_energy_flux_erg'],J,'integrated energy flux')
with (E/'real_60_paceval_spectral_samples.csv').open() as f: rows=list(csv.DictReader(f))
for r in rows[::43]:
 E0,N,P,g,dg=map(mp.mpf,[r['E_MeV'],r['published_normalization'],r['pivot_MeV'],r['published_index'],r['published_index_uncertainty']]);L=mp.log(E0/P)
 F=N*mp.exp(-g*L)
 audit(r['paceval_powerlaw_flux'],F,'powerlaw real fit')
 audit(r['paceval_SED_E2_flux'],E0**2*F,'SED real fit')
 audit(r['paceval_index_dlogflux'],-L,'index sensitivity')
 audit(r['paceval_toy_curvature_q02_flux'],F*mp.exp(-mp.mpf('0.2')*L**2),'hypothetical spectral curve')
with (E/'paceval_curvature_sensitivity_surface_HYPOTHETICAL.csv').open() as f: rows=list(csv.DictReader(f))
for r in rows[::73]:
 E0,q=map(mp.mpf,[r['E_MeV'],r['toy_curvature_q']]);s=next(csv.DictReader((E/'real_60_original_fits.csv').open()))
 P=mp.mpf(s['pivot_MeV']); L=mp.log(E0/P)
 # curvature dependence independent of source normalization or photon index
 audit(r['paceval_log_ratio'],-q*L**2,'toy log ratio')
 audit(r['paceval_curvature_derivative'],-L**2,'toy sensitivity')
out={'status':'PASS','decimal_precision':80,'independent_values_checked':cases,'maximum_scaled_absolute_difference':max(errors),'source_data':'ORIGINAL_2FLE_FITS_PACEVAL_CSV','astrophysical_likelihood_verified':False}
(R/'high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
