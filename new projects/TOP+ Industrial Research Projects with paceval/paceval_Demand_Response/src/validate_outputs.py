#!/usr/bin/env python3
"""Independent, high-precision (90 digit) DR audit without invoking paceval.

The audit recomputes every synthetic rule evaluation from exported *binary64*
inputs and coefficients. It also checks raw TINC bounds using an exact
Decimal-from-float interpretation, zero-valued rejected claims, and 24-hour
energy reconciliation. This does not certify arbitrary TINC interval outputs.
"""
import argparse, csv, json
from decimal import Decimal, localcontext
from pathlib import Path

def records(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def d(x):
    # The C++ SDK receives IEEE-754 doubles; avoid decimal-text rounding here.
    return Decimal.from_float(float(x))

def expected(r, e):
    D=d(e['delivered_kwh']); Q=d(e['requested_kwh'])
    PE=d(e['event_price_eur_kwh']); PR=d(e['recovery_price_eur_kwh'])
    A=d(r['alpha']); B=d(r['bonus_eur_per_kwh'])
    PEN=d(r['penalty_eur_per_kwh2']); COM=d(r['comfort_eur_per_kwh2'])
    CUB=d(r['cubic_eur_per_kwh3']); fam=int(r['family'])
    x=A*D*(PE-PR)+B*D
    if fam>=1: x-=PEN*(Q-D)**2
    if fam>=2: x-=COM*D**2
    if fam>=3: x-=CUB*D**3
    return x

def run(folder):
    rules=records(folder/'rules.csv')
    events=records(folder/'evaluations.csv')
    hours=records(folder/'hourly_trace.csv')
    tins=records(folder/'tinc_samples.csv')
    updates=records(folder/'model_update.csv')
    assert rules and events and hours and tins
    index={int(r['rule_id']):r for r in rules}
    assert len(events)==len(rules)*len(hours)
    errors=0; maximum=Decimal(0); bad=[]
    checked=0; false_claim_checks=0; excluded_checks=0
    with localcontext() as ctx:
        ctx.prec=90
        for e in events:
            rid=int(e['rule_id']); r=index[rid]
            reference=expected(r,e); actual=d(e['value_eur'])
            err=abs(actual-reference); maximum=max(err,maximum)
            tol=Decimal('5e-12')*(1+abs(reference))
            checked+=1
            if err>tol: errors+=1;bad.append((rid,e['hour_index'],str(err)))
            h=hours[int(e['hour_index'])]
            # Unmetered claims must not produce a positive modeled reward.
            if h['event']=='1' and h['quality']=='1' and float(h['requested_kwh'])>0 and float(h['actual_kwh'])>=float(h['baseline_kwh']):
                assert actual<=Decimal('1e-14'), 'false positive claim generated credit'
                false_claim_checks+=1
            if h['event']=='1' and h['quality']=='0':
                assert actual==0, 'bad-quality event generated a modeled value'
                excluded_checks+=1
        assert errors==0, f'High precision mismatch first 5: {bad[:5]}'
        assert false_claim_checks>0 and excluded_checks>0
        for i in range(0,len(hours),24):
            block=hours[i:i+24]; assert len(block)==24
            base=sum((d(h['baseline_kwh']) for h in block),Decimal(0))
            actual=sum((d(h['actual_kwh']) for h in block),Decimal(0))
            assert abs(base-actual)<Decimal('3e-10'), 'daily energy mismatch'
        tin_ok=0; tin_fail=[]
        for r in tins:
            result=d(r['delivered_kwh'])*(d(r['event_price'])-d(r['recovery_price']))
            low=d(r['raw_lower']); high=d(r['raw_upper'])
            if low<=result<=high:tin_ok+=1
            else:tin_fail.append(r['sample_id'])
        assert tin_ok==len(tins), f'TINC value missed: {tin_fail}'
        assert len(updates)>0, 'model update missing'
        assert all(x['unrelated_graph_unchanged']=='true' for x in updates)
    audit={"source":"independent Python decimal audit from binary64 inputs; 90 digits",
        "models":len(rules),"hours":len(hours),"evaluations_checked":checked,
        "max_absolute_difference_eur":str(maximum),"tolerance":"5e-12*(1+abs(reference))",
        "tinc_raw_inclusions":tin_ok,"tinc_samples":len(tins),
        "false_claim_outputs_checked":false_claim_checks,
        "quality_excluded_outputs_checked":excluded_checks,
        "daily_energy_conservation_checked":len(hours)//24,
        "model_updates_checked":len(updates),"status":"PASS"}
    print(json.dumps(audit,indent=2))
    return audit
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dir',type=Path,required=True)
    ap.add_argument('--write-audit',type=Path)
    args=ap.parse_args(); result=run(args.dir)
    if args.write_audit:args.write_audit.write_text(json.dumps(result,indent=2)+'\n')
