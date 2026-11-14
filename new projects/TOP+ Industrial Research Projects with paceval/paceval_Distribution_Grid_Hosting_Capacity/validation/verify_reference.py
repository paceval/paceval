#!/usr/bin/env python3
"""Independent complex-nodal AC verification of original paceval-generated WP11 outputs.
Unlike the productive C++ graph path, this script uses NumPy complex arithmetic;
selected points are also checked by nonlinear SciPy nodal equations and mpmath.
"""
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import root
import mpmath as mp
P=argparse.ArgumentParser();P.add_argument('results',nargs='?',default=str(Path(__file__).resolve().parents[1]/'results'));P.add_argument('--small',action='store_true');args=P.parse_args()
base=Path(args.results)
def read(name):
 with (base/name).open(newline='') as f:return list(csv.DictReader(f))
lines=read('network_branches.csv');scenario=read('scenario_results.csv');raw=read('input_scenarios.csv');hc=read('hosting_capacity.csv');sample=read('branch_samples.csv');trace=read('end_to_end_trace.csv')
assert len(lines)==11 and len(raw)==len(scenario)
N=12;parent=np.zeros(N,dtype=int);rr=np.zeros(N);xx=np.zeros(N);ratings=np.zeros(N);Pload=np.zeros(N);Qload=np.zeros(N)
for r in lines:
 i=int(r['bus']);parent[i]=int(r['parent']);rr[i]=float(r['r_pu']);xx[i]=float(r['x_pu']);ratings[i]=float(r['imax_pu']);Pload[i]=float(r['pload_pu']);Qload[i]=float(r['qload_pu'])
z=rr+1j*xx
for i in range(1,N):assert parent[i]<i
# Distinct reference formulation: complex-number nodal currents and a separate loop.
def solve_complex(row):
 bus=int(row['candidate_bus']);mode=int(row['control_mode']);p=float(row['der_pu']);
 pvec=Pload.copy();qvec=Qload.copy();pvec[bus]-=p;qvec[bus]+=0.25*p if mode else 0
 S=pvec+1j*qvec;V=np.ones(N,complex)
 for iteridx in range(100):
  cur=np.conj(S/V)
  for i in reversed(range(1,N)):
   if parent[i]>0:cur[parent[i]]+=cur[i]
  updated=np.ones(N,dtype=complex)
  for i in range(1,N):updated[i]=updated[parent[i]]-z[i]*cur[i]
  if np.max(np.abs(updated-V))<4.e-14:
   V=updated;break
  V=updated
 else:raise AssertionError('independent complex radial solver did not converge')
 cur=np.conj(S/V)
 for i in reversed(range(1,N)):
  if parent[i]>0:cur[parent[i]]+=cur[i]
 vm=np.abs(V[1:]);cm=np.abs(cur[1:]);m_v=np.minimum(vm-.95,1.05-vm);m_i=ratings[1:]-cm
 penalty1=np.maximum(0,.95-vm)**2+np.maximum(0,vm-1.05)**2+.4*np.maximum(0,cm-ratings[1:])**2
 penalty2=1.4*np.maximum(0,.95-vm)**2+1.8*np.maximum(0,vm-1.05)**2+.7*np.maximum(0,cm-ratings[1:])**2
 score=.38*(cm/ratings[1:])**2+.3*((vm-1)/.05)**2
 return {'V':V,'I':cur,'feasible':int(np.all((m_v>=0)&(m_i>=0))), 'violated_branches':int(np.sum((m_v<0)|(m_i<0))),
 'min_voltage_pu':min(vm),'max_voltage_pu':max(vm),'min_voltage_margin_pu':min(m_v),'min_current_margin_pu':min(m_i),
 'total_line_loss_pu':float(np.sum(rr[1:]*cm**2)),'scenario_score':float(np.sum(score)),
 'penalty_v1':float(np.sum(penalty1)),'penalty_v2':float(np.sum(penalty2)),
 'der_bus_voltage_pu':abs(V[bus]),'slack_real_power_pu':cur[1].real,'slack_reactive_power_pu':-cur[1].imag,
 'vm':vm,'cm':cm,'margin':m_v,'pvec':pvec,'qvec':qvec}
checks=0;maxdiff=0;max_slack=0
source={ (int(r['candidate_bus']),int(r['control_mode']),int(r['penetration_step'])):r for r in raw}
samples_by_key={}
for s in sample:samples_by_key.setdefault((int(s['candidate_bus']),int(s['control_mode']),int(s['penetration_step'])),[]).append(s)
for row in scenario:
 k=(int(row['candidate_bus']),int(row['control_mode']),int(row['penetration_step']))
 assert k in source and abs(float(source[k]['der_active_power_pu'])-float(row['der_pu']))<1e-12
 got=solve_complex(row)
 assert got['feasible']==int(row['feasible']),('classification',k)
 assert got['violated_branches']==int(row['violated_branches']),('violations',k)
 checks+=2
 for col in ['min_voltage_pu','max_voltage_pu','min_voltage_margin_pu','min_current_margin_pu','total_line_loss_pu','scenario_score','penalty_v1','penalty_v2','der_bus_voltage_pu','slack_real_power_pu','slack_reactive_power_pu']:
  a=got[col];b=float(row[col]);d=abs(a-b);maxdiff=max(maxdiff,d);assert d<3e-9*(1+abs(a)),(k,col,a,b,d)
  checks+=1
 for s in samples_by_key.get(k,[]):
  i=int(s['bus'])-1
  for key,v in [('voltage_pu',got['vm'][i]),('current_pu',got['cm'][i]),('voltage_margin_pu',got['margin'][i])]:
   d=abs(float(s[key])-v);maxdiff=max(maxdiff,d);assert d<2e-9,(k,key,d)
   checks+=1
# Reference hosting-capacity definition is largest FEASIBLE DISCRETE sampled active export.
for h in hc:
 bus=int(h['candidate_bus']);mode=int(h['control_mode'])
 entries=[r for r in scenario if int(r['candidate_bus'])==bus and int(r['control_mode'])==mode]
 passed=[r for r in entries if int(r['feasible'])==1]
 expected=max([float(r['der_pu']) for r in passed],default=-1)
 assert abs(float(h['highest_feasible_der_pu'])-expected)<1e-10
 assert int(h['tested_levels'])==len(entries) and int(h['feasible_levels'])==len(passed)
 checks+=3
# A genuinely different nonlinear power-flow test using nodal YV + conj(S/V) = 0.
Y=np.zeros((N,N),dtype=complex)
for i in range(1,N):
 p=parent[i];y=1/z[i];Y[i,i]+=y;Y[p,p]+=y;Y[i,p]-=y;Y[p,i]-=y
root_cases=[]
by_key={(int(r['candidate_bus']),int(r['control_mode']),int(r['penetration_step'])):r for r in scenario}
levels=sorted(set(int(r['penetration_step']) for r in scenario));use_levels=sorted(set([0,levels[len(levels)//4],levels[len(levels)//2],levels[-1]]))
for bus in [4,6,9,11]:
 for mode in [0,1]:
  for level in use_levels:
   k=(bus,mode,level)
   if k not in by_key:continue
   row=by_key[k];ref=solve_complex(row);S=ref['pvec']+1j*ref['qvec']
   def F(a):
    V=np.r_[1+0j,a[:N-1]+1j*a[N-1:]]
    currents=Y[1:,:]@V+np.conj(S[1:]/V[1:])
    return np.r_[currents.real,currents.imag]
   initial=np.r_[np.ones(N-1),np.zeros(N-1)]
   sol=root(F,initial,method='hybr',tol=1e-11)
   assert np.linalg.norm(F(sol.x),ord=np.inf)<3e-10,(k,sol.message)
   V=np.r_[1+0j,sol.x[:N-1]+1j*sol.x[N-1:]]
   assert np.max(abs(V-ref['V']))<3e-9,k
   root_cases.append({'candidate_bus':bus,'control_mode':mode,'penetration_step':level,'max_kcl_nodal_residual':float(np.max(abs(F(sol.x))))})
   checks+=2*(N-1)
# 80-digit checks of full graph-derived voltages and squared current magnitudes in archived rows.
mp.mp.dps=80;hi=0
for s in sample[::max(1,len(sample)//256)]:
 k=(int(s['candidate_bus']),int(s['control_mode']),int(s['penetration_step']))
 r=by_key[k];ref=solve_complex(r);i=int(s['bus'])
 V=ref['V'][i];I=ref['I'][i]
 vv=mp.sqrt(mp.mpf(float(V.real))**2+mp.mpf(float(V.imag))**2)
 cc=mp.sqrt(mp.mpf(float(I.real))**2+mp.mpf(float(I.imag))**2)
 assert abs(vv-mp.mpf(s['voltage_pu']))<mp.mpf('3e-9')
 assert abs(cc-mp.mpf(s['current_pu']))<mp.mpf('3e-9')
 hi+=2
with (base/'independent_validation_audit.json').open('w') as f:json.dump({'scenario_rows_checked':len(scenario),'independent_python_reference_assertions':checks,'selected_scipy_nonlinear_nodal_solutions':len(root_cases),'high_precision_decimal80_checks':hi,'max_absolute_validation_difference':maxdiff,'all_passed':True,'scipy_nodal_cases':root_cases},f,indent=2)
print('INDEPENDENT VALIDATION PASS:',len(scenario),'scenarios,',checks,'assertions,',len(root_cases),'SciPy nonlinear roots,',hi,'high-precision checks')
