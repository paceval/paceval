#!/usr/bin/env python3
"""An independently written Python high-resolution RK4 path checks full closed-loop states."""
import csv,sys,json,math
from pathlib import Path
p=Path(sys.argv[1]);source=Path(sys.argv[2]);cases={r['candidate_id']:r for r in csv.DictReader(source.open())};lines=list(csv.DictReader((p/'closed_loop_traces.csv').open()));final={}
for r in lines:
 if abs(float(r['time'])-3)<1e-10 and int(r['initial_case'])==0 and int(r['candidate_id'][1:])<8:final[(r['candidate_id'],r['model'])]=r
check=0;maxdiff=0;bad=[]
def rhs(x,y,ref,v):
 get=lambda z:float(ref[z]); k3=get('k3') if v=='V2' else 0
 u=-get('k1')*x-get('k2')*y-k3*math.tanh(x)
 return (-get('a')*x+u+get('c')*x*y*y,-get('b')*y+get('d')*x*x*y)
for (id,ver),target in final.items():
 x,y=.65,.2;h=3/960
 for _ in range(960):
  a=rhs(x,y,cases[id],ver);b=rhs(x+h*a[0]/2,y+h*a[1]/2,cases[id],ver);c=rhs(x+h*b[0]/2,y+h*b[1]/2,cases[id],ver);d=rhs(x+h*c[0],y+h*c[1],cases[id],ver)
  x+=h*(a[0]+2*b[0]+2*c[0]+d[0])/6;y+=h*(a[1]+2*b[1]+2*c[1]+d[1])/6
 for z,expected in [('x',x),('y',y)]:
  check+=1;diff=abs(float(target[z])-expected);maxdiff=max(maxdiff,diff)
  if diff>1e-6:bad.append((id,ver,z,diff))
result={'independent_integration':'Python RK4 four times smaller step than C++ host','checks':check,'max_abs_difference_internal_only':maxdiff,'failures':bad,'pass':not bad}
(p/'trajectory_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('INDEPENDENT TRAJECTORY',{'pass':not bad,'checks':check});assert not bad,str(bad[:3])
