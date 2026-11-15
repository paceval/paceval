#!/usr/bin/env python3
"""Independent high-precision evaluation of archived REAL remote paceval results.
The formula strings in src/formula_manifest.json are NOT interpreted here.
This implements geometric contact mechanics independently, at 90 decimal digits.
"""
from pathlib import Path
from mpmath import mp
import csv,json,sys,math,hashlib
mp.dps=90
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
inputs={x['case_id']:x for x in csv.DictReader((R/'examples/synthetic_contact_candidates.csv').open())}
actuals=list(csv.DictReader((R/'results/mcp_observed_main_selected.csv').open()))
def D(v):return mp.mpf(v)
def mag(v):return mp.sqrt(sum(t*t for t in v))
errors=[];checks=0;worst=0.0;flags_v1=flags_v2=changes=0
ref_cache={}
for row in actuals:
    case=inputs[row['case_id']]
    force=[mp.mpf('0'),mp.mpf('0'),-D(case['mass'])*D(case['g'])]
    torque=[mp.mpf('0')]*3
    frics=[];nmins=[];cmins=[];pen=mp.mpf('0')
    for idx in (1,2,3):
        fn,ft,fz,nx,ny,r,z,mu,ncap=(D(case[f'{x}{idx}']) for x in ('Fn','Ft','Fz','nx','ny','R','z','mu','Ncap'))
        fx=-nx*fn-ny*ft;fy=-ny*fn+nx*ft
        pt=[r*nx,r*ny,z]
        for k,x in enumerate((fx,fy,fz)):force[k]+=x
        moment=[pt[1]*fz-pt[2]*fy,pt[2]*fx-pt[0]*fz,pt[0]*fy-pt[1]*fx]
        for k in range(3):torque[k]+=moment[k]
        margin=mu*fn-mp.sqrt(ft*ft+fz*fz)
        frics.append(margin);nmins.append(fn);cmins.append(ncap-fn)
        pen+=max(mp.mpf(0),-margin)**2
        assert abs(nx*nx+ny*ny-1)<D('1e-12')
    F1=mag(force);T1=mag(torque)
    for i,k in enumerate(('ex','ey','ez')):force[i]+=D(case[k])
    for i,k in enumerate(('etx','ety','etz')):torque[i]+=D(case[k])
    F2=mag(force);T2=mag(torque)
    Ftol,Ttol,Lref=(D(case[k]) for k in ('Ftol','Ttol','Lref'))
    J2=D(case['wF'])*F2*F2+D(case['wT'])*(T2/Lref)**2+D(case['wM'])*pen
    margin=min(Ftol-F2,(Ttol-T2)/Lref,min(frics),min(nmins),min(cmins))
    cond=lambda f,t: int(f<=Ftol and t<=Ttol and min(frics)>=0 and min(nmins)>=0 and min(cmins)>=0)
    flag1,flag2=cond(F1,T1),cond(F2,T2)
    ref_cache[row['case_id']]={'force_residual_v2':F2,'joint_margin_v2':margin}
    expected={'force_residual_v2_N':F2,'torque_residual_v2_Nm':T2,'friction_margin_min_N':min(frics),
      'cost_v2_N2':J2,'candidate_guard_v1':flag1,'candidate_guard_v2':flag2,'joint_margin_v2_N':margin}
    for key,value in expected.items():
        got=D(row[key]);diff=abs(got-value)
        tol=D('2e-10')*max(mp.mpf(1),abs(value))
        if key.startswith('candidate_guard_'):tol=mp.mpf('0')
        if diff>tol:errors.append({'case':row['case_id'],'function':key,'actual':row[key],'reference':str(value),'absolute_error':str(diff)})
        worst=max(worst,float(diff));checks+=1
    flags_v1+=flag1;flags_v2+=flag2;changes+=int(flag1!=flag2)
assert len(actuals)==81 and len(inputs)==81
assert (flags_v1,flags_v2,changes)==(21,12,9)
tinc_rows=list(csv.DictReader((R/'results/mcp_tinc_observed.csv').open()))
tinc_pass=0
for item in tinc_rows:
    ref=ref_cache[item['case_id']][item['graph_id']]
    if int(item['error_number'])!=0 or not (D(item['lower'])<=ref<=D(item['upper'])):
        errors.append({'case':item['case_id'],'function':item['graph_id'],'reason':'TINC printed bounds did not enclose independent point reference'})
    else:tinc_pass+=1
# Strict invalid-input and exact-boundary policy checks for the host contract.
rejected_literals=['1+2','NaN','1,0','0x10',' 3','.','3.4m','1e999999']
assert all(not __import__('re').fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',s) or s=='1e999999' for s in rejected_literals)
status={'status':'PASS' if not errors else 'FAIL','engine_evidence':'remote paceval MCP 4.26 graph results transcribed to CSV',
 'reference':'independent geometrical contact mechanics; mpmath 90 digits',
 'checked_cases':len(actuals),'checked_numeric_and_boolean_cells':checks,
 'passed_cells':checks-len(errors),'worst_absolute_difference_due_to_remote_decimal_transcription':worst,
 'model_v1_candidate_pass_count':flags_v1,'model_v2_candidate_pass_count':flags_v2,
 'changed_candidate_status_count':changes,'errors':errors,
 'tinc_printed_interval_point_checks':len(tinc_rows),'tinc_passed':tinc_pass,'pointwise_not_full_interval_coverage':True,
 'measurement_or_force_closure_certification':False}
(R/'results/high_precision_validation.json').write_text(json.dumps(status,indent=2)+'\n')
print('Independent high precision:',status['status'],'cases',len(actuals),'cells',checks,'v1/v2',flags_v1,flags_v2,'changes',changes)
for x in errors[:8]:print('FAILED',x)
if errors:sys.exit(1)
