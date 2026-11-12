#!/usr/bin/env python3
"""Independent 100-digit mathematical and SHA-256 audit for WP-012.

The input decimal strings are explicitly converted to binary64 and then to
mpmath values: this tests the *actual numerical inputs* passed to paceval.
Hash chaining is verified against a terminal digest. For provenance assurance,
that terminal digest must additionally be retained/anchored outside this folder.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
import mpmath as mp
mp.mp.dps = 100
GENESIS = '0' * 64

def rows(path):
    with Path(path).open(newline='', encoding='utf8') as f:
        return list(csv.DictReader(f))

def sha(s):
    return hashlib.sha256(s.encode('utf8')).hexdigest()

def equal(value, reference, tol=mp.mpf('1e-11')):
    return abs(mp.mpf(float(value)) - reference) <= tol * (1 + abs(reference))

def audit(directory, do_tamper=True):
    root = Path(directory)
    models = rows(root / 'models.csv')
    formulas = {(r['node_id'], r['version']):r for r in models}
    assert len(formulas) == 5, 'missing model catalog entries'
    for m in models:
        raw = '|'.join((m['node_id'], m['version'], m['expression'], m['variables']))
        assert m['sha256'] == sha(raw), 'invalid immutable formula digest'
    raw_lines = (root / 'requests.csv').read_text(encoding='utf8').splitlines()[1:]
    input_digests = Counter(sha(s) for s in raw_lines)
    results = rows(root/'results.csv')
    accepted = [r for r in results if r['status'] == 'OK']
    rejected = [r for r in results if r['status'] == 'REJECTED']
    assert len(results) == len(raw_lines), 'request response accounting mismatch'
    expected = {}
    for r in accepted:
        assert r['formula_id'] == 'CHAIN_LOGRATIO'
        x = mp.mpf(float(r['x'])); a = mp.mpf(float(r['a']))
        assert abs(1+a*x) >= mp.mpf('0.05') - mp.mpf('1e-15')
        t1=x*x; t2=mp.log(1+t1); t3=1+a*x
        z=t2/t3 + (mp.mpf('0.05')*x if r['version']=='1.1' else mp.mpf('0'))
        expected[r['request_id']] = (r['version'],(t1,t2,t3,z))
        assert equal(r['result'],z), 'incorrect final result '
    steps = rows(root/'steps.csv')
    assert len(steps) == len(accepted)*4
    stage_map = defaultdict(set)
    max_err = mp.mpf('0')
    for row in steps:
        rid = row['request_id'];version, reference = expected[rid]
        step = int(row['step']);assert 1<=step<=4
        assert step not in stage_map[rid], 'duplicate stage output'
        stage_map[rid].add(step)
        node = ('SQUARE','LOG1P','DENOM','RATIO')[step-1]
        mver = version if step==4 else '1.0'
        assert row['node_id'] == node and row['formula_sha256'] == formulas[(node,mver)]['sha256']
        rref = reference[step-1]
        assert equal(row['value'],rref),f'high precision mismatch {rid}:{step}'
        assert equal(row['native_reference'],rref),f'native reference mismatch {rid}:{step}'
        calcerr=abs(mp.mpf(float(row['value']))-mp.mpf(float(row['native_reference'])))
        assert abs(calcerr-mp.mpf(float(row['abs_error'])))<=mp.mpf('5e-11')
        max_err=max(max_err,abs(mp.mpf(float(row['value']))-rref))
    assert all(len(s)==4 for s in stage_map.values()),'incomplete computation chain'
    vcomp=rows(root/'version_comparison.csv')
    assert len(vcomp)==16
    for r in vcomp:
        a=mp.mpf(float(r['x']));difference=mp.mpf(float(r['version_1_1']))-mp.mpf(float(r['version_1_0']))
        assert abs(difference-mp.mpf('0.05')*a)<mp.mpf('1e-11')
    # Verify the audit chain independently (including identities and inputs).
    audit_rows=rows(root/'audit_steps.csv')
    assert len(audit_rows)==len(accepted)*6+len(rejected)
    head=GENESIS; seen_inputs=Counter(); rejected_digests=Counter()
    count=Counter(); rejection_count=0
    for seq,r in enumerate(audit_rows,1):
        assert int(r['sequence'])==seq and r['previous_hash']==head,'broken sequence or prev digest'
        payload='|'.join([str(seq),r['request_id'],r['kind'],r['step'],r['node_id'],
                         r['version'],r['formula_hash'],r['value'],r['status'],r['reason']])
        head=sha(head+'|'+payload)
        assert head==r['record_hash'], 'AUDIT TAMPERING DETECTED'
        rid=r['request_id'];kind=r['kind']
        if kind=='INPUT':
            assert r['status']=='OK' and r['formula_hash']==sha('request_id,formula_id,version,x,a,unit')
            assert r['value'] in input_digests,'input was not bound to recorded request'
            seen_inputs[r['value']]+=1
        elif kind=='STEP':
            count[(rid,'STEP')]+=1
            step=int(r['step']); node=('SQUARE','LOG1P','DENOM','RATIO')[step-1]
            version,ref=expected[rid]
            mver=version if step==4 else '1.0'
            assert r['node_id']==node and r['formula_hash']==formulas[(node,mver)]['sha256']
            assert equal(r['value'],ref[step-1]),'incorrect auditable intermediate'
        elif kind=='RESULT':
            count[(rid,'RESULT')]+=1
            assert equal(r['value'],expected[rid][1][3])
        elif kind=='REJECT':
            rejection_count+=1
            rejected_digests[r['value']]+=1
            assert r['status']=='REJECTED' and r['reason']
        else:
            raise AssertionError('unexpected audit event type')
    assert all(count[(rid,'STEP')]==4 and count[(rid,'RESULT')]==1 for rid in expected)
    assert rejection_count==len(rejected)
    assert not (seen_inputs-input_digests) and not(rejected_digests-input_digests)
    assert sum(seen_inputs.values())==len(accepted)
    assert sum(rejected_digests.values())==len(rejected)
    manifest=(root/'audit_head.txt').read_text().splitlines()
    assert manifest == ['SHA256-CHAIN-V1',str(len(audit_rows)),head],'audit head mismatch'
    # TINC: report every inclusion using exact binary64 operands, no widening.
    tinc=rows(root/'tinc_samples.csv');included=0;excluded=[]
    for r in tinc:
        x=mp.mpf(float(r['x']));correct=mp.log(1+x*x)
        lo=mp.mpf(float(r['low']));hi=mp.mpf(float(r['high']))
        assert lo<=hi and equal(r['value'],correct)
        if lo<=correct<=hi:included+=1
        else:excluded.append(int(r['sample']))
    assert len(tinc)==24 and set(excluded).issubset({12}), 'unexpected new TINC non-inclusion'
    result={'accepted_requests':len(accepted),'rejected_requests':len(rejected),
            'high_precision_step_results':len(steps),'audit_entries':len(audit_rows),
            'audit_head':head,'formula_versions':len(formulas),
            'max_high_precision_step_error':mp.nstr(max_err,8),
            'tinc_sample_count':len(tinc),'tinc_inclusions':included,
            'tinc_non_inclusion_indices':excluded,'precision_digits':100,
            'audit_hash_check':'PASS','high_precision_check':'PASS'}
    if do_tamper:
        altered=dict(audit_rows[0]);altered['value']='000000';
        payload='|'.join([altered['sequence'],altered['request_id'],altered['kind'],altered['step'],
         altered['node_id'],altered['version'],altered['formula_hash'],altered['value'],altered['status'],altered['reason']])
        result['tamper_detection_test'] = 'PASS' if sha(GENESIS+'|'+payload)!=altered['record_hash'] else 'FAIL'
        assert result['tamper_detection_test']=='PASS'
    return result

if __name__=='__main__':
    folder=Path(sys.argv[1]) if len(sys.argv)>1 else Path('examples')
    details=audit(folder)
    print(json.dumps(details,indent=2))
    # Do not overwrite the immutable example data during verification.
