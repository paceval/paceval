#!/usr/bin/env python3
"""80-digit independently implemented audit for deterministic released synthetic records."""
import csv,json
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'examples/quality_records.csv').open()))
registry={int(r['score_id']):r for r in csv.DictReader((root/'examples/score_registry.csv').open())}
worst=mp.mpf(0);count=0
for row in rows[::20]:
 rule=registry[int(row['score_id'])];a,b,c=[mp.mpf(rule[k]) for k in ('coefficient_a','coefficient_b','coefficient_c')]
 t,p,s,v,w=[mp.mpf(row[k]) for k in ('temperature_dev','pressure_dev','speed_dev','vibration_dev','wear_dev')]
 family=int(rule['family']);D=mp.mpf
 if family==1:z=a*t+b*p+c*s+D('0.35')*v+D('0.25')*w
 elif family==2:z=a*t*t+b*p*p+c*s*s+D('0.30')*v-D('0.70')
 elif family==3:z=a*t*p+b*s*v+c*w+D('0.12')*t*t-D('0.15')
 elif family==4:z=a*mp.sin(t)+b*mp.cos(p)+c*s*w+D('0.30')*v
 else:z=a*mp.log(1+t*t)+b*mp.sqrt(1+p*p)+c*v*w+D('0.15')*s-D('0.45')
 ref=1/(1+mp.exp(-z)); got=D(row['score']);error=abs(ref-got);worst=max(error,worst)
 assert error < D('0.00000000005'), (row['record_id'],str(error))
 assert (got>=D('0.60')) == bool(int(row['inspect_flag']))
 count+=1
output={'status':'PASS','precision_digits':80,'checks':count,'max_absolute_error_internal':str(worst),'reference':'independently implemented mpmath formulas; input strings from exported CSV'}
(root/'results/decimal_audit.json').write_text(json.dumps(output,indent=2)+'\n')
print('PASS',count,'independent high-precision quality-score checks')
