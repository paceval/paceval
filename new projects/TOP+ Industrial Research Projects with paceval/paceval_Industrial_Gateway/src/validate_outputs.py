#!/usr/bin/env python3
"""Independent scientific audit of the industrial gateway replay.

Uses mpmath at 90 decimal digits, checks ALL rows against the rule/telemetry
contracts, reproduces the host-owned alarm persistence logic, and separately
reports TINC pointwise sample containment. Runtime outputs are not used to
calculate the reference values. No real telemetry or gateway is involved.
"""
import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
import mpmath as mp
mp.mp.dps = 90

def read_csv(path):
    with Path(path).open(newline="",encoding="utf-8") as fp:
        return list(csv.DictReader(fp))

def m(x): return mp.mpf(str(x))

def reference(rule, inp):
    T=m(inp['temp_C']); V=m(inp['vibration_mm_s']); I=m(inp['current_A'])
    t=(T-70)/40; v=V/2; i=max(mp.mpf(0),I-m(rule['current_limit_A']))/8
    a=m(rule['w1']);b=m(rule['w2']);c=m(rule['w3']);d=m(rule['w4'])
    fam=int(rule['family']); z=a*t+b*v+c*i
    if fam==1: return mp.tanh(z)
    if fam==2: return a*t*t+b*v*v+c*i*i
    if fam==3: return z+d*t*v
    return z

def audit(directory, output, tinc=None, updated=None, sampled=600):
    directory=Path(directory)
    tele=read_csv(directory/'telemetry.csv')
    rules=read_csv(directory/'rules.csv')
    results=read_csv(output)
    assert len(tele)==12000 and len(rules)==100 and len(results)==24000
    tmap={(int(row['tick']),int(row['channel'])):row for row in tele}
    rmap={int(r['rule_id']):r for r in rules}
    reasons=Counter(); statuses=Counter(); alarm_streak={k:0 for k in rmap}; alarm_active={k:False for k in rmap}
    max_abs=0.; max_hp=0.;hp_count=0; regular=0; invalid=0; alarms=0
    # Sample high precision at fixed cadence across rules and ticks without
    # choosing cases on the basis of observed numerical errors.
    for row in results:
        rid=int(row['rule_id']);tick=int(row['tick']);r=rmap[rid]
        assert int(row['channel'])==int(r['channel'])
        source=tmap[tick,int(row['channel'])]
        assert int(row['timestamp_ms'])==int(source['timestamp_ms'])
        assert row['quality']==source['quality']
        assert row['version']==r['version']
        assert float(row['threshold'])==float(r['threshold'])
        statuses[row['status']]+=1
        if source['quality']!='GOOD':
            assert row['status']=='NO_DATA' and not row['score'] and not row['native_reference'] and row['alarm']=='0'
            invalid+=1;reasons[source['quality']]+=1
            alarm_streak[rid]=0;alarm_active[rid]=False
            continue
        assert row['status'] in ('ALERT','NORMAL')
        assert row['score'] and row['native_reference']
        value=float(row['score']);native=float(row['native_reference'])
        assert math.isfinite(value) and math.isfinite(native)
        err=abs(value-native);max_abs=max(max_abs,err)
        assert err<=2e-11*(1+abs(native)),(tick,rid,err)
        regular+=1
        if (rid*19+tick*43)%37==0 and hp_count<sampled:
            high=reference(r,source); diff=abs(mp.mpf(value)-high)
            max_hp=max(max_hp,float(diff))
            assert diff<=mp.mpf('2e-11')*(1+abs(high)),(tick,rid,diff)
            hp_count+=1
        if value>float(row['threshold']):
            alarm_streak[rid]+=1
            if alarm_streak[rid]>=3:alarm_active[rid]=True
        else:
            alarm_streak[rid]=0
            if value<=float(row['threshold'])-0.025:alarm_active[rid]=False
        expected='ALERT' if alarm_active[rid] else 'NORMAL'
        assert row['status']==expected and row['alarm']==str(int(alarm_active[rid])),(tick,rid,expected,row['status'])
        alarms+=int(alarm_active[rid])
    assert regular+invalid==24000
    tinc_inside=0;tinc_rows=0;max_tinc_abs=0.
    if tinc:
        for row in read_csv(tinc):
            source=tmap[int(row['tick']),int(row['channel'])]
            r=rmap[0]
            hp=reference(r,source)
            lo=m(row['tinc_low']);hi=m(row['tinc_high']);p=m(row['paceval_value'])
            assert lo<=hi and math.isfinite(float(p))
            assert abs(p-hp)<=mp.mpf('2e-11')*(1+abs(hp))
            max_tinc_abs=max(max_tinc_abs,float(abs(p-hp)))
            if lo<=hp<=hi:tinc_inside+=1
            tinc_rows+=1
        assert tinc_rows==24
    delta_ids=set();number_delta=0
    if updated:
        other=read_csv(updated)
        assert len(other)==len(results)
        for old,new in zip(results,other):
            rid=int(old['rule_id'])
            if old!=new:
                delta_ids.add(rid)
                number_delta+=1
                assert rid==17 and new['version']=='1.1'
            else:
                assert rid!=17
        assert delta_ids=={17}
    report={
        'replay_rows':len(tele),'channels':50,'rules':100,'candidate_evaluations':len(results),
        'accepted':regular,'rejected':invalid,'quality_rejections':dict(reasons),
        'alert_rows':alarms,'result_statuses':dict(statuses),
        'native_max_absolute_difference':max_abs,
        'high_precision_sampled':hp_count,'high_precision_decimal_digits':mp.mp.dps,
        'high_precision_max_absolute_difference':max_hp,
        'tinc_sample_count':tinc_rows,'tinc_containment_count':tinc_inside,
        'tinc_max_absolute_difference':max_tinc_abs,
        'updated_rule_ids':sorted(delta_ids),'updated_rule_output_rows':number_delta,
        'high_precision_tolerance':'2e-11*(1+abs(reference))',
        'test_scope':'synthetic replay only; no OPC UA or MQTT runtime, plant data, or safety qualification'
    }
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--examples',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--tinc')
    parser.add_argument('--updated')
    parser.add_argument('--json-out')
    args=parser.parse_args()
    result=audit(args.examples,args.output,args.tinc,args.updated)
    if args.json_out:Path(args.json_out).write_text(json.dumps(result,indent=2)+'\n')
