#!/usr/bin/env python3
"""External Monte Carlo check of Gaussian propagation with nonlinear quadratic calibration.
Generated measurements are hypothetical. This is a distribution model check, not traceability.
"""
import csv, math, json,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
audit=Path(sys.argv[1]) if len(sys.argv)>1 else root/'results'/'audit_samples.csv'
with audit.open() as f:rows=list(csv.DictReader(f))
# Select representative records for both signs and large correlations; use only v2.
selected=[];seen=set()
for row in rows:
 if int(row['model_version'])!=2:continue
 case=int(row['covariance_case']);revision=int(row['revision']);
 if case not in [0,2,4,7,8,9] or revision not in [0,5,9]:continue
 key=(case,revision)
 if key in seen:continue
 seen.add(key);selected.append(row)
 if len(selected)>=14:break
assert len(selected)>=6
records=[];N=60000
for index,row in enumerate(selected):
 val=lambda key:float(row[key]);x,temp,ux,ut,rho=[val(k) for k in ['x','temp_C','ux','ut_C','rho']]
 a0,a1,a2,b=[val(k) for k in ['a0','a1','a2','b']]; ucal,ures=val('ucal'),val('ures')
 rg=np.random.default_rng(20261114+index*17)
 z1=rg.standard_normal(N);z2=rg.standard_normal(N)
 xs=x+ux*z1;temps=temp+ut*(rho*z1+np.sqrt(1-rho*rho)*z2)
 yy=(a0+a1*xs+a2*xs*xs+b*(temps-20)+ucal*rg.standard_normal(N)+ures*rg.standard_normal(N))
 mu=float(yy.mean());var=float(yy.var(ddof=1));theory_y=val('y_mm');theory_var=val('variance_mm2')
 # Conservative 7-sigma sample-mean and sample-variance acceptance for reproducible finite MC.
 se_mean=np.sqrt(theory_var/N)
 se_var=theory_var*np.sqrt(2.0/(N-1))
 zmean=abs(mu-theory_y)/se_mean
 zvar=abs(var-theory_var)/se_var
 assert zmean<7 and zvar<7,(index,zmean,zvar)
 records.append({'revision':int(row['revision']),'case':int(row['covariance_case']),
                 'rho':rho,'mc_samples':N,'reference_y_mm':theory_y,'mc_mean_mm':mu,
                 'reference_variance_mm2':theory_var,'mc_variance_mm2':var,
                 'mean_standard_error_units':zmean,'variance_standard_error_units':zvar,
                 'status':'PASS'})
out=audit.parent/'monte_carlo_audit.csv'
with out.open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=records[0]);writer.writeheader();writer.writerows(records)
print('INDEPENDENT_MONTE_CARLO_CHECK_PASS',len(records),'cases',N,'draws each')
