#!/usr/bin/env python3
from pathlib import Path
import csv,json,math
ROOT=Path(__file__).resolve().parent.parent
read=lambda p:list(csv.DictReader((ROOT/'examples'/p).open()))
sumrows=read('scenario_summary.csv');trace=read('selected_event_timeline.csv');station=read('station_performance.csv');steps=read('paceval_operation_results.csv')
assert len(sumrows)>=1 and len(station)==4*len(sumrows)
for s in sumrows:
 n=int(s['arrivals']);g=int(s['completed_good']);bad=int(s['scrapped']);assert g+bad==n and n>0
 assert abs(float(s['paceval_line_yield'])-g/n)<1e-12
 assert abs(float(s['paceval_good_throughput_units_hr'])-60*g/float(s['simulated_minutes']))<1e-10
 assert 0<=float(s['paceval_blocked_fraction'])<=1
# Validate all imported operation data and formula registry layout, with actual row count from original saved trace.
assert len(steps)==int(sumrows[0]['arrivals'])*4
for r in steps:
 for k in range(1,21):assert math.isfinite(float(r[f'cycle_v{k:02d}'])) and float(r[f'cycle_v{k:02d}'])>0
 assert 0<float(r['energy_kWh']) and 0<=float(r['reject_probability'])<.1
# Full baseline event log order, no station overlaps, no later-stage start before previous-stage finish.
by_station={s:[] for s in range(1,5)};by_job={}
for r in trace:
 s=int(r['station']);j=int(r['job']);a=float(r['operation_start_min']);e=float(r['operation_finish_min']);assert e>a
 by_station[s].append((a,e,j));by_job.setdefault(j,{})[s]=(a,e)
for s,v in by_station.items():
 v.sort()
 for (a0,b0,_),(a1,b1,_) in zip(v,v[1:]):assert a1>=b0-1e-8,('station overlap',s,a1,b0)
for j,stages in by_job.items():
 for s in range(1,4):
  if s+1 in stages:assert stages[s+1][0]>=stages[s][1]-1e-8
assert len(by_job)==int(sumrows[0]['arrivals'])
rec={'passed':True,'scenarios':len(sumrows),'operation_rows':len(steps),'baseline_event_operations':len(trace),'checked_station_nonoverlap':True,'checked_stage_precedence':True,'checked_output_conservation':True,'source':'executed original paceval CSV outputs plus deterministic C++ event trace'}
(ROOT/'results'/'trace_integrity_audit.json').write_text(json.dumps(rec,indent=2)+'\n');print(rec)
