#!/usr/bin/env python3
"""Independent high-precision audit of TRUE paceval-exported bulk-wave values.

No call to the paceval runtime is made in this file; mathematical expressions
are independently reconstructed with mpmath at 80 decimal places.  The script
also verifies convergence and model provenance without claiming gravitational
wave propagation or nonlinear Einstein equation verification.
"""
import csv, json, math
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
R=Path(__file__).resolve().parents[1]
def D(x):return mp.mpf(str(x))
def near(got,want):
    got=mp.mpf(got)
    return float(abs(got-want)/(1+abs(want)))
values=list(csv.DictReader((R/'examples'/'parameterized_kernel_surface.csv').open()))
checks=0;worst=0.;worst_key=''
stride=max(1,len(values)//220)
for r in values[::stride]:
    z,k,q=D(r['z']),D(r['k']),D(r['q'])
    dx=D('.015');t=D('.23');omega=D('2.05');m=D('1.8');amp=D('.25');delta=D('.4')
    f=lambda x:amp*x*x*mp.sin(m*x)*mp.cos(omega*t)
    h=f(z);hl=f(z-dx);hr=f(z+dx);v=-omega*amp*z*z*mp.sin(m*z)*mp.sin(omega*t)
    grad=(hr-hl)/(2*dx);lap=(hr-2*h+hl)/(dx*dx)
    op=lap-3*grad/z
    source=mp.mpf('0')  # Parametric surface intentionally fixes forcing OFF to isolate q and k.
    rhs=op-(k*k+q)*h+source
    en=mp.mpf('.5')*(v*v+grad*grad+(k*k+q)*h*h)/z**3
    flux=-v*grad/z**3
    zero=amp*(1+mp.mpf('.08')*z**4)*mp.cos(omega*t)
    ref={
      'rhs_v1':rhs,'rhs_v2':rhs-delta*h,'spatial_operator':op,'source':source,
      'energy_density':en,'flux':flux,
      'drhs_dk':-2*k*h,
      'drhs_dq':-h,
      'version_delta':-delta*h,'exact_zero':zero,'exact_mms':h
    }
    for col,want in ref.items():
        err=near(r[col],want);checks+=1
        if err>worst:worst=err;worst_key=col
        if err>2e-10:raise AssertionError(f'{col} {err:.3e} at z={z}, k={k}, q={q}')
mode=dict(zero_radial=(0,1.4,0,0,1.4,.38),bessel_J2=(1,1.1,.30,2.,math.sqrt(1.21+.3+4),.80),manufactured_forced=(2,1.3,.25,1.8,2.05,.25),zero_radial_revision=(3,1.4,0,0,math.sqrt(1.96+.55),.38))
wave=list(csv.DictReader((R/'examples'/'field_time_series.csv').open()))
for r in wave[::max(1,len(wave)//150)]:
    kind,k,q,m,omega,amp=mode[r['mode']]
    z=D(r['z']);t=D(r['t']);m=D(m);amp=D(amp);omega=D(omega)
    if kind in (0,3):sp=amp*(1+D('.08')*z**4)
    elif kind==1:sp=amp*z*z*mp.besselj(2,m*z)
    else:sp=amp*z*z*mp.sin(m*z)
    a=sp*mp.cos(omega*t)
    e=near(r['exact_h'],a);checks+=1
    if e>worst:worst=e;worst_key='exact_bessel_or_mms'
    if e>2e-10:raise AssertionError(f'Exact mode incorrect: {r["mode"]} {e:.3e}')
    e2=abs(float(r['h'])-float(r['exact_h'])-float(r['error']));checks+=1
    if e2>2e-11:raise AssertionError('Wave CSV error reconciliation failed')
con=list(csv.DictReader((R/'examples'/'grid_convergence.csv').open()))
assert len(con)==12
for r in con:
    if int(r['n'])>25:
        p=float(r['observed_order']);assert 1.90<p<2.10,(r['mode'],p)
run=json.loads((R/'results'/'execution_summary.json').read_text())
assert run['paceval_persistent_graphs']==28 and run['parameter_surface_points']==len(values)
assert run['multi_graph_batch_calls']>0 and run['paceval_batch_outputs']>0
out={'status':'passed','precision_decimal_digits':80,'independently_checked_values':checks,'max_scaled_error':worst,'max_scaled_error_column':worst_key,'tested_modes':list(mode),'grid_sizes':run['grid_sizes'],'source_is_synthetic':True,'physical_detection_claim':False}
(R/'results'/'high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
