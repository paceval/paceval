"""External QA using pandas (not used by C++ programs)."""
import json
from pathlib import Path
import pandas as pd
root=Path(__file__).resolve().parent.parent
prec=json.loads((root/'validation/v15_highprecision.json').read_text())
precision={float(x['ell_Mpc']):float(x['seconds']) for x in prec}
summary={'v15':{},'v14':{}}
for n in [100,250,500,1000,2000]:
 d=pd.read_csv(root/f'results/cosmo_n{n}.csv')
 summary['v15'][str(n)]={str(ell):{'paceval_seconds':float(d.loc[(d['ell_Mpc']-ell).abs().idxmin(),'geometric_advance_seconds']),
     'absolute_error_seconds':abs(float(d.loc[(d['ell_Mpc']-ell).abs().idxmin(),'geometric_advance_seconds'])-ref)}
     for ell,ref in precision.items()}
for dt in [.006,.003,.0015]:
 p=root/f'results/wave_static_dt{dt}.csv';d=pd.read_csv(p)
 summary['v14'][f'static_dt_{dt}']={'max_error':float(d.error.max()),'end_error':float(d.error.iloc[-1])}
for ny in [81,161,321]:
 d=pd.read_csv(root/f'results/wave_pulse_ny{ny}.csv')
 summary['v14'][f'pulse_ny_{ny}']={'brane_final':float(d.h_brane.iloc[-1]),'quarter_final':float(d.h_yquart.iloc[-1]),'energy_final':float(d.energy.iloc[-1])}
 e=pd.read_csv(root/f'results/wave_constant_ny{ny}.csv')
 summary['v14'][f'moving_constant_ny_{ny}']={'max_error':float(e.error.max())}
for ny in [81,161]:
 summary['v14'][f'independent_scipy_ny_{ny}']=json.loads((root/f'validation/v14_scipy{ny}.json').read_text())['max_abs_difference']
print(json.dumps(summary,indent=2))
