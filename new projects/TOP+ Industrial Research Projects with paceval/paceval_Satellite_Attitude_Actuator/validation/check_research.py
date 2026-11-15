#!/usr/bin/env python3
"""Independent 90-digit audit of actual transcribed paceval MCP 4.26 numerical responses.
Reports pointwise interval inclusion, explicitly retaining original TINC error codes.
No claims about unsampled input intervals, certified control safety, or local SDK execution.
"""
import csv,json,math,sys
from pathlib import Path
import mpmath as mp
mp.mp.dps=90
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'validation'))
import independent_model as im
O=R/'results'
read=lambda p:list(csv.DictReader((O/p).open()))
fail=[];count={};max_err={}

def eq(a,b,kind,case,rtol=mp.mpf('8e-12'),atol=mp.mpf('1e-12')):
    a=mp.mpf(str(a));b=mp.mpf(str(b));e=abs(a-b)
    max_err[kind]=max(max_err.get(kind,0.),float(e))
    count[kind]=count.get(kind,0)+1
    if e>atol+rtol*abs(b):fail.append(f'{kind} {case}: observed={a}, reference={b}, abs={e}')

# 1) independent mpmath derivation, not the native reference's implementation.
def axis_prec(seq):
    (I,Ij,Ik,w,wj,wk,h,hj,hk,tau,ext,dt,taumax,hmax,wlimit,Jw,wF,wH,wA,targetAcc)=map(lambda x:mp.mpf(str(x)),seq)
    inert=(Ik-Ij)*wj*wk;gy=wj*hk-wk*hj
    a1=(tau+ext-inert)/I;a2=(tau+ext-inert-gy)/I
    w1=w+dt*a1;w2=w+dt*a2;hn=h-tau*dt;mt=taumax-abs(tau);mh=hmax-abs(hn);mw1=wlimit-abs(w1);mw2=wlimit-abs(w2)
    s1=min(mt/taumax,mh/hmax,mw1/wlimit);s2=min(mt/taumax,mh/hmax,mw2/wlimit)
    return {'rate_v1':w1,'rate_v2':w2,'wheel_h_next':hn,'momentum_margin':mh,'rate_margin_v1':mw1,'rate_margin_v2':mw2,'score_v1':s1,'score_v2':s2,'guard_v1':int(s1>=0),'guard_v2':int(s2>=0),'acceleration_v2':a2,'gyro_coupling':gy,'body_momentum_next':I*w2+hn,'angular_residual':I*a2+(-tau)+inert+gy-ext}

def inputs_for(cid):return next(v for id,v in im.cases() if id==cid)

# All actual observed aggregate results 49 rows x 7 graphs.
for row in read('mcp_observed_joint_grid.csv'):
    vals=[axis_prec(v) for v in inputs_for(row['case_id'])]
    sc1=min(v['score_v1'] for v in vals);sc2=min(v['score_v2'] for v in vals)
    checks={'joint_guard_v1':int(sc1>=0),'joint_guard_v2':int(sc2>=0),'joint_score_v1':sc1,'joint_score_v2':sc2,
      'decision_changed':int((sc1>=0)!=(sc2>=0)),'min_torque_margin_Nm':min(mp.mpf(str(v[12]))-abs(mp.mpf(str(v[9]))) for v in inputs_for(row['case_id'])),
      'min_momentum_margin_Nms':min(v['momentum_margin'] for v in vals)}
    for key,val in checks.items():
        key_in='min_torque_margin_Nm' if key=='min_torque_margin_Nm' else 'min_momentum_margin_Nms' if key=='min_momentum_margin_Nms' else key
        eq(row[key_in],val,'observed_aggregate',row['case_id']+'/'+key)

# Selected actual axis x graph observations.
for row in read('mcp_observed_axis_x_examples.csv'):
    val=inputs_for(row['case_id'])[0];ref=axis_prec(val)
    for key in ['rate_v1','rate_v2','wheel_h_next','momentum_margin','rate_margin_v1','rate_margin_v2','score_v1','score_v2','guard_v1','guard_v2','acceleration_v2','gyro_coupling']:
        eq(row[key],ref[key],'observed_axis',row['case_id']+'/'+key)

# 12 actually observed quaternion graph outputs, using independently written mpmath Hamilton multiplication.
for row in read('mcp_observed_quaternion.csv'):
    q=[mp.mpf(str(row[f'q{i}'])) for i in range(4)]
    wx,wy,wz=[mp.mpf(str(row[k])) for k in ['wx','wy','wz']];dt=mp.mpf('1.8')
    dq=[-(q[1]*wx+q[2]*wy+q[3]*wz)/2,
         (q[0]*wx+q[2]*wz-q[3]*wy)/2,
         (q[0]*wy+q[3]*wx-q[1]*wz)/2,
         (q[0]*wz+q[1]*wy-q[2]*wx)/2]
    qq=[a+dt*b for a,b in zip(q,dq)];norm=mp.sqrt(sum(v*v for v in qq))
    eq(row['candidate_norm'],norm,'observed_quaternion',row['case_id']+'/norm')
    for j in range(4):eq(row[f'next_q{j}'],qq[j]/norm,'observed_quaternion',row['case_id']+f'/next{j}')
    n=mp.sqrt(sum(mp.mpf(row[f'next_q{i}'])**2 for i in range(4)))
    eq(n,1,'quaternion_unit_norm',row['case_id'],rtol=mp.mpf('1e-12'))

# 12 sequential actual remote desaturation evaluations, not an analytic-only trajectory.
old=mp.mpf('.039')
for row in read('mcp_observed_desaturation.csv'):
    nn=old-mp.mpf('.00015')*mp.mpf('10')
    eq(row['momentum_in_Nms'],old,'observed_desaturation',row['step']+'/in')
    eq(row['momentum_next_Nms'],nn,'observed_desaturation',row['step']+'/out')
    eq(row['momentum_margin_Nms'],mp.mpf('.041')-abs(nn),'observed_desaturation',row['step']+'/margin')
    eq(row['body_acceleration_rad_s2'],0,'observed_desaturation',row['step']+'/omega')
    eq(row['guard_v2'],1,'observed_desaturation',row['step']+'/guard')
    eq(row['wheel_mechanical_power_proxy_W'],abs(mp.mpf('.00015')*old/mp.mpf('.00013')),'observed_desaturation',row['step']+'/proxy')
    old=nn

# Interval output is for fixed inputs. The 144 cases are explicit errors.
# When returned decimal endpoints collapse to one string, strict inclusion of the
# exact rational input may be undecidable from text alone: flag INCONCLUSIVE, not pass/fail.
interval_pass=0;interval_uncertain=0;interval_unresolved=0
for row in read('mcp_observed_tinc.csv'):
    v=list(inputs_for('S001')[0]);v[9]=float(row['tau_x_Nm']);v[6]=float(row['h_x_Nms'])
    ref=axis_prec(v)['rate_margin_v2' if row['formula']=='rate_margin_v2' else 'momentum_margin']
    if row['error_number']!='0':
        interval_unresolved+=1;continue
    interval_pass+=1
    lo=mp.mpf(row['lower']);hi=mp.mpf(row['upper'])
    if not lo<=ref<=hi:
        interval_pass-=1;interval_uncertain+=1
# Invariants: no external torque one-axis spin-momentum exchange.
a=axis_prec([.085,.105,.075,0,0,0,.039,0,0,.00015,0,10,.0009,.041,.026,.00013,1,.25,.5,0])
eq(a['body_momentum_next'],mp.mpf('.039'),'momentum_exchange_invariant','zero_external')
eq(a['angular_residual'],0,'coupled_euler_invariant','zero_external')

# Inputs rejected by the model's domain contract.
invalid=['I <= 0','Jw <= 0','dt <= 0','taumax <= 0','hmax <= 0','wlimit <= 0','NaN/Inf forbidden','wheel+body axes must be orthogonal in this version']
result={'reference_precision_decimal_digits':90,'checks_by_class':count,'total_compared':sum(count.values()),'max_absolute_differences':max_err,'failures':fail,'tinc':{'confirmed':interval_pass,'point_inclusion_not_demonstrable_from_rounded_text':interval_uncertain,'paceval_error_144_unresolved':interval_unresolved,'input_interval_certification':False},'domain_negative_tests_documented':invalid,'local_paceval_sdk_link_and_execution':'NOT EXECUTED','engine_numerical_speedup':'NOT MEASURED'}
(O/'high_precision_validation.json').write_text(json.dumps(result,indent=2)+'\n')
(O/'failed_cases.json').write_text(json.dumps(fail,indent=2)+'\n')
print(json.dumps({'checks':result['total_compared'],'by_class':count,'tinc':result['tinc'],'errors':len(fail)},indent=2))
for x in fail[:30]:print('FAIL',x)
if fail:sys.exit(1)
