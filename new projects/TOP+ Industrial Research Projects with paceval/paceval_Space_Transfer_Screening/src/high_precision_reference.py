#!/usr/bin/env python3
"""80-digit independent orbital mechanics verification. No paceval calls here.

Input CSV numbers are parsed from their 17-digit decimal round-trip representation.
This is an independent implementation of the physical equations, not an expression replay.
"""
from pathlib import Path
import csv, json
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parent.parent
KEYS=['departure_kms','arrival_coplanar_kms','arrival_with_plane_kms','total_with_plane_kms','time_days','propellant_kg','propellant_fraction','bielliptic_coplanar_kms','bielliptic_time_days','bielliptic_propellant_kg','bi_departure_kms','bi_apoapsis_kms','bi_arrival_kms','initial_circular_speed_kms','target_circular_speed_kms','policy_v1','policy_v2']
def ref(row):
 c=lambda name:mp.mpf(row[name])
 mu,r1,r2,rb,theta,isp,mass=(c(k) for k in ['mu_km3_s2','r1_km','r2_km','rb_km','plane_rad','isp_s','mass_kg'])
 v1=mp.sqrt(mu/r1);v2=mp.sqrt(mu/r2)
 vt1=mp.sqrt(mu*(mp.mpf(2)/r1-2/(r1+r2)))
 vt2=mp.sqrt(mu*(mp.mpf(2)/r2-2/(r1+r2)))
 d1=abs(vt1-v1);d2=abs(vt2-v2)
 # Alternative independent geometric velocity-vector form to cross-check the stable C++ formula.
 da=mp.sqrt(v2*v2+vt2*vt2-2*v2*vt2*mp.cos(theta))
 total=d1+da;time=mp.pi*mp.sqrt(((r1+r2)/2)**3/mu)/86400
 ff=1-mp.exp(-total*1000/(isp*mp.mpf('9.80665')))
 b1=mp.sqrt(mu*(mp.mpf(2)/r1-2/(r1+rb)))
 bh1=mp.sqrt(mu*(mp.mpf(2)/rb-2/(r1+rb)))
 bh2=mp.sqrt(mu*(mp.mpf(2)/rb-2/(r2+rb)))
 b3=mp.sqrt(mu*(mp.mpf(2)/r2-2/(r2+rb)))
 db1=abs(b1-v1);db2=abs(bh2-bh1);db3=abs(b3-v2)
 btot=db1+db2+db3
 bt=mp.pi*(mp.sqrt(((r1+rb)/2)**3/mu)+mp.sqrt(((r2+rb)/2)**3/mu))/86400
 bf=1-mp.exp(-btot*1000/(isp*mp.mpf('9.80665')))
 policy1=total/4+mp.mpf('0.10')*time/mp.mpf('0.5')+mp.mpf('0.35')*ff
 policy2=total/4+mp.mpf('0.35')*time/mp.mpf('0.5')+mp.mpf('0.12')*ff
 return [d1,d2,da,total,time,mass*ff,ff,btot,bt,mass*bf,db1,db2,db3,v1,v2,policy1,policy2]

def main():
 rows=list(csv.DictReader((ROOT/'examples'/'transfer_candidates.csv').open()))
 assert len(rows)>=100
 ids=sorted(set([0,1,17,21,39,50,len(rows)//2,len(rows)-1]+list(range(20,len(rows),47))))
 cases=0;worst=0;validated=0
 for i in ids:
  r=rows[i];v=ref(r)
  for key,expected in zip(KEYS,v):
   actual=mp.mpf(r[key]);delta=abs(actual-expected);worst=max(worst,float(delta))
   if delta > mp.mpf('2e-9')*(1+abs(expected)):
    raise AssertionError((i,key,mp.nstr(delta,20),mp.nstr(expected,20)))
   validated+=1
  cases+=1
 # Analytical invariants holding for the defined domain. No mission feasibility implied.
 for i in [0,25,60,100,300]:
  r=rows[i];assert float(r['total_with_plane_kms'])+1e-10 >=float(r['departure_kms'])+float(r['arrival_coplanar_kms'])
  assert float(r['propellant_fraction'])>0 and float(r['propellant_fraction'])<1
 audit={'project':'WP_037','precision_digits':80,'independent_cases':cases,'independent_values':validated,'max_absolute_difference_for_technical_audit_only':worst,'pass':True,'notes':'80-digit independent formula translation and physical model invariants; not a mission optimizer or formal interval certificate.'}
 (ROOT/'results'/'high_precision_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(f'PASS high precision: {cases} candidates, {validated} mathematical quantities')
if __name__=='__main__':main()
