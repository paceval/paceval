#!/usr/bin/env python3
"""Independent decimal arithmetic validation of selected exported paceval samples.
Uses analytical equations, NOT the paceval output or its expression parser to calculate reference values.
The source CSV records binary64 input values with 17 significant digits; decimal reference
therefore compares against that faithfully exported representation.
"""
from pathlib import Path
import csv, json
from decimal import Decimal, localcontext
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'examples'
D=Decimal

def reference(rule, row):
    p,m=D(row['power_w']),D(row['flow_mg_s'])
    base,peak=D(rule['eta_base']),D(rule['eta_peak'])
    eta=base+peak*(-(((p-D(1700))/D(900))**2+((m-D('4.5'))/D(2))**2)).exp()
    force=(D(2)*eta*p*m*D('0.000001')).sqrt()
    family=int(rule['family'])
    return [eta,force*1000,force/(m*D('0.000001')*D('9.80665')),
            force*D(1000000)/p,p*(1-eta)][family-1]

def main():
    with localcontext() as ctx:
        ctx.prec=80
        rules={int(r['rule_id']):r for r in csv.DictReader(open(DATA/'rule_registry.csv'))}
        rows=list(csv.DictReader(open(DATA/'performance_replay.csv')))
        selected=rows[:500]
        max_diff=D(0)
        for row in selected:
            got=D(row['value']); expected=reference(rules[int(row['rule_id'])],row)
            deviation=abs(got-expected)
            max_diff=max(max_diff,deviation)
            assert deviation <= D('0.000000003')*(1+abs(expected)),row
        audit={'status':'PASS','precision_digits':80,'samples':len(selected),
               'max_absolute_diagnostic':str(max_diff),
               'method':'Independent decimal functions and exp/sqrt; exported input values'}
    out=ROOT/'results'/'high_precision_audit.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(audit,indent=2)+'\n')
    print('PASS independent decimal samples:',len(selected))
if __name__=='__main__':main()
