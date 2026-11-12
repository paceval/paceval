#!/usr/bin/env python3
"""Independent 80-decimal-digit reference calculated from released CSV text."""
from pathlib import Path
import csv,json
from mpmath import mp
mp.dps=80
root=Path(__file__).resolve().parents[1]
rules={int(r['rule_id']):r for r in csv.DictReader((root/'examples/rule_registry.csv').open())}
D=mp.mpf
def oracle(r,x):
 a,b=D(r['a']),D(r['b']);w,u,s=x;v1=D('0.0002');v2=D('0.00045');cov=D('0.00012');q=v1*w*w+2*cov*w*u+v2*u*u
 family=int(r['family'])-1
 if family==0:return mp.sqrt(q)*(1+a*s)
 if family==1:return mp.sqrt(q+a*(w*w+u*u)*D('0.00002')*s*s)
 if family==2:return mp.sqrt(v1*w*w+v2*u*u+2*(cov+a*D('0.00002')*s)*w*u)
 if family==3:return mp.sqrt(q)+a*mp.sqrt(w*w+u*u)*mp.sqrt(1+s*s)*D('0.004')
 return mp.sqrt(q)+a*abs(w*u)*s*s*D('0.00015')+b*mp.sqrt(1+s*s)*D('0.002')
records=list(csv.DictReader((root/'examples/risk_replay.csv').open()))
worst=D('0');checked=0
for row in records[:500]:
 x=[D(row[k]) for k in ['w1_eur_m','w2_eur_m','shock']]
 expected=oracle(rules[int(row['rule_id'])],x);got=D(row['risk_eur_m']);err=abs(expected-got)
 assert err<=D('1e-10')*(1+abs(expected)),(row,err)
 worst=max(worst,err);checked+=1
result={'status':'PASS','precision_decimal_digits':80,'tested_rows':checked,'max_abs_deviation_from_exported_decimals':str(worst),'input_interpretation':'exact exported decimal text; not reconstruction of binary64 input'}
(root/'results/high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
