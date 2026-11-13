#!/usr/bin/env python3
"""Independent source-level and recorded-result audits.

The published numeric data are original paceval outputs from two provenance categories:
A. Full 512/1024 dense inverse matrices were produced by a previously recorded local paceval SDK run.
B. New quality scores/sensitivities/TINC bounds came from real paceval MCP 4.26 bulk calls.
This audit independently computes decimal high-precision mathematical references. It does NOT
reexecute the unavailable original local SDK or certify an industrial measurement system.
"""
import csv, json, math, sys, pathlib, hashlib
from decimal import Decimal, localcontext
import numpy as np
from mpmath import mp

def run(root):
    root=pathlib.Path(root)
    param=json.loads((root/'examples/model_parameters.json').read_text())
    arr=np.fromfile(root/'results/recorded_baseline/generic_spd_512_inverse.f64',dtype='<f8').reshape(512,512)
    coef=[float(arr[0,0]),float(arr[0,1]),float(arr[0,2]),float(arr[1,1]),float(arr[1,2]),float(arr[2,2])]
    recorded=list(param['precision_upper_triangle'].values())
    assert coef==recorded,'Source matrix precision coefficients mismatch'
    mp.dps=85
    a,b,c,d,e,f=[mp.mpf(x) for x in coef]
    t,h=mp.mpf(float(param['threshold'])),mp.mpf(float(param['penalty_h']))
    def calc(x,y,z):
        X,Y,Z=[mp.mpf(float(v)) for v in (x,y,z)]
        q=a*X*X+2*b*X*Y+2*c*X*Z+d*Y*Y+2*e*Y*Z+f*Z*Z
        q2=q+h*(X*X+Y*Y+Z*Z)
        return [q,q2,t-q,t-q2,2*a*X+2*b*Y+2*c*Z,2*a*X+2*b*Y+2*c*Z+2*h*X,2*c*X+2*e*Y+2*f*Z+2*h*Z,mp.sqrt(q)]
    cases=list(csv.DictReader((root/'results/remote_paceval_scenarios.csv').open()))
    worst=mp.mpf(0)
    tinc_all=True
    bad=[]
    columns=['q_v1','q_v2','margin_v1','margin_v2','dx_v1','dx_v2','dz_v2','radius']
    for row in cases:
        actual=calc(row['x'],row['y'],row['z'])
        for i,name in enumerate(columns):
            # Parse the full decimal output string, not a rounded Python float.
            observed=mp.mpf(row[name]);err=abs(actual[i]-observed)
            worst=max(worst,err)
            if err>mp.mpf('0.000000000005'):
                bad.append((row['scenario_id'],name,mp.nstr(err,8)))
        for name,v in [('q',actual[0]),('margin',actual[2])]:
            low=mp.mpf(float(row[f'{name}_tinc_lo']));high=mp.mpf(float(row[f'{name}_tinc_hi']))
            # The MCP formats endpoints with short decimal strings. Reconstruct the binary64 value.
            # Actual internal interval endpoints may contain more bits than exported digits.
            if not (low<=v<=high):
                bad.append((row['scenario_id'],name+'_TINC','exclusion'));tinc_all=False
    grid=list(csv.DictReader((root/'results/remote_paceval_grid.csv').open()))
    grid_worst=mp.mpf(0)
    for row in grid:
        values=calc(row['x'],row['y'],row['z'])
        for name,i in [('score_v1',0),('score_v2',1),('version_delta',None)]:
            actual=(values[1]-values[0]) if i is None else values[i]
            err=abs(actual-mp.mpf(row[name]));grid_worst=max(err,grid_worst)
            # Grid values were intentionally printed to ten decimal places.
            if err>mp.mpf('0.00000000006'):
                bad.append((row['x']+','+row['y'],name,mp.nstr(err,10)))
    # Independent complete-matrix algebraic validation (not a new paceval execution).
    fullchecks={}
    for n in (512,1024):
        A=np.fromfile(root/f'results/recorded_baseline/generic_spd_{n}_A.f64',dtype='<f8').reshape(n,n)
        inv=np.fromfile(root/f'results/recorded_baseline/generic_spd_{n}_inverse.f64',dtype='<f8').reshape(n,n)
        assert A.shape==(n,n) and np.isfinite(inv).all() and np.isfinite(A).all()
        residual=A@inv-np.eye(n)
        max_res=float(np.max(np.abs(residual)))
        assert max_res<2e-12, ('matrix residual too large',n,max_res)
        fullchecks[str(n)]={'full_matrix_max_residual_internal_only':max_res,'all_entries_finite':True,'full_matrix_checked':True}
    audit={'reference':'mpmath independent 85 decimal arithmetic using exact IEEE754 binary64 input values','new_mcp_cases':len(cases),'new_mcp_grid':len(grid),'TINC_q_and_margin_inclusions_successful':tinc_all,'max_mcp_vs_high_precision_error_internal_only':str(worst),'max_mcp_grid_vs_high_precision_error_internal_only':str(grid_worst),'recorded_original_matrix_checks':fullchecks,'problems':bad,'status':'PASS' if not bad else 'FAIL','local_cpp_executable_tested':False}
    (root/'results/high_precision_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('Reference audit:',audit['status'],'sample cases',len(cases),'grid cases',len(grid),'matrix dimensions',list(fullchecks))
    if bad: raise SystemExit('Failed reference audit: '+repr(bad[:10]))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1])
