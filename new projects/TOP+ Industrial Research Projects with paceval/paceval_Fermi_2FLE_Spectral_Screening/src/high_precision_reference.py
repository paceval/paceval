#!/usr/bin/env python3
"""Independent high-precision testing of real paceval-generated synthetic surfaces.
No Fermi photon data or measured 2FLE spectral points are used in this program.
"""
from pathlib import Path
import csv, json
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'examples/synthetic_spectral_surface.csv').open()))
assert len(rows)==65*65
fields=['flux_powerlaw','flux_lp_v1','flux_lp_v2','expected_counts_lp','log_likelihood_lp','deviance_lp','log_flux_ratio','sensitivity_logflux_dq']
checked=0;worst=0
for row in rows[::31]:
 E=mp.mpf(row['energy_MeV']);q=mp.mpf(row['curvature_q']);x=mp.log(E/100)
 p=mp.mpf(9)*mp.exp(-mp.mpf('1.8')*x)
 lp=mp.mpf(9)*mp.exp(-mp.mpf('1.8')*x-q*x*x)
 lp2=mp.mpf(9)*mp.exp(-mp.mpf('1.8')*x-q*x*x-mp.mpf('0.08')*x*x*x)
 mu=mp.mpf(4)+mp.mpf(30)*mp.mpf('0.12')*lp
 n=mp.mpf(20)
 wanted=[p,lp,lp2,mu,n*mp.log(mu)-mu,2*(mu-n+n*mp.log((n+mp.mpf('1e-16'))/mu)),-q*x*x,-x*x]
 for key,expected in zip(fields,wanted):
  got=mp.mpf(row[key]);err=float(abs(got-expected));worst=max(worst,err)
  assert abs(got-expected)<=mp.mpf('2e-10')*(1+abs(expected)),(key,row['energy_MeV'],row['curvature_q'],str(err))
  checked+=1
report={'status':'PASS','independent_decimal_digits':80,'checked_values':checked,'checked_surface_rows':len(rows[::31]),'maximum_absolute_difference_internal':worst,'source':'synthetic_spectral_surface.csv','scope':'synthetic paceval spectra only; no astronomy class inference'}
(ROOT/'results/high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS independent mpmath checked',checked,'values')
