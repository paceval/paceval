#!/usr/bin/env python3
"""Independent 80-digit audit of exported ORIGINAL paceval result data.
The reference implements the mathematical model separately using mpmath,
not by executing the archived paceval formula strings.
"""
import csv, json, math, pathlib, sys
import mpmath as mp
mp.mp.dps=80

def check(path):
    root=pathlib.Path(path)
    evidence=json.loads((root/'execution_evidence.json').read_text())
    for x in ['unique_graphs_created','unique_graphs_executed','graph_point_evaluations','model_point_rows']:
        assert evidence[x]>0, x
    assert evidence['unique_graphs_created']==evidence['unique_graphs_executed']==60
    assert evidence['model_point_rows']==2*evidence['synthetic_feature_rows']
    n=0;max_error=mp.mpf(0);status_count={'ACTION_CANDIDATE':0,'REVIEW':0,'NO_ACTION':0}
    with (root/'audit_samples.csv').open(newline='') as file:
        for row in csv.DictReader(file):
            v={k:mp.mpf(value) for k,value in row.items() if k not in ['status']}
            # Only historical sampled CSV fields, not binary floats, are available here;
            # tolerance accounts for the documented ~15 significant digit CSV formatting.
            k,N=v['k'],v['n'];raw=k/N;q=(k+mp.mpf('.5'))/(N+1)
            logit=mp.log(q/(1-q))
            anomaly=(v['mean']-v['thr'])/v['scale']
            spread=v['spread']/v['scale']
            season=2*mp.pi*v['doy']/mp.mpf('365.25')
            z=(v['b0']+v['b1']*logit+v['b2']*anomaly+v['b3']*spread+
                v['b4']*v['elev']/1000+v['b5']*mp.sin(season)+v['b6']*mp.cos(season)+
                v['b7']*v['lead']/72)
            if v['version']==2:
                z+=v['b8']*(anomaly*anomaly)/(1+anomaly*anomaly)
            p=1/(1+mp.exp(-z))
            event=v['event'];loss=v['loss'];eff=v['eff'];cost=v['cost']
            brier=(p-event)**2;raw_brier=(raw-event)**2
            margin=p*eff*loss-cost
            br=cost/(eff*loss)
            priority=mp.mpf('.60')*p*loss/(loss+cost)+mp.mpf('.40')/(1+mp.exp(-5*margin/(loss+cost)))
            dz=v['b2']/v['scale']
            if v['version']==2:dz+=v['b8']*2*anomaly/(v['scale']*(1+anomaly*anomaly)**2)
            sens=dz*p*(1-p)
            checks={'raw':raw,'q':q,'logit':logit,'z':z,'prob':p,'brier':brier,
                    'raw_brier':raw_brier,'action_margin':margin,'break_even':br,
                    'priority':priority,'sensitivity_mean':sens}
            for key,expected in checks.items():
                found=v[key];deviation=abs(found-expected)
                max_error=max(max_error,deviation)
                allowed=mp.mpf('3e-10')*max(mp.mpf(1),abs(expected))
                if deviation>allowed:
                    raise AssertionError(f'{key} high precision value differs on row {n}: {deviation}')
            status='ACTION_CANDIDATE' if margin>0 and p>=mp.mpf('.25') else ('REVIEW' if margin>0 else 'NO_ACTION')
            if row['status']!=status:raise AssertionError(f'Categorical mismatch at row {n}: {status} != {row["status"]}')
            status_count[status]+=1
            n+=1
    if n!=evidence['high_precision_audit_candidate_rows']:
        raise AssertionError(f'Audit sample count mismatch {n} vs {evidence["high_precision_audit_candidate_rows"]}')
    # Independent deterministic aggregation consistency check across all scenario categories.
    scenarios=0;sum_cases=0;distinct=set();bins=0
    with (root/'hazard_window_summary.csv').open(newline='') as file:
        for row in csv.DictReader(file):
            scenarios+=1;cases=int(row['cases']);sum_cases+=cases
            assert (int(row['action_candidate'])+int(row['review'])+int(row['no_action']))==cases
            assert all(0<=float(row[key])<=1 for key in ['synthetic_event_frequency','raw_probability_mean','model_probability_mean','brier_score','raw_brier_score'])
            distinct.add((row['hazard'],row['window'],row['version']))
    assert scenarios==24 and len(distinct)==24 and sum_cases==evidence['model_point_rows']
    pairs=0
    with (root/'compound_bounds_samples.csv').open(newline='') as file:
        for row in csv.DictReader(file):
            a,b=mp.mpf(row['p_a']),mp.mpf(row['p_b']);lo=max(mp.mpf(0),a+b-1);hi=min(a,b)
            assert abs(mp.mpf(row['frechet_lower'])-lo)<mp.mpf('1e-12')
            assert abs(mp.mpf(row['frechet_upper'])-hi)<mp.mpf('1e-12')
            assert lo<=hi
            pairs+=1
    assert pairs>0
    report={'reference_precision_decimal_digits':80,'high_precision_audit_rows_verified':n,
            'high_precision_individual_values_verified':n*11,
            'high_precision_compound_pair_samples_verified':pairs,
            'summary_categories_verified':scenarios,'categorical_audit_counts':status_count,
            'mathematical_check':'passed','data_type':'synthetic, not issued weather forecasts'}
    (root/'validation_evidence.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('REFERENCE PASSED: 80-digit high precision rows',n,'values',n*11,'compound pairs',pairs,'summaries',scenarios)

if __name__=='__main__':check(sys.argv[1] if len(sys.argv)>1 else 'results')
