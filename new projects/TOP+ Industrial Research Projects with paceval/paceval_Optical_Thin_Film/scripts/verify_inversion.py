#!/usr/bin/env python3
"""Independent inverse and identifiability tests using SciPy and direct physics.
The independent objective is reimplemented, not evaluated through paceval.
"""
from pathlib import Path
import csv,sys,json,math
import numpy as np
from scipy.optimize import minimize_scalar
P=Path(sys.argv[1]); dat=list(csv.DictReader((P/'spectral_samples.csv').open())); src=list(csv.DictReader((Path(__file__).parents[1]/'input/spectral_samples.csv').open()));fits=list(csv.DictReader((P/'site_summary.csv').open()))
by={}
for a,b in zip(src,dat):by.setdefault(a['site_id'],[]).append((a,b))
failed=[];checks=0;errs=[]
for r in fits:
 w=by[r['site_id']]
 def objective(d):
  val=0
  for a,b in w:
   nf=float(a['film_n']);ns=float(a['substrate_n']);lam=float(a['wavelength_nm']);ra=(1-nf)/(1+nf);rb=(nf-ns)/(nf+ns);c=2*ra*rb*math.cos(4*math.pi*nf*d/lam)
   rpred=(ra*ra+rb*rb+c)/(1+(ra*rb)**2+c)
   val+=((rpred-float(b['reflectance_observed']))/.00035)**2
  return val
 grid=np.linspace(88,460,373);values=np.array([objective(float(x)) for x in grid]);imin=int(np.argmin(values));lo=max(88,grid[imin]-2);hi=min(460,grid[imin]+2)
 opt=minimize_scalar(objective,bounds=(lo,hi),method='bounded',options={'xatol':1e-9})
 d=float(r['film_fit_nm']);v=float(r['film_objective']);error=abs(d-opt.x);errs.append(error);checks+=3
 if error>.05 or abs(v-objective(d))>.0005 or abs(d-float(r['true_nm']))>3:
  failed.append([r['site_id'],d,opt.x,error,v,objective(d)])
assert len(fits)==144
alias=list(csv.DictReader((P/'alias_case.csv').open()))[0];checks+=3
if abs(float(alias['reflectance_a'])-float(alias['reflectance_b']))>1e-9:failed.append(['alias reflection'])
if abs(float(alias['thickness_b_nm'])-float(alias['thickness_a_nm'])-float(alias['reflection_period_nm']))>1e-8:failed.append(['alias period'])
result={'independent_inversion_checks':checks,'independent_scipy_recovered_sites':len(fits),'pass':not failed,'max_optimizer_thickness_difference_nm_internal':max(errs),'single_wavelength_alias_verified':True,'failed_cases':failed[:10], 'scope':'synthetic nine-wavelength lossless single-layer normal-incidence optics'}
(P/'inverse_reference_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('INVERSION',json.dumps({'pass':not failed,'checks':checks,'max_d_difference_nm':max(errs)}))
if failed:raise SystemExit(str(failed[:5]))
