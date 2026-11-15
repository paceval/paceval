#!/usr/bin/env python3
"""Independent exact-binary-input mpmath verification; never evaluates graph text."""
import csv,json,sys,math
from pathlib import Path
from mpmath import mp
mp.dps=90
result=Path(sys.argv[1]); src=Path(sys.argv[2]);cases={r['candidate_id']:r for r in csv.DictReader(src.open())}
check=0;worst=0.;failed=[]
def val(s):return mp.mpf(float(s))
def num(x):return mp.mpf(float(x))
def confirm(actual,reference,tag):
 global check,worst
 check+=1
 z=float(abs((num(actual)-reference)))
 worst=max(worst,z)
 if z>3e-8+2e-8*abs(float(reference)):
  if len(failed)<10:failed.append((tag,float(reference),actual,z))
for row in csv.DictReader((result/'state_samples.csv').open()):
 c=cases[row['candidate_id']];x,y=val(row['x']),val(row['y']);v=row['model'];p={k:val(c[k]) for k in ['k1','k2','k3','a','b','c','d','p1','p2','R','eps','umax']}; k3=p['k3'] if v=='V2' else mp.mpf(0)
 u=-p['k1']*x-p['k2']*y-k3*mp.tanh(x)
 f1=-p['a']*x+u+p['c']*x*y*y;f2=-p['b']*y+p['d']*x*x*y
 V=p['p1']*x*x+p['p2']*y*y
 dot=2*p['p1']*x*f1+2*p['p2']*y*f2
 residual=-p['eps']*(x*x+y*y)-dot
 B=max(mp.mpf(0),p['p1']*p['c']+p['p2']*p['d']);mix=p['p1']*abs(p['k2'])+B*p['R']**2/2
 mx=2*p['p1']*(p['a']+p['k1'])+2*p['p1']*k3*(1-p['R']**2/3)-mix-p['eps']
 my=2*p['p2']*p['b']-mix-p['eps'];cm=min(mx,my)
 for k,ref in [('control',u),('V',V),('Vdot',dot),('lyapunov_margin',residual),('actuator_margin',p['umax']-abs(u)),('certificate_margin',cm)]:confirm(row[k],ref,row['candidate_id']+'_'+v+'_'+k)
 if check and check%10000==0: pass
for row in csv.DictReader((result/'model_comparison.csv').open()):
 p=cases[row['candidate_id']];x,y=mp.mpf('.3'),mp.mpf('.4');k3=val(p['k3']);p1=val(p['p1']);c1=val(p['c']);c2=val(p['d']);R=val(p['R']);eps=val(p['eps'])
 confirm(row['delta_u_x03_y04'],-k3*mp.tanh(x),'delta_control')
 confirm(row['delta_Vdot_x03_y04'],-2*p1*k3*x*mp.tanh(x),'delta_vdot')
for row in csv.DictReader((result/'closed_loop_traces.csv').open()):
 if row['time'] not in ('0','0.0','0.000000','0.025') and len(row['time'])>0:continue
 p=cases[row['candidate_id']];x,y=val(row['x']),val(row['y']);v=row['model'];k3=val(p['k3']) if v=='V2' else mp.mpf(0)
 u=-val(p['k1'])*x-val(p['k2'])*y-k3*mp.tanh(x)
 f1=-val(p['a'])*x+u+val(p['c'])*x*y*y;f2=-val(p['b'])*y+val(p['d'])*x*x*y
 V=val(p['p1'])*x*x+val(p['p2'])*y*y;vd=2*val(p['p1'])*x*f1+2*val(p['p2'])*y*f2
 confirm(row['V'],V,'traceV');confirm(row['Vdot'],vd,'traceVdot')
output={'precision_decimal_digits':mp.dps,'independent_checks':check,'max_absolute_comparison_difference_internal_only':worst,'failures':failed,'pass':not failed,'reference_origin':'separately written mpmath formulas with source numeric values converted to exact binary float first'}
(result/'high_precision_audit.json').write_text(json.dumps(output,indent=2)+'\n')
print('HIGH_PRECISION',json.dumps({'pass':not failed,'checks':check,'failure_count':len(failed)}))
if failed:raise SystemExit('High precision verification failure: '+str(failed[:2]))
