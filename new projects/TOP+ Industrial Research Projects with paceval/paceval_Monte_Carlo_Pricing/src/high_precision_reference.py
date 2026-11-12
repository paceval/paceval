#!/usr/bin/env python3
"""Independent high-precision audit of published payoff and TINC samples.

Uses mpmath instead of C++/paceval for arithmetic. The input values are parsed
as IEEE-754 doubles first, then promoted exactly to mpf values, matching the
actual floating-point values that the engine received, not abstract decimal
numbers represented by CSV text. TINC inclusion is tested strictly; failures
are reported, never silently reclassified as passes.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from mpmath import mp

mp.dps = 100

def exact_number(string):
    x = float(string)
    if not math.isfinite(x):
        raise ValueError('Nonfinite input in audit')
    return mp.mpf(x)

def intrinsic(family, vals):
    st, av, maximum, k, cap, r, maturity = vals
    pos = lambda v: max(v, mp.zero)
    discount = mp.exp(-r * maturity)
    if family == 'european_call': return pos(st-k) * discount
    if family == 'european_put': return pos(k-st) * discount
    if family == 'capped_call': return (pos(st-k)-pos(st-k-cap)) * discount
    if family == 'asian_call': return pos(av-k) * discount
    if family == 'lookback_call': return pos(maximum-k) * discount
    if family == 'discounted_terminal': return st*discount
    raise ValueError('Unexpected payoff family: '+family)

def verify(root):
    root = Path(root)
    payoff = list(csv.DictReader((root/'payoff_audit.csv').open(newline='')))
    tinc = list(csv.DictReader((root/'tinc_samples.csv').open(newline='')))
    largest = 0.0; violations = 0
    for row in payoff:
        vals = [exact_number(row[k]) for k in ['terminal_price','arithmetic_average','observed_maximum','strike','cap','rate','time']]
        ref = intrinsic(row['family'], vals)
        reported = exact_number(row['paceval_payoff'])
        diff = float(abs(ref-reported)); largest=max(largest,diff)
        if diff>2e-11*(1+float(abs(ref))): violations+=1
    if not payoff or len(tinc)!=24:
        raise ValueError('Expected nonempty payoff samples and exactly 24 TINC samples')
    contain=0; tdiff=0.0; missed=[]
    for row in tinc:
        vals=[exact_number(row[k]) for k in ['st','av','mx','k','cap','r','t']]
        ref=intrinsic(row['family'], vals)
        lo=exact_number(row['lower']); hi=exact_number(row['upper'])
        if lo<=ref<=hi:contain+=1
        else:missed.append({'sample':int(row['sample']), 'reference':mp.nstr(ref,30), 'lower':row['lower'], 'upper':row['upper']})
        tdiff=max(tdiff,float(abs(exact_number(row['value'])-ref)))
    # Independent analytical Black-Scholes formula, checked against the
    # stored C++ analytic reference (not used to fit the Monte Carlo model).
    prices=list(csv.DictReader((root/'prices.csv').open(newline='')))
    analytic_checks=0; analytic_failures=0; max_analytic_ref_error=0.0
    s0=mp.mpf(100); rate=mp.mpf(float(0.03)); maturity=mp.mpf(1); sigma=mp.mpf(float(0.2))
    cdf=lambda z: mp.erfc(-z/mp.sqrt(2))/2
    for row in prices:
        if row['analytic_price']=='NA':continue
        k=exact_number(row['strike']);d1=(mp.log(s0/k)+(rate+sigma*sigma/2)*maturity)/(sigma*mp.sqrt(maturity));d2=d1-sigma*mp.sqrt(maturity)
        if row['family']=='european_call':ref=s0*cdf(d1)-k*mp.exp(-rate*maturity)*cdf(d2)
        elif row['family']=='european_put':ref=k*mp.exp(-rate*maturity)*cdf(-d2)-s0*cdf(-d1)
        else:raise ValueError('Unexpected analytic family')
        err=float(abs(ref-exact_number(row['analytic_price'])))
        analytic_checks+=1;max_analytic_ref_error=max(err,max_analytic_ref_error)
        if err>2e-12:analytic_failures+=1
    # GBM antithetic pairs obey an exact terminal identity independently of Z:
    # S_T(+Z) * S_T(-Z) = S0^2 * exp(2 * (r - sigma^2/2) * T).
    paths=list(csv.DictReader((root/'path_samples.csv').open(newline='')))
    identity=s0*s0*mp.exp(2*(rate-sigma*sigma/2)*maturity)
    antithetic_checks=0;antithetic_failures=0
    for i in range(0,len(paths)-1,2):
        prod=exact_number(paths[i]['terminal_price'])*exact_number(paths[i+1]['terminal_price'])
        antithetic_checks+=1
        if abs(prod-identity)>mp.mpf('1e-8'):antithetic_failures+=1
    result={'method':'independent 100-decimal mpmath, binary64 input values','payoff_checks':len(payoff),
            'payoff_violations':violations,'max_payoff_abs_error':largest,'tinc_checks':len(tinc),
            'tinc_enclosures':contain,'tinc_non_enclosures':missed,
            'max_tinc_point_abs_error':tdiff,
            'analytic_checks':analytic_checks,'analytic_failures':analytic_failures,
            'max_analytic_reference_abs_error':max_analytic_ref_error,
            'antithetic_pair_checks':antithetic_checks,'antithetic_pair_failures':antithetic_failures}
    (root/'high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if violations or missed or analytic_failures or antithetic_failures:raise SystemExit(1)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('root',nargs='?',default='examples')
    verify(p.parse_args().root)
