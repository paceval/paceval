"""Independent 80-decimal-digit spot audit of the C++/paceval CSV outputs.
Not a clinical or signal-extraction validator.
"""
import csv, json, sys
from pathlib import Path
from mpmath import mp
mp.dps=80
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'examples'
rows=list(csv.DictReader((root/'feature_replay.csv').open()))
checked=0;maxerr=mp.mpf('0')
for row in rows[::20][:500]:
    r,d,q,a=[mp.mpf(row[k]) for k in ('r','d','q','a')]
    idx=int(row['rule_id'])-1;family=idx//10;j=idx%10
    A=mp.mpf('0.28')+mp.mpf('0.048')*j+mp.mpf('0.015')*family
    B=mp.mpf('0.16')+mp.mpf('0.032')*j
    if family==0:z=A*r+B*d+mp.mpf('.36')*q+mp.mpf('.12')*a
    elif family==1:z=A*r*d+B*q*a+mp.mpf('.19')*d
    elif family==2:z=A*r*r+B*d*d+mp.mpf('.22')*q*q-mp.mpf('.3')
    elif family==3:z=A*mp.sin(r)+B*mp.cos(q)+mp.mpf('.17')*d*a
    else:z=A*mp.log(1+r*r)+B*mp.exp(-d*d)+mp.mpf('.18')*q*a
    value=1/(1+mp.exp(-z));delta=abs(value-mp.mpf(row['score']))
    maxerr=max(maxerr,delta)
    if delta>mp.mpf('1e-11'):raise AssertionError(f'independent audit failed record {row["record_id"]}: {delta}')
    checked+=1
report={'checks':checked,'passed':True,'maximum_absolute_difference':mp.nstr(maxerr,18),'reference_digits':80,
        'scope':'independently specified synthetic score formulas; no clinical validation'}
(root.parent/'results'/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',report)
