#!/usr/bin/env python3
"""Independent 80-decimal verification of all recorded original paceval graph probes.
Mathematical definitions are written independently; no eval() of paceval strings.
"""
import argparse,csv,json,math
from pathlib import Path
import mpmath as mp
mp.mp.dps=80

def read(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))

def M(a):return mp.mpf(float(a))  # exact input binary64 interpreted at high precision

def expected(c,p,ops):
 # Reconstruct all central metrics using independent mathematics, including derivatives w.r.t. policy weights.
 completion=[]
 for j in range(4):
  op=next(r for r in ops if int(r['job'])==j and int(r['step'])==2)
  completion.append(M(op['end_h']))
 due=([10,11,12,14] if c['urgent_due']=='1' else [12,14,18,17])
 due=[M(x) for x in due];priority=list(map(M,(2.,1.6,1.2,1.9)))
 lateness=[cc-dd for cc,dd in zip(completion,due)]
 late=[max(mp.mpf('0'),l) for l in lateness];early=[max(mp.mpf('0'),-l) for l in lateness]
 wm=M(p['makespan_weight']);wt=M(p['tardiness_weight']);ws=M(p['changeover_weight']);we=M(p['energy_weight']);budget=M(p['budget'])
 mk=M(c['makespan_h']);setup=M(c['setup_h']);switches=M(c['switches']);idle=M(c['idle_h']);
 # C++ processing energy is accumulated in binary64. The exact binary64 accumulation is passed as graph input.
 # 3 jobs x operations and two rates used by the mathematical execution path.
 energy=M(float(sum(t[3]*(1.5,1.1,1.8)[t[2]] for t in [
   (0,0,0,3),(0,1,1,2),(0,2,2,2),(1,0,0,2),(1,1,2,1),(1,2,1,4),
   (2,0,1,4),(2,1,2,3),(2,2,0,1),(3,0,2,2),(3,1,0,4),(3,2,1,3)])))
 T=sum(x*w for x,w in zip(late,priority));TSQ=sum(x*x*w for x,w in zip(late,priority));E=sum(early)
 mx=max(late);setUnits=setup+mp.mpf('0.5')*switches;energyTotal=energy+mp.mpf('0.25')*setup
 mc=wm*mk/30;tc=wt*T/25;sc=ws*setUnits/20;ec=we*energyTotal/60
 objective1=mc+tc+sc+ec
 tailrisk=wt*mp.mpf('0.15')*TSQ/250;idlecost=mp.mpf('0.06')*idle/60;worstcost=mp.mpf('0.04')*(mx/15)**2
 objective2=objective1+tailrisk+idlecost+worstcost
 d={}
 for j in range(4):
  d['lateness_job'+str(j)]=lateness[j]
  d['tardiness_job'+str(j)]=late[j]
  d['earliness_job'+str(j)]=early[j]
  d['due_margin_job'+str(j)]=-lateness[j]
  d['weighted_tardiness_job'+str(j)]=priority[j]*late[j]
 d.update(weighted_tardiness_total=T,weighted_tardiness_squared=TSQ,total_earliness=E,
          maximum_positive_lateness=mx,minimum_due_margin=min([-x for x in lateness]),
          sequence_changeover_hours=M(c['setup_scale_h']),operation_finish=M(next(r for r in ops if int(r['operation'])==0)['start_h'])+3,
          energy_total=energyTotal,setup_units=setUnits,machine_utilization=1-idle/(3*mk),operating_horizon_margin=34-mk,
          risk_budget_margin_v1=budget-objective1,risk_budget_margin_v2=budget-objective2,
          makespan_component=mc,tardiness_component=tc,changeover_component=sc,energy_component=ec,
          risk_tardiness_component_v2=tailrisk,idle_component_v2=idlecost,worst_delay_component_v2=worstcost,
          policy_objective_v1=objective1,policy_objective_v2=objective2,objective_revision_v2_minus_v1=objective2-objective1,
          d_objective_d_wmakespan_v1=mk/30,d_objective_d_wtardiness_v1=T/25,
          d_objective_d_wsetup_v1=setUnits/20,d_objective_d_wenergy_v1=energyTotal/60,
          d_objective_d_wtardiness_v2=T/25+mp.mpf('0.15')*TSQ/250,
          d_objective_d_wenergy_v2=energyTotal/60,
          composite_service_index=1/(1+T/20),schedule_dispersion=((sum(completion)/4)-(mk/2))**2,
          composite_priority_score=objective2+mp.mpf('0.015')*E/30)
 return d

def check(root):
 policy={r['policy']:r for r in read(root/'examples/agent_requests.csv')}
 sums={r['scenario']:r for r in read(root/'results/scenario_summary.csv')}
 ops={}
 for r in read(root/'examples/best_schedules.csv'):ops.setdefault(r['scenario'],[]).append(r)
 rows=read(root/'results/graph_probe_values.csv');assert len(rows)==32*52
 cache={key:expected(s,policy[s['policy']],ops[key]) for key,s in sums.items()}
 checked=0;maxscaled=mp.mpf(0);fail=[]
 for r in rows:
  key=r['scenario'];name=r['graph_id'];ref=cache[key][name]
  val=M(r['paceval_value'])
  scaled=abs(val-ref)/(1+abs(ref));maxscaled=max(scaled,maxscaled)
  if scaled>mp.mpf('4e-12'):fail.append((key,name,str(val),str(ref)))
  checked+=1
 assert not fail,fail[:10]
 report={'status':'PASS','mpmath_decimal_precision':mp.mp.dps,'high_precision_independent_graph_checks':checked,
         'distinct_scenarios_checked':len(sums),'distinct_graphs_per_scenario':len(rows)//len(sums),
         'max_scaled_absolute_difference':str(maxscaled),'reference_implementation':'handwritten_80_digit_mpmath_definitions_not_paceval_formula_eval',
         'note':'Pointwise tests do not prove a global interval guarantee or real-shop-floor model validity'}
 (root/'results/high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS 80-digit independent formula checks',checked)
 return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);b=a.parse_args();check(b.root)
