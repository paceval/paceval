"""Independent high-precision decimal audit of released paceval outputs.
The model is reimplemented here, without calling the SDK or the C++ parser.
"""
import csv,json
from decimal import Decimal,getcontext
from pathlib import Path
getcontext().prec=80
ROOT=Path(__file__).resolve().parents[1]
D=lambda v:Decimal(str(v))
rows=list(csv.DictReader(open(ROOT/'examples/offers.csv',newline='')))
rules={int(r['policy_id']):r for r in csv.DictReader(open(ROOT/'examples/policy_registry.csv',newline=''))}
maximum=D(0)
for r in rows[::20]:
 p=rules[int(r['policy_id'])]
 f=int(p['family'])-1;a,b,k=map(D,(p['markup'],p['exposure'],p['discount_weight']))
 c,q,risk,d,l,v=map(D,(r['unit_cost_eur'],r['qty'],r['risk_eur_per_item'],r['discount_fraction'],r['lead_days'],r['volatility']))
 if f==1: exposure=l*l/D(900)
 elif f==2: exposure=(1+v*v).sqrt()
 elif f==4: exposure=(-l/D(30)).exp()
 else: exposure=v
 if f==3: volume=(1+q).ln()/D(1001).ln()
 else: volume=q/(q+100)
 value=c*(1+a)+risk*(1+b*exposure)-c*d*k*volume
 diff=abs(value-D(r['formula_unit_bid_eur']))
 maximum=max(maximum,diff)
 if diff>D('2e-10')*(1+abs(value)):
  raise AssertionError(f"High precision audit mismatch: row {r['request']}: {diff}")
report={'status':'PASS','checked':len(rows[::20]),'decimal_precision':80,'max_absolute_difference_eur':str(maximum),'reference':'independent Python Decimal model'}
(ROOT/'results/high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
