#!/usr/bin/env python3
"""Independent 90-decimal optical references from binary-double measurements.
No SDK expressions or C++ code are evaluated as a mathematical reference.
"""
import csv,json,sys,math
from pathlib import Path
from mpmath import mp
mp.dps=90
out=Path(sys.argv[1]); src=Path(sys.argv[2]);checks=0;worst=0.;fails=[]
def read(filename):return list(csv.DictReader(open(filename,newline='')))
def exact(s):return mp.mpf(float(s))
def check(got,expected,context,atol=3e-7,rtol=2e-6):
 global checks,worst
 checks+=1;err=float(abs(exact(got)-expected));worst=max(worst,err)
 if err>atol+rtol*abs(float(expected)) and len(fails)<15:fails.append([context,got,mp.nstr(expected,22),err])
source=read(src);data=read(out/'spectral_samples.csv');sites=read(out/'site_summary.csv')
assert len(source)==len(data)==1296 and len(sites)==144
for a,b in zip(source,data):
 assert a['site_id']==b['site_id'] and a['wavelength_nm']==b['wavelength_nm']
 d=exact(a['true_nm']);alpha=exact(a['alpha_per_nm']);lam=exact(a['wavelength_nm']);offset=exact(a['offset']);nf=exact(a['film_n']);ns=exact(a['substrate_n'])
 yT=exact(b['transmission_observed']);yR=exact(b['reflectance_observed']);ae=alpha*550/lam
 trans=mp.exp(-ae*d)+offset
 tSens=-1/(ae*(yT-offset))
 recovered=-mp.log(yT-offset)/ae
 p=(1-nf)/(1+nf);q=(nf-ns)/(nf+ns)
 phase=4*mp.pi*nf*d/lam;cs=mp.cos(phase)
 numerator=p*p+q*q+2*p*q*cs;denominator=1+(p*q)**2+2*p*q*cs
 reflection=numerator/denominator
 derivative=(4*mp.pi*nf/lam)*(2*p*q)*mp.sin(phase)*(p*p+q*q-1-(p*q)**2)/(denominator*denominator)
 check(b['film_reflectance_at_truth'],reflection,'film reflection '+a['site_id'])
 check(b['film_dR_dd_at_truth'],derivative,'film derivative '+a['site_id'])
 check(b['beer_inverse_nm'],recovered,'Beer inverse '+a['site_id'])
 check(b['beer_sensitivity_nm_per_intensity'],tSens,'Beer sensitivity '+a['site_id'])
 check(b['beer_local_uncertainty_nm'],abs(tSens)*mp.mpf('.001'),'Beer uncertainty '+a['site_id'])
 check(b['film_local_information'],(derivative/mp.mpf('.00035'))**2,'Film information '+a['site_id'],atol=2e-6)
for row in sites:
 ref=[(src0,dat0) for src0,dat0 in zip(source,data) if src0['site_id']==row['site_id']]
 d=exact(row['film_fit_nm']);obj=mp.mpf('0');info=mp.mpf('0')
 for p,y in ref:
  nf=exact(p['film_n']);ns=exact(p['substrate_n']);lam=exact(p['wavelength_nm']);r0=(1-nf)/(1+nf);r1=(nf-ns)/(nf+ns);ph=4*mp.pi*nf*d/lam
  A=r0*r0+r1*r1;B=2*r0*r1;C=1+(r0*r1)**2;den=C+B*mp.cos(ph)
  R=(A+B*mp.cos(ph))/den;dR=4*mp.pi*nf/lam*B*mp.sin(ph)*(A-C)/(den*den)
  obj+=((R-exact(y['reflectance_observed']))/mp.mpf('.00035'))**2
  info+=(dR/mp.mpf('.00035'))**2
 check(row['film_objective'],obj,'composite objective '+row['site_id'],atol=.0002,rtol=.00001)
 check(row['film_local_uncertainty_nm'],1/mp.sqrt(info),'composite local uncertainty '+row['site_id'])
 check(row['true_nm'],exact(ref[0][0]['true_nm']),'site truth '+row['site_id'])
result={'precision_decimal_digits':mp.dps,'checks':checks,'pass':not fails,'internal_max_absolute_reference_discrepancy':worst,'failures':fails,'reference_method':'Independent explicit mpmath Fresnel/Beer optics using exact binary floating-point inputs, direct composite spectral objective'}
(out/'high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('HIGH PRECISION',json.dumps({'pass':not fails,'checks':checks,'failures':len(fails)}))
if fails:raise SystemExit(str(fails[:3]))
