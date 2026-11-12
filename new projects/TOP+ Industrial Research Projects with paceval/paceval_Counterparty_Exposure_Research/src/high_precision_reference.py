#!/usr/bin/env python3
"""Independent high precision audit for the sampled, executed paceval exposure rows."""
import csv, json
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec=80
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'examples/exposure_samples.csv').open()))
D=Decimal
worst=D(0)
for r in rows:
    k=int(r['rule_id'])-1; family=k//10; j=k%10
    a=D('0.05')+D('0.015')*j+D('0.002')*family
    b=D('1.0')+D('0.12')*j
    v,c,h,s,t,f=[D(r[x]) for x in ('mtm_eur_m','collateral_eur_m','haircut','shock','threshold_eur_m','fx')]
    if family==0: z=v-c*(1-h)-t+a*s
    elif family==1: z=v*(1+a*s)-c*(1-h)-t
    elif family==2: z=v+a*s+b*s*s-c*(1-h)-t
    elif family==3: z=v-c*(1-h)*(f+a*s)-t
    else: z=v-c*(1-h)-t
    y=max(z,D(0))
    if family==4:y+=a*(1+s*s).sqrt()*max(v,D(0))
    observed=D(r['exposure_eur_m'])
    delta=abs(observed-y);worst=max(worst,delta)
    if delta>D('5e-10')*(1+abs(y)):raise AssertionError(f"decimal audit failed {r['update']}: {delta}")
result={'status':'PASS','precision_digits':80,'sampled_rows':len(rows),'max_absolute_difference_internal':str(worst),'input_representation':'CSV decimal values, not exact binary64 originals'}
(root/'results/high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
