#!/usr/bin/env python3
"""Cross-validate the public experiment counts against all recorded CSVs."""
import csv,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'results'
E=json.loads((R/'execution_evidence.json').read_text())
def read(f):
 with (R/f).open(newline='',encoding='utf-8') as x:return list(csv.DictReader(x))
assert E['candidate_count']==1000
assert E['unique_graphs_created']==1031
assert E['unique_graphs_executed']==1031
assert E['graph_point_evaluations']>1000000
assert E['multi_graph_batch_calls']>1000
assert len(read('candidate_search.csv'))==1000
assert len(read('selected_models.csv'))==2
assert len(read('synthetic_kinetics_observations.csv'))==E['training_samples']+E['validation_samples']+E['holdout_samples']
assert len(read('holdout_predictions.csv'))==2*E['holdout_samples']
assert len(read('integrated_reaction_profiles.csv'))==2*8*81
assert len(read('model_response_surface.csv'))==2*2*41*41
assert len(read('model_temperature_and_saturation_curves.csv'))==2*2*91
assert len(read('formula_registry.csv'))==1026
assert len(read('math_execution_inventory.csv'))>=1032
chosen=read('selected_models.csv');assert int(chosen[0]['selected_id'])==E['v1_selected_id']==92
assert int(chosen[1]['selected_id'])==E['v2_selected_id']==301
assert int(chosen[1]['family'])==1 and float(chosen[1]['activation_energy_J_mol'])==36000
V=json.loads((R/'independent_validation.json').read_text())
assert V['status']=='PASS' and V['independent_candidate_scoring_checks']==4000
assert V['independent_high_precision_80_digit_values']>=400
assert (P/'src/paceval_main.cpp').exists() and (P/'src/paceval_main.h').exists()
assert not any(P.rglob('*.so'))
print('WP27 EVIDENCE CONTRACT PASSED',E['unique_graphs_executed'],E['graph_point_evaluations'],V['independent_high_precision_80_digit_values'])
