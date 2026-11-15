#!/usr/bin/env python3
"""Independent proof-obligation tests for the stated sufficient Lyapunov inequality.
A certificate applies to the explicitly defined class and ellipsoid only.
"""
import csv,json,sys,math
from pathlib import Path
from mpmath import mp
mp.dps=90
out=Path(sys.argv[1]);data=Path(sys.argv[2]);src={r['candidate_id']:r for r in csv.DictReader(data.open())}
screen=list(csv.DictReader((out/'screening.csv').open()));checks=0;fails=[];counts={'V1':0,'V2':0};counter={'V1':0,'V2':0};sample_pass={'V1':0,'V2':0};false_cert=0
for row in screen:
 p=src[row['candidate_id']];v=row['model'];k1,k2,k3,a,b,c,d,p1,p2,R,eps,umax=[mp.mpf(p[k]) for k in ['k1','k2','k3','a','b','c','d','p1','p2','R','eps','umax']];z=k3 if v=='V2' else mp.mpf(0)
 assert 0<R<=1 and p1>0 and p2>0 and k3>=0 and c>=0 and d>=0
 B=max(mp.mpf(0),p1*c+p2*d);mx=2*p1*(a+k1)+2*p1*z*(1-R*R/3)-p1*abs(k2)-B*R*R/2-eps
 my=2*p2*b-p1*abs(k2)-B*R*R/2-eps
 act=umax-R*(abs(k1)+abs(k2)+z)
 positive=mx>=0 and my>=0 and act>=0
 actual=int(row['analytic_certificate'])==1
 checks+=4
 if actual!=positive:fails.append((row['candidate_id'],v,'certificate_flag'))
 if actual: counts[v]+=1
 if int(row['sampled_pass']):sample_pass[v]+=1
 if int(row['sampled_violations'])>0: counter[v]+=1
 if actual and int(row['sampled_violations'])>0:false_cert+=1;fails.append((row['candidate_id'],v,'certified_but_sample_violation'))
 for k,expected in [('analytic_cert_margin',min(mx,my)),('global_actuator_margin',act)]:
  if abs(mp.mpf(float(row[k]))-expected)>mp.mpf('1e-8'):fails.append((row['candidate_id'],v,k))
# A representative entire ellipsoid claim is algebraic: Vdot <= -eps*r^2,
# from |xy| <= (x^2+y^2)/2; x^2 y^2 <= R^2(x^2+y^2)/4;
# x tanh(x) >= (1-R^2/3)*x^2 for 0<R<=1 and k3>=0.
# Test positivity of the last elementary inequality at high precision across the domain.
for j in range(-1000,1001):
 x=mp.mpf(j)/1000
 if x*mp.tanh(x)+(mp.mpf('1e-70'))<(1-mp.mpf(1)/3)*x*x:fails.append(('tanh_bound',j));break
 checks+=1
result={'valid_region':'V <= min(p1,p2)*R^2; implies x^2+y^2<=R^2','model':'2-state autonomous continuous-time controlled nonlinear plant; u not clipped','analytic_method':'elementary Young/Cauchy plus tanh(x)/x >= 1-R^2/3 on |x|<=R<=1','checks':checks,'certified_sufficient':counts,'sampled_pass':sample_pass,'sampled_counterexamples':counter,'false_certificates':false_cert,'failures':fails[:10],'pass':not fails,'not_claimed':'Global stability, actuator saturation dynamics, disturbances, complete original robot system, industrial safety certification'}
(out/'certificate_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('CERTIFICATE',json.dumps({'pass':not fails,'certified':counts,'counterexamples':counter,'checks':checks}))
if fails:raise SystemExit('Certificate verification failed: '+str(fails[:2]))
