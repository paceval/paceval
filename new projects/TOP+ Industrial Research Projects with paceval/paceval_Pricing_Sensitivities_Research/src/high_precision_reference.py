#!/usr/bin/env python3
"""Independent mpmath 80-digit reference for selected exported BSM results.
This script DOES NOT call the C++ or paceval implementations. It recomputes
normal CDF via mpmath.erf and analytical prices/Greeks from original inputs.
"""
import csv, json, sys
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
N=lambda z: (1+mp.erf(z/mp.sqrt(2)))/2
P=lambda z: mp.exp(-z*z/2)/mp.sqrt(2*mp.pi)
NAMES=['call_price','put_price','call_delta','put_delta','gamma','vega','call_theta','put_theta','call_rho','put_rho']
def oracle(x):
    S,K,T,r,q,v=(mp.mpf(x[k]) for k in ('S','K','T','r','q','sigma'))
    d1=(mp.log(S/K)+(r-q+v*v/2)*T)/(v*mp.sqrt(T));d2=d1-v*mp.sqrt(T)
    n1,n2,nm1,nm2=N(d1),N(d2),N(-d1),N(-d2)
    dc=mp.exp(-q*T); dr=mp.exp(-r*T)
    g=dc*P(d1)/(S*v*mp.sqrt(T));veg=S*dc*P(d1)*mp.sqrt(T)
    first=-S*dc*P(d1)*v/(2*mp.sqrt(T))
    return [S*dc*n1-K*dr*n2,K*dr*nm2-S*dc*nm1,dc*n1,-dc*nm1,g,veg,
            first-r*K*dr*n2+q*S*dc*n1,first+r*K*dr*nm2-q*S*dc*nm1,K*T*dr*n2,-K*T*dr*nm2]
def main(root):
    root=Path(root); rows=list(csv.DictReader((root/'examples/pricing_grid.csv').open()))
    # Stratified selection includes all four corners, center and 99 other cases.
    idx=sorted(set([0,40,60,1200,1240,1250,2460,2500]+list(range(0,len(rows),25))))
    max_abs=mp.mpf(0);worst='';checks=0
    for i in idx:
        row=rows[i];ref=oracle(row)
        for key,value in zip(NAMES,ref):
            observed=mp.mpf(row[key]);diff=abs(observed-value)
            if diff>max_abs:max_abs=diff;worst=f'case={i}, output={key}'
            if diff>mp.mpf('1e-9')*(1+abs(value)):
                raise SystemExit(f'FAIL {worst}: {diff}')
            checks+=1
    result={'precision_decimal_digits':80,'selected_cases':len(idx),'comparisons':checks,'tolerance':'1e-9 * (1 + abs(reference))',
            'maximum_absolute_difference':mp.nstr(max_abs,18),'worst_case':worst,'status':'PASS',
            'note':'Precision compares exported decimal strings against independently evaluated mp.mpf formulas; no binary-exact enclosure assertion.'}
    (root/'results/decimal_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)
if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
