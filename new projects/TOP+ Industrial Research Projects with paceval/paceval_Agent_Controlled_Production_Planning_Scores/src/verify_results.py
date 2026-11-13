#!/usr/bin/env python3
"""Independent structural/exhaustive job-shop and whole-schedule objective reference.
Does not call paceval or reuse its formula registry for numerical calculations.
"""
import argparse,csv,itertools,json,math
from pathlib import Path

NJ=4; NM=3
TASKS=((0,0,0,3),(0,1,1,2),(0,2,2,2),(1,0,0,2),(1,1,2,1),(1,2,1,4),(2,0,1,4),(2,1,2,3),(2,2,0,1),(3,0,2,2),(3,1,0,4),(3,2,1,3))
FAMILIES=(0,0,1,1);PRIORITY=(2,1.6,1.2,1.9);MACHINE_OPS=tuple(tuple(i for i,t in enumerate(TASKS) if t[2]==m) for m in range(3))
ENERGY=sum(t[3]*(1.5,1.1,1.8)[t[2]] for t in TASKS)

def readcsv(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def enumerate_schedules(scale):
 schedules=[];counter=0
 for orders in itertools.product(*(itertools.permutations(m) for m in MACHINE_OPS)):
  counter+=1;edges=[[] for _ in TASKS];ind=[0]*len(TASKS)
  for j in range(4):
   for k in range(2):u=j*3+k;v=u+1;edges[u].append((v,0.));ind[v]+=1
  sw=0;setup=0
  for m in range(3):
   for a,b in zip(orders[m],orders[m][1:]):
    delta=scale*(FAMILIES[TASKS[a][0]]-FAMILIES[TASKS[b][0]])**2
    sw+=(delta!=0) if scale else (FAMILIES[TASKS[a][0]]!=FAMILIES[TASKS[b][0]])
    setup+=delta;edges[a].append((b,delta));ind[b]+=1
  earlier=[0.]*len(TASKS);start=[0.]*len(TASKS);end=[0.]*len(TASKS);visited=set()
  for _ in TASKS:
   u=next((i for i in range(len(TASKS)) if i not in visited and ind[i]==0),None)
   if u is None:break
   visited.add(u);start[u]=earlier[u];end[u]=start[u]+TASKS[u][3]
   for v,d in edges[u]:earlier[v]=max(earlier[v],end[u]+d);ind[v]-=1
  if len(visited)<len(TASKS):continue
  comp=tuple(end[3*j+2] for j in range(4));mk=max(comp);idle=3*mk-sum(t[3] for t in TASKS)-setup
  assert idle>=-1e-10
  schedules.append(dict(index=counter,orders=orders,start=start,end=end,c=comp,mk=mk,idle=idle,setup=setup,sw=sw))
 return schedules

def calc(candidate,policy,urgent,version):
 due=(10,11,12,14) if urgent else (12,14,18,17)
 late=[max(0.,c-d) for c,d in zip(candidate['c'],due)]
 t=sum(p*x for p,x in zip(PRIORITY,late));q=sum(p*x*x for p,x in zip(PRIORITY,late))
 w=[float(policy[x]) for x in ('makespan_weight','tardiness_weight','changeover_weight','energy_weight')]
 result=w[0]*candidate['mk']/30+w[1]*(t/25+(0.15*q/250 if version==2 else 0))+w[2]*(candidate['setup']+.5*candidate['sw'])/20+w[3]*(ENERGY+.25*candidate['setup'])/60
 if version==2:result+=.06*candidate['idle']/60+.04*(max(late)/15)**2
 return result,t

def check(root):
 summary=readcsv(root/'results/scenario_summary.csv')
 assert len(summary)==32,('expected 32 scenario results',len(summary))
 ops=readcsv(root/'examples/best_schedules.csv');assert len(ops)==32*12
 requests={x['policy']:x for x in readcsv(root/'examples/agent_requests.csv')}
 assert set(requests)=={'throughput','delivery','changeover','energy'}
 schedules={x:enumerate_schedules(x) for x in (0.,2.)};assert all(schedules.values())
 winner_checks=0;structure_checks=0;objective_checks=0
 opmap={}
 for o in ops:opmap.setdefault(o['scenario'],[]).append(o)
 for row in summary:
  key=row['scenario']; assert len(opmap[key])==12
  scale=float(row['setup_scale_h']);urgent=row['urgent_due']=='1';version=int(row['model_version'][-1]);p=requests[row['policy']]
  winner=min(schedules[scale],key=lambda s:(round(calc(s,p,urgent,version)[0],11),s['index']))
  score,tardy=calc(winner,p,urgent,version)
  assert winner['index']==int(row['winning_candidate']),(key,'wrong globally optimal candidate')
  for col,expected in [('objective_score',score),('makespan_h',winner['mk']),('weighted_tardiness_h',tardy),('setup_h',winner['setup']),('idle_h',winner['idle']),('energy_kwh',ENERGY+.25*winner['setup'])]:
   got=float(row[col]);assert math.isclose(got,expected,rel_tol=1e-10,abs_tol=1e-10),(key,col,got,expected)
   objective_checks+=1
  assert int(row['feasible_schedules'])==len(schedules[scale]);assert int(row['switches'])==winner['sw']
  for op in opmap[key]:
   i=int(op['operation']);assert int(op['job'])==TASKS[i][0] and int(op['machine'])==TASKS[i][2]
   assert math.isclose(float(op['start_h']),winner['start'][i],abs_tol=1e-10)
   assert math.isclose(float(op['end_h']),winner['end'][i],abs_tol=1e-10)
   structure_checks+=2
  winner_checks+=1
 # Key properties: no overlap, precedence, no fake policy solver.
 execution=dict(x.strip().split('=',1) for x in (root/'results/sdk_execution.txt').read_text().splitlines() if '=' in x)
 assert execution['status']=='PASS' and execution['policy_source'].startswith('scripted')
 out=dict(status='PASS',independent_method='fresh_Python_exhaustive_machine_order_enumeration',assignment_count_per_setup=13824,
    feasible_assignment_counts={str(k):len(v) for k,v in schedules.items()},scenario_winners_verified=winner_checks,
    complete_objective_and_metric_checks=objective_checks,operation_interval_checks=structure_checks,
    note='No LLM inference, CP-SAT execution, or external production data were used')
 (root/'results/independent_schedule_audit.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS independent schedule audit:',out)
 return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);v=a.parse_args();check(v.root)
