#!/usr/bin/env python3
"""Independent audit using Decimal's exact binary-float conversion at 110 digits.

This file never calls paceval and does not reuse the C++ reference functions.
It checks the saved inputs, the 200 random rule/record combinations, the
selected explanation decomposition, event detection, and raw TINC bounds.
"""
import argparse, csv, json, math
from decimal import Decimal, localcontext
from pathlib import Path

def d(x):
    """Recover the exact IEEE-754 double passed to the C++ engine."""
    return Decimal.from_float(float(x))

def rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def expected(r):
    v=[d(r[k]) for k in ('x','mu','sigma','dx','ds','c','cs','eps','w0','w1','w2')]
    x,mu,sigma,dx,ds,c,cs,eps,w0,w1,w2=v
    family=int(r['family'])
    z=(x-mu)/(sigma+eps)
    v=dx/(ds+eps)
    ctx=c/(cs+eps)
    terms=[w0*(z*z if family==2 else abs(z)),
           w1*(v*v if family==1 else abs(v)),
           w2*(ctx*ctx if family==3 else abs(ctx))]
    return sum(terms),terms

def validate(folder):
    with localcontext() as ctx:
        ctx.prec=110
        audits=rows(folder/'audit_samples.csv')
        assert len(audits)==200
        max_error=Decimal(0)
        for r in audits:
            true,_=expected(r)
            result=d(r['paceval_score'])
            diff=abs(result-true)
            max_error=max(max_error,diff)
            assert diff <= Decimal('5e-12')+abs(true)*Decimal('2e-12'), (r,diff)
        selected=rows(folder/'selected_scores.csv')
        policies=rows(folder/'rules.csv')
        models={int(r['rule_id']):r for r in policies}
        signals=rows(folder/'signals.csv')
        assert len(selected)==len(signals)==4096 and len(policies)==100
        good=0
        max_expl_error=Decimal(0)
        for s,original in zip(selected,signals):
            assert (s['channel'],s['minute'],s['quality'])==(original['channel'],original['minute'],original['quality'])
            if s['quality']!='GOOD':
                assert s['score']=='' and s['persistent_alarm']=='0'
                continue
            good+=1
            model=models[int(s['selected_rule'])]
            data={'family':s['family'],
                  'x':original['x'],'mu':original['mu'],'sigma':original['sigma'],
                  'dx':original['dx'],'ds':original['ds'],'c':original['context'],
                  'cs':original['context_scale'],'eps':original['eps'],
                  'w0':model['w0'],'w1':model['w1'],'w2':model['w2']}
            value,parts=expected(data)
            result=d(s['score'])
            diff=abs(result-value)
            assert diff<= Decimal('5e-12')+abs(value)*Decimal('2e-12')
            for field,term in zip(('deviation_component','derivative_component','context_component'),parts):
                comp_diff=abs(d(s[field])-term)
                max_expl_error=max(max_expl_error,comp_diff)
                assert comp_diff<Decimal('5e-12')
        assert good==4080
        # Recompute confusion metrics exclusively from saved score/labels.
        byfamily={f:[] for f in range(4)}
        for r in selected:
            if r['quality']=='GOOD' and r['split']=='test':byfamily[int(r['family'])].append(r)
        selected_rules=rows(folder/'selection.csv')
        for m in selected_rules:
            rr=byfamily[int(m['family'])]
            tp=sum(int(r['truth'])==1 and int(r['raw_alarm'])==1 for r in rr)
            fp=sum(int(r['truth'])==0 and int(r['raw_alarm'])==1 for r in rr)
            fn=sum(int(r['truth'])==1 and int(r['raw_alarm'])==0 for r in rr)
            assert (tp,fp,fn)==tuple(int(m[k]) for k in ('test_tp','test_fp','test_fn'))
        event=rows(folder/'event_detection.csv')
        assert len(event)==32
        test_events=[r for r in event if r['split']=='test']
        assert len(test_events)==8
        detected=sum(int(r['detected']) for r in test_events)
        summary=json.loads((folder/'validation.json').read_text())
        assert summary['evaluated_score_count']==408000
        assert summary['quality_skipped_rows']==16
        assert summary['test_events_detected']==detected
        assert summary['test_events']==8
        assert len(rows(folder/'rule_update.csv'))==24
        tinc=rows(folder/'tinc_samples.csv')
        assert len(tinc)==24
        included=0
        for s in tinc:
            x=d(s['x']); true=x*x+Decimal(1)
            lo=d(s['raw_lower']);hi=d(s['raw_upper']);value=d(s['paceval_result'])
            assert lo<=hi and math.isfinite(float(value))
            assert lo<=true<=hi, (s,true)
            included+=1
        report={
            'audit_method':'110-digit Decimal; exact Decimal.from_float for supplied binary64 inputs',
            'independent_score_samples':len(audits),'selected_score_and_explanation_samples':good,
            'independent_score_max_absolute_error':str(max_error),
            'independent_explanation_max_absolute_error':str(max_expl_error),
            'raw_tinc_inclusions':included,'raw_tinc_tested':len(tinc),
            'heldout_test_events_detected':detected,'heldout_test_events':8,
            'validation':'passed'}
        (folder/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--examples',type=Path,required=True)
    validate(p.parse_args().examples)
