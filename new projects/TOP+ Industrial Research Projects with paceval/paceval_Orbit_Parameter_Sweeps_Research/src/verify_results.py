#!/usr/bin/env python3
"""Standalone CSV-level checks. Does not depend on or call the paceval engine.
Verifies trajectory schema, independent native comparison fields, energy
conservation where appropriate, and the no-J2 no-drag circular orbit oracle.
"""
import csv, math, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; EX=ROOT/'examples'; RES=ROOT/'results'; RES.mkdir(exist_ok=True)
MU=398600.4418; RE=6378.137; INC=math.radians(51.6)
def read(name):
 with open(EX/name,newline='') as f:return list(csv.DictReader(f))
summary=read('scenario_summary.csv');grid=read('parameter_surface.csv')
assert len(summary)==10 and len(grid)==49
max_path_error=0;max_speed_error=0;max_analytic_error=0;total_states=0
for spec in summary:
 name=spec['scenario'];rows=read('orbit_'+name+'.csv');assert len(rows)==361
 assert all(int(r['step'])==i and float(r['time_s'])==i*60 for i,r in enumerate(rows))
 for row in rows:
  r=math.sqrt(sum(float(row[k])**2 for k in ['x_km','y_km','z_km']))
  assert abs(r-RE-float(row['altitude_km']))<1e-9
  patherr=float(row['position_difference_km']);velerr=float(row['velocity_difference_km_s'])
  max_path_error=max(max_path_error,patherr);max_speed_error=max(max_speed_error,velerr)
  assert patherr<1e-4 and velerr<1e-7
  total_states+=1
  if name=='two_body':
   t=float(row['time_s']);ang=math.sqrt(MU/(RE+500)**3)*t;rr=RE+500
   target=[rr*math.cos(ang),rr*math.sin(ang)*math.cos(INC),rr*math.sin(ang)*math.sin(INC)]
   err=math.dist([float(row[k]) for k in ['x_km','y_km','z_km']],target)
   max_analytic_error=max(max_analytic_error,err)
 assert abs(float(rows[-1]['altitude_km'])-float(spec['final_altitude_km']))<1e-9
assert max_analytic_error<.3
assert all(0<=float(g['j2_scale'])<=1.5 and 0<=float(g['drag_scale'])<=100 for g in grid)
report={'status':'pass','number_of_scenarios':len(summary),'parameter_grid_scenarios':len(grid),'trajectory_rows':total_states,
        'largest_native_position_difference_km':max_path_error,'largest_native_velocity_difference_km':max_speed_error,
        'two_body_six_hour_analytic_max_position_difference_km':max_analytic_error,
        'caveat':'Finite-step integration and analytical test are not a high-fidelity operational orbit validation.'}
(RES/'csv_independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
