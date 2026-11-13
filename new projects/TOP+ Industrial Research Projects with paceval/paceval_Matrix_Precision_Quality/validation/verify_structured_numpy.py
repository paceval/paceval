#!/usr/bin/env python3
"""Independent validation only; not used by C++ paceval program.
Rebuilds full dense SPD matrices and computes Cholesky, inverse, log-determinant
with NumPy / BLAS. This is a separate verification, not a paceval benchmark.
"""
import argparse,csv,json,time
from pathlib import Path
import numpy as np

def read_arrays(directory,n):
    rows=list(csv.DictReader(open(directory/f'structured_spd_input_{n}.csv')))
    assert len(rows)==n
    d=np.array([float(r['D']) for r in rows],dtype=np.float64)
    u=np.array([[float(r[f'U{k}']) for k in range(3)] for r in rows],dtype=np.float64)
    a=u@u.T; a[np.diag_indices(n)]+=d
    return a,d,u

def check(directory,n):
    A,d,U=read_arrays(directory,n)
    t=time.perf_counter();L=np.linalg.cholesky(A);choltime=time.perf_counter()-t
    t=time.perf_counter();inv=np.linalg.inv(A);invtime=time.perf_counter()-t
    logdet=2*np.log(np.diag(L)).sum()
    meta={}
    for line in (directory/f'structured_spd_diagnostics_{n}.txt').read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1);meta[k]=v
    rows=list(csv.DictReader(open(directory/f'inverse_{n}_samples.csv')))
    err=max(abs(inv[int(r['i']),int(r['j'])]-float(r['paceval'])) for r in rows)
    # Independently form the complete rotated covariance via BLAS, compare exported samples.
    angles=0.02+0.5*np.sin((np.arange(n//2)+1)*0.013)
    R=np.zeros((n,n),dtype=np.float64)
    for block,(c,s) in enumerate(zip(np.cos(angles),np.sin(angles))):
        i=block*2
        R[i,i]=c;R[i,i+1]=-s;R[i+1,i]=s;R[i+1,i+1]=c
    cov=R@A@R.T
    cov_rows=list(csv.DictReader(open(directory/f'covariance_{n}_samples.csv')))
    cov_error=max(abs(cov[int(r['i']),int(r['j'])]-float(r['paceval'])) for r in cov_rows)
    sym_error=float(np.max(np.abs(cov-cov.T)))
    trace_diff=float(abs(np.trace(cov)-np.trace(A)))
    true_resid=np.max(np.abs(A@inv-np.eye(n)))
    logerr=abs(logdet-float(meta['logdet_paceval']))
    assert err<2e-12 and logerr<1e-10 and true_resid<2e-12 and cov_error<2e-12 and sym_error<2e-12 and trace_diff<2e-9,(n,err,logerr,true_resid,cov_error)
    res={'n':n,'status':'PASS','numpy_cholesky_s':choltime,'numpy_inverse_s':invtime,
         'numpy_inverse_residual_max':float(true_resid),'max_abs_inverse_error_on_exported_samples':float(err),
         'numpy_logdet':float(logdet),'paceval_logdet':float(meta['logdet_paceval']),
         'logdet_abs_error':float(logerr),'max_abs_covariance_error_on_exported_samples':float(cov_error), 'covariance_symmetry_residual':float(sym_error),'covariance_trace_difference':float(trace_diff),'min_cholesky_diag':float(np.diag(L).min()),
         'max_cholesky_diag':float(np.diag(L).max())}
    print(json.dumps(res,indent=2));return res
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('results',type=Path);args=parser.parse_args()
    results=[check(args.results,n) for n in (512,1024)]
    (args.results/'external_numpy_verification.json').write_text(json.dumps(results,indent=2)+'\n')
