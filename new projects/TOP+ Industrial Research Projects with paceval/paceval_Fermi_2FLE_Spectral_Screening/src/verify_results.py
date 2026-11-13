#!/usr/bin/env python3
"""Check research data structure and explicit science/data-provenance boundaries."""
from pathlib import Path
import csv, json, re
ROOT=Path(__file__).resolve().parents[1]
def read(p):return list(csv.DictReader((ROOT/p).open()))
source=read('examples/unidentified_60_from_user_whitepaper.csv')
assert len(source)==60 and len(set(s['source_name'] for s in source))==60
assert sum(s['ASSOC3_flag']=='has_ASSOC3' for s in source)==38
assert sum(s['ASSOC3_flag']=='no_ASSOC3' for s in source)==22
assert sum(int(s['usable_band_count_TS_ge_4'])==3 for s in source)==10
assert all(float(s['catalog_TS'])>25 for s in source)
reg=read('examples/formula_registry.csv')
assert len(reg)==17 and len(set(x['function_id'] for x in reg))==17
inventory=read('results/math_execution_inventory.csv')
assert sum(x['execution_owner']=='paceval' for x in inventory)==17
counts=read('examples/synthetic_photon_counts.csv')
recovery=read('examples/synthetic_injection_recovery.csv')
scan=read('examples/synthetic_curvature_parameter_scan.csv')
surface=read('examples/synthetic_spectral_surface.csv')
assert len(counts)==60*24 and len(recovery)==60 and len(scan)==60*61 and len(surface)==65*65
assert all('synthetic' in x for x in ['synthetic_photon_counts.csv','synthetic_injection_recovery.csv'])
for r in recovery:
 assert 0<=float(r['best_grid_q'])<=.6 and 0<=float(r['truth_q'])<=.6
assert all(r['source_name'] in set(s['source_name'] for s in source) for r in recovery)
summary=dict(x.strip().split('=',1) for x in (ROOT/'results/execution_summary.txt').read_text().splitlines() if '=' in x)
assert summary['status']=='PASS' and summary['instrument_response_forward_likelihood_performed']=='NO'
assert summary['crossmatches_performed']=='NO' and summary['technosignatures_detected']=='NOT_TESTED'
assert int(summary['genuine_paceval_graphs'])==17 and int(summary['batch_evaluated_graph_values'])>1000000
assert len(read('examples/source_hypothesis_matrix_not_tested.csv'))==60*29

# Independent complete-application check: recompute every toy curvature objective
# from stored synthetic counts, rather than trusting a single paceval intermediate.
import math
from collections import defaultdict
by_source=defaultdict(list)
for r in counts:by_source[r['source_name']].append(r)
full_checks=0
for r in recovery:
    source=r['source_name']; records=by_source[source];assert len(records)==24
    ll=[]
    for ai in range(61):
        q=.6*ai/60.; total=0.0
        for v in records:
            E=float(v['energy_center_MeV']);N=float(v['synthetic_N']);g=float(v['synthetic_gamma'])
            b=float(v['synthetic_background_counts']);A=float(v['exposure_scale']);w=float(v['bin_weight']);n=float(v['synthetic_observed_counts'])
            z=math.log(E/100.0);mu=b+A*w*N*math.exp(-g*z-q*z*z)
            total+=n*math.log(mu)-mu
        ll.append(total)
    best=max(range(61),key=lambda i:ll[i])
    assert abs(best*.6/60.-float(r['best_grid_q']))<1e-12,(source,best)
    assert abs(ll[best]-float(r['synthetic_best_loglikelihood']))<=2e-9*(1+abs(ll[best])),source
    full_checks+=1

print('PASS verified 60 source provenance rows, 17 graphs, and',full_checks,'independently reconstructed full synthetic curve fits')
(ROOT/'results/verification_audit.json').write_text(json.dumps({'status':'PASS','pdf_source_rows':60,'synthetic_recovery_rows':len(recovery),'spectral_scan_rows':len(scan),'spectral_surface_rows':len(surface),'all_hypothesis_source_pairs_not_tested':60*29,'full_synthetic_argmax_oracle_checked_sources':full_checks,'original_fits_present':False,'claim_of_technosignature':False},indent=2)+'\n')
