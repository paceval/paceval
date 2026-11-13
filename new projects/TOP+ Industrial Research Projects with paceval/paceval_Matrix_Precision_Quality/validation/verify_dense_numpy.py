"""Independent dense NumPy LAPACK verification of paceval-produced f64 matrices.
Uses no paceval. Reads n*n IEEE754 binary64 row-major little-endian arrays.
"""
import argparse, csv, json, time
from pathlib import Path
import numpy as np

def verify(base, n):
    a_path=base/f'generic_spd_{n}_A.f64'
    inv_path=base/f'generic_spd_{n}_inverse.f64'
    a=np.fromfile(a_path,dtype='<f8').reshape(n,n)
    inv=np.fromfile(inv_path,dtype='<f8').reshape(n,n)
    t=time.perf_counter()
    chol=np.linalg.cholesky(a)
    chol_t=time.perf_counter()-t
    t=time.perf_counter()
    npinv=np.linalg.inv(a)
    inv_t=time.perf_counter()-t
    r=a@inv - np.eye(n)
    symmetry=np.max(np.abs(inv-inv.T))
    eigs=np.linalg.eigvalsh(a)
    cond=float(eigs[-1]/eigs[0])
    result={
        'matrix_size':n,'full_dense_spd':True,
        'smallest_eigenvalue':float(eigs[0]),'largest_eigenvalue':float(eigs[-1]),
        'eigenvalue_condition_2':cond,
        'max_abs_A_minus_AT':float(np.max(np.abs(a-a.T))),
        'max_abs_X_minus_XT':float(symmetry),
        'max_abs_Ainv_minus_numpy_inverse_all_elements':float(np.max(np.abs(inv-npinv))),
        'max_abs_A_times_X_minus_I_all_elements':float(np.max(np.abs(r))),
        'max_abs_numpy_cholesky_reconstruction':float(np.max(np.abs(chol@chol.T-a))),
        'reference_logdet':float(2*np.log(np.diag(chol)).sum()),
        'numpy_cholesky_s':chol_t,'numpy_inverse_s':inv_t,
        'reference_library':np.__version__,'verified_element_count':int(n*n)}
    (base/f'generic_spd_{n}_numpy_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    assert eigs[0]>0
    assert result['max_abs_Ainv_minus_numpy_inverse_all_elements']<3e-9
    assert result['max_abs_A_times_X_minus_I_all_elements']<3e-9
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('results_dir',type=Path);p.add_argument('sizes',nargs='+',type=int)
    args=p.parse_args();
    for n in args.sizes: print(json.dumps(verify(args.results_dir,n),indent=2))
