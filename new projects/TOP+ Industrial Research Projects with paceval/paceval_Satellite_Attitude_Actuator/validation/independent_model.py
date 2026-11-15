"""Exact disclosed mathematical expressions for the satellite attitude screening study.
This is a build-time formula generator and independent reference, not a substitute for paceval execution.
"""
import math
AXIS_VARS='I Ij Ik w wj wk h hj hk tau ext dt taumax hmax wlimit Jw wF wH wA targetAcc'.split()
Q_VARS='q0 q1 q2 q3 wx wy wz dt'.split()
AGG_VARS='mtx mty mtz mhx mhy mhz mwx1 mwy1 mwz1 mwx2 mwy2 mwz2 sx1 sy1 sz1 sx2 sy2 sz2'.split()

inert='((Ik-Ij)*wj*wk)'
gyro='(wj*hk-wk*hj)'
acc1=f'((tau+ext-{inert})/I)'
acc2=f'((tau+ext-{inert}-{gyro})/I)'
wr1=f'(w+dt*{acc1})'
wr2=f'(w+dt*{acc2})'
hnext='(h-tau*dt)'
mt='(taumax-abs(tau))'
mh=f'(hmax-abs({hnext}))'
mr1=f'(wlimit-abs({wr1}))'
mr2=f'(wlimit-abs({wr2}))'
sc1=f'((({mt}/taumax) min ({mh}/hmax)) min ({mr1}/wlimit))'
sc2=f'((({mt}/taumax) min ({mh}/hmax)) min ({mr2}/wlimit))'
cost1=f'(wF*(tau/taumax)^2+wH*({hnext}/hmax)^2+wA*(({acc1}-targetAcc)*dt/wlimit)^2)'
cost2=f'(wF*(tau/taumax)^2+wH*({hnext}/hmax)^2+wA*(({acc2}-targetAcc)*dt/wlimit)^2)'
guard1=f'((({mt}>=0) AND ({mh}>=0)) AND ({mr1}>=0))'
guard2=f'((({mt}>=0) AND ({mh}>=0)) AND ({mr2}>=0))'
AXIS_FORMULAS=[
 ('wheel_inertial_coupling',inert,'N m'),
 ('wheel_gyro_coupling',gyro,'N m'),
 ('acceleration_v1',acc1,'rad/s^2'),
 ('acceleration_v2',acc2,'rad/s^2'),
 ('rate_next_v1',wr1,'rad/s'),
 ('rate_next_v2',wr2,'rad/s'),
 ('wheel_h_next',hnext,'N m s'),
 ('torque_margin',mt,'N m'),
 ('momentum_margin',mh,'N m s'),
 ('rate_margin_v1',mr1,'rad/s'),
 ('rate_margin_v2',mr2,'rad/s'),
 ('candidate_guard_v1',guard1,'0/1'),
 ('candidate_guard_v2',guard2,'0/1'),
 ('normalized_score_v1',sc1,'dimensionless'),
 ('normalized_score_v2',sc2,'dimensionless'),
 ('cost_v1',cost1,'dimensionless'),
 ('cost_v2',cost2,'dimensionless'),
 ('sensitivity_accel_to_torque','(1/I)','1/(kg m^2)'),
 ('sensitivity_momentum_to_torque','(-dt)','s'),
 ('acceleration_version_delta',f'({acc2}-{acc1})','rad/s^2'),
 ('angular_momentum_balance_residual_v2',f'(I*{acc2}-tau-ext+{inert}+{gyro})','N m'),
 ('wheel_spin_rate','(h/Jw)','rad/s'),
 ('wheel_mechanical_power_proxy','abs(tau*h/Jw)','W'),
 ('body_and_wheel_momentum','(I*w+h)','N m s'),
 ('torque_utilization','(abs(tau)/taumax)','dimensionless'),
 ('momentum_utilization',f'(abs({hnext})/hmax)','dimensionless'),
 ('gyro_to_torque_ratio',f'(abs({gyro})/taumax)','dimensionless'),
 ('sensitivity_acceleration_to_hj','(wk/I)','1/s/(kg m^2)'),
 ('sensitivity_acceleration_to_hk','(-wj/I)','1/s/(kg m^2)'),
 ('score_delta_v2_v1',f'({sc2}-{sc1})','dimensionless'),
]

j1='((sx1 min sy1) min sz1)';j2='((sx2 min sy2) min sz2)'
AGG_FORMULAS=[
 ('joint_guard_v1',f'((sx1>=0) AND ((sy1>=0) AND (sz1>=0)))','0/1'),
 ('joint_guard_v2',f'((sx2>=0) AND ((sy2>=0) AND (sz2>=0)))','0/1'),
 ('joint_score_v1',j1,'dimensionless'),('joint_score_v2',j2,'dimensionless'),
 ('decision_changed',f'(({j1}>=0) <> ({j2}>=0))','0/1'),
 ('joint_score_delta',f'({j2}-{j1})','dimensionless'),
 ('smallest_torque_margin','((mtx min mty) min mtz)','N m'),
 ('smallest_momentum_margin','((mhx min mhy) min mhz)','N m s'),
]
q=['q0','q1','q2','q3'];qdot=[
 '-0.5*(q1*wx+q2*wy+q3*wz)',
 '0.5*(q0*wx+q2*wz-q3*wy)',
 '0.5*(q0*wy+q3*wx-q1*wz)',
 '0.5*(q0*wz+q1*wy-q2*wx)'
]
qu=[f'({q[i]}+dt*({qdot[i]}))' for i in range(4)]
qn='sqrt('+('+'.join(f'({qi})^2' for qi in qu))+')'
QUAT_FORMULAS=[('quaternion_candidate_norm',qn,'dimensionless')]+[(f'quaternion_next_q{i}',f'({qu[i]}/{qn})','dimensionless') for i in range(4)]

INERTIA=(.085,.105,.075)
OMEGA=(.023,-.015,.017)
MOMENTA=(.025,-.018,.026)
TAU_OTHER=(.00022,-.00018)
EXT=(.00009,-.00004,.00002)
TAUMAX=(.0009,.0008,.0008)
HMAX=(.034,.036,.038)
WLIMIT=(.026,.031,.030)
JW=(.00013,.00012,.00011)
DT=1.8


def cases():
    # Fixed-grid 7x7 deliberately spans wheel-momentum and predicted-rate boundaries.
    out=[]
    for h in [.015,.019,.023,.027,.031,.035,.039]:
        for tx in [-.0009,-.0006,-.0003,0,.0003,.0006,.0009]:
            caseid=f'S{len(out)+1:03d}'
            moments=(h,MOMENTA[1],MOMENTA[2]);tau=(tx,*TAU_OTHER)
            vec=[]
            for ax in range(3):
                i,j,k=[(0,1,2),(1,2,0),(2,0,1)][ax]
                vec.append([INERTIA[i],INERTIA[j],INERTIA[k],OMEGA[i],OMEGA[j],OMEGA[k],moments[i],moments[j],moments[k],tau[i],EXT[i],DT,TAUMAX[i],HMAX[i],WLIMIT[i],JW[i],1.0,.25,.5,0.0])
            out.append((caseid,vec))
    return out

def axis_ref(v):
    I,Ij,Ik,w,wj,wk,h,hj,hk,tau,ext,dt,taumax,hmax,wlimit,Jw,wF,wH,wA,targetAcc=v
    c=(Ik-Ij)*wj*wk;g=wj*hk-wk*hj
    a1=(tau+ext-c)/I;a2=(tau+ext-c-g)/I
    nr1=w+dt*a1;nr2=w+dt*a2;hn=h-tau*dt
    mt=taumax-abs(tau);mh=hmax-abs(hn);mr1=wlimit-abs(nr1);mr2=wlimit-abs(nr2)
    sc1=min(mt/taumax,mh/hmax,mr1/wlimit);sc2=min(mt/taumax,mh/hmax,mr2/wlimit)
    res={'wheel_inertial_coupling':c,'wheel_gyro_coupling':g,'acceleration_v1':a1,'acceleration_v2':a2,'rate_next_v1':nr1,'rate_next_v2':nr2,'wheel_h_next':hn,'torque_margin':mt,'momentum_margin':mh,'rate_margin_v1':mr1,'rate_margin_v2':mr2,'candidate_guard_v1':float(mt>=0 and mh>=0 and mr1>=0),'candidate_guard_v2':float(mt>=0 and mh>=0 and mr2>=0),'normalized_score_v1':sc1,'normalized_score_v2':sc2,'cost_v1':wF*(tau/taumax)**2+wH*(hn/hmax)**2+wA*((a1-targetAcc)*dt/wlimit)**2,'cost_v2':wF*(tau/taumax)**2+wH*(hn/hmax)**2+wA*((a2-targetAcc)*dt/wlimit)**2,'sensitivity_accel_to_torque':1/I,'sensitivity_momentum_to_torque':-dt,'acceleration_version_delta':a2-a1,'angular_momentum_balance_residual_v2':I*a2-tau-ext+c+g,'wheel_spin_rate':h/Jw,'wheel_mechanical_power_proxy':abs(tau*h/Jw),'body_and_wheel_momentum':I*w+h,'torque_utilization':abs(tau)/taumax,'momentum_utilization':abs(hn)/hmax,'gyro_to_torque_ratio':abs(g)/taumax,'sensitivity_acceleration_to_hj':wk/I,'sensitivity_acceleration_to_hk':-wj/I,'score_delta_v2_v1':sc2-sc1}
    return res

def agg_inputs(axis):
    return [axis[k]['torque_margin'] for k in range(3)]+[axis[k]['momentum_margin'] for k in range(3)]+[axis[k]['rate_margin_v1'] for k in range(3)]+[axis[k]['rate_margin_v2'] for k in range(3)]+[axis[k]['normalized_score_v1'] for k in range(3)]+[axis[k]['normalized_score_v2'] for k in range(3)]

def agg_ref(v):
    t=v[:3];m=v[3:6];rv1=v[6:9];rv2=v[9:12];sc1=v[12:15];sc2=v[15:18]
    j1=min(sc1);j2=min(sc2)
    return {'joint_guard_v1':float(j1>=0),'joint_guard_v2':float(j2>=0),'joint_score_v1':j1,'joint_score_v2':j2,'decision_changed':float((j1>=0)!=(j2>=0)),'joint_score_delta':j2-j1,'smallest_torque_margin':min(t),'smallest_momentum_margin':min(m)}

if __name__=='__main__':
    a=[]
    for cid,ls in cases():
        x=[axis_ref(row) for row in ls];a.append(agg_ref(agg_inputs(x)))
    print('axis formulas',len(AXIS_FORMULAS),'agg',len(AGG_FORMULAS),'quat',len(QUAT_FORMULAS))
    print('guards v1',sum(x['joint_guard_v1'] for x in a),'v2',sum(x['joint_guard_v2'] for x in a),'changed',sum(x['decision_changed'] for x in a))
    for i in range(7):
        print(i,[int(x['joint_guard_v2']) for x in a[i*7:i*7+7]], [int(x['joint_guard_v1']) for x in a[i*7:i*7+7]])
