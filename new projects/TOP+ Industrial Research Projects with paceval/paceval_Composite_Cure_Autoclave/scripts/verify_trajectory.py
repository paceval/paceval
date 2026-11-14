#!/usr/bin/env python3
"""Independent full 10-node time integration for one selected synthetic recipe.
NumPy's dense linear solver is used, not C++'s tridiagonal Thomas solver. This
verifies the actual coupled state progression, not just algebraic subexpressions.
"""
from pathlib import Path
import csv, json, sys, math
import numpy as np

def main(root):
 p=Path(root);target='R032';dt=15.;steps=840;n=10
 recipes=list(csv.DictReader((Path(__file__).resolve().parents[1]/'input/recipes.csv').open(newline='')))
 recipe=next(x for x in recipes if x['recipe_id']==target)
 thickness=float(recipe['thickness_m']);dz=thickness/n;ramp=float(recipe['ramp_C_min']);holdC=float(recipe['hold_C']);holdMin=float(recipe['hold_min']);h=float(recipe['convection_W_m2K'])
 output=list(csv.DictReader((p/'cure_profiles.csv').open(newline='')))
 selected=[r for r in output if r['recipe_id']==target]
 lookup={(r['model'],int(float(r['time_min'])*60/dt),int(r['node'])):r for r in selected}
 def air(t):
  minute=t/60;rise=(holdC-25)/ramp
  if minute<rise:return 273.15+25+ramp*minute
  if minute<=rise+holdMin:return 273.15+holdC
  return 273.15+max(25,holdC-2.3*(minute-rise-holdMin))
 report={};maxT=0.;maxA=0.;checks=0
 for version in ['V1','V2']:
  T=np.full(n,298.15);a=np.full(n,.015)
  for step in range(steps+1):
   if step%40==0 or step==steps:
    for j in range(n):
     r=lookup[(version,step,j)]
     qT=float(r['part_C'])+273.15;qa=float(r['alpha'])
     dt_err=abs(qT-T[j]);da_err=abs(qa-a[j]);maxT=max(maxT,dt_err);maxA=max(maxA,da_err)
     assert dt_err<2e-6, f'Independent thermal solver mismatch: {target} {version} {step} {j} {dt_err}'
     assert da_err<2e-7, f'Independent cure integration mismatch: {target} {version} {step} {j} {da_err}'
     checks+=2
   if step==steps:break
   k1=1e4*np.exp(-65000/(8.314462618*T));k2=45000*np.exp(-63500/(8.314462618*T))
   rate=(k1+k2*a)*(1-a)**1.35
   if version=='V2':
    tg=260.15+(455.15-260.15)*.68*a/(1-.32*a)
    rate=rate/(1+np.exp((tg-T)/9.5))
   releaseTemp=610.*250000.*rate/1.64e6
   newA=np.minimum(1.,a+dt*rate)
   coef=.48/(1.64e6*dz*dz);edge=h/(1.64e6*dz)
   M=np.zeros((n,n));B=T+dt*releaseTemp
   for j in range(n):
    neighbors=(j>0)+(j<n-1)
    boundary=j in (0,n-1)
    M[j,j]=1+dt*(neighbors*coef+(edge if boundary else 0))
    if j>0:M[j,j-1]=-dt*coef
    if j<n-1:M[j,j+1]=-dt*coef
    if boundary:B[j]+=dt*edge*air((step+1)*dt)
   T=np.linalg.solve(M,B)
   a=newA
  report[version]={'end_centre_T_K':float(T[5]),'end_centre_alpha':float(a[5])}
 audit={'tested_recipe':target,'versions':report,'comparison_points':checks,'max_abs_temperature_residual_K':maxT,'max_abs_conversion_residual':maxA,'method':'independent native NumPy full 10-node trajectory with dense linear solve (not paceval expression strings)','status':'PASS','scope_limit':'One representative recipe and two versions; not an industrial material calibration or a time/space convergence study'}
 (p/'trajectory_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print('INDEPENDENT FULL TRAJECTORY PASS',checks,'temperature/conversion comparisons')
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('Usage: verify_trajectory.py results_dir')
 main(sys.argv[1])
