#!/usr/bin/env python3
"""Check exported outputs and independent finite-grid argmin and immutable revision."""
from pathlib import Path
import csv,json
root=Path(__file__).resolve().parents[1];d=root/'examples'
def load(s):return list(csv.DictReader(open(d/s)))
allrows=load('trajectory_candidates.csv');winners=load('selected_trajectories.csv');points=load('selected_path_points.csv');registry=load('formula_registry.csv');audit=load('numeric_audit.csv')
assert len(allrows)==80 and len(winners)==5 and len(points)==255 and len(registry)==5
for w in winners:
 sub=[r for r in allrows if r['policy']==w['policy'] and r['version']==w['version'] and int(r['feasible'])]
 assert sub
 assert min(sub,key=lambda v:float(v['total_cost']))['candidate']==w['candidate']
 assert all(float(r['margin_m2'])>=0 for r in points if r['policy']==w['policy'] and r['version']==w['version'])
assert registry[1]['expression'] != registry[-1]['expression']
assert audit[0]['passed']=='true'
info={'candidate_policy_pairs':len(allrows),'selected_policies':len(winners),'sampled_selected_points':len(points),'formula_versions':len(registry),'scalar_comparisons':int(audit[0]['comparison_count']),'batch_results':int(audit[0]['batch_count']),'passed':True}
(root/'results'/'results_audit.json').write_text(json.dumps(info,indent=2)+'\n')
print('PASS exported trajectory selection and version checks:', info)
