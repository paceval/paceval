#!/usr/bin/env python3
"""Independent high-precision arithmetic audit of exported synthetic credit scorecards.
Requires only Python 3 standard library. Checks exported coefficients/features, logit,
logistic result and positive-contribution rank; it does not validate credit-risk models.
"""
import argparse, csv, decimal, json, sys
from pathlib import Path
from decimal import Decimal as D

def run(path):
    decimal.getcontext().prec=80
    count=0; violations=[]; max_abs=D(0)
    with Path(path).open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            count+=1
            b=[D(row['b'+str(j)]) for j in range(5)]
            x=[D(row['x'+str(j)]) for j in range(5)]
            terms=[b[j]*x[j] for j in range(5)]
            z=D(row['intercept'])+sum(terms,D(0))
            # Stable decimal logistic expression
            if z>=0:
                q=(-z).exp(); p=1/(1+q)
            else:
                q=z.exp(); p=q/(1+q)
            err=abs(p-D(row['pd']))
            max_abs=max(max_abs,err)
            if err>D('1e-12') or abs(z-D(row['eta']))>D('1e-12') or terms.index(max(terms))!=int(row['dominant_logodds_feature']):
                violations.append(row.get('case_id','?'))
    report={'rows_checked':count,'decimal_precision':80,'max_absolute_pd_difference':str(max_abs),'failures':len(violations),'status':'PASS' if count and not violations else 'FAIL','interpretation':'numeric arithmetic agreement on exported synthetic inputs only'}
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv_file');a=p.parse_args();sys.exit(run(a.csv_file))
