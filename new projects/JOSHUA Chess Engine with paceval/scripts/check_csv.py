#!/usr/bin/env python3
"""Independent numeric schema and exact integer-formula reference for real CSV path."""
import csv,sys
from decimal import Decimal,getcontext
getcontext().prec=90
with open(sys.argv[1]) as f:a=list(csv.DictReader(f))
with open(sys.argv[2]) as f:b=list(csv.DictReader(f))
assert len(a)==len(b) and len(a)>0
for r,z in zip(a,b):
 assert r['id']==z['id'];v=lambda k:Decimal(r[k])
 mat=100*(v('wp')-v('bp'))+320*(v('wn')-v('bn'))+330*(v('wb')-v('bb'))+500*(v('wr')-v('br'))+900*(v('wq')-v('bq'))
 second=mat+13*(v('wc')-v('bc'))+17*(v('wd')-v('bd'))+3*(v('wa')-v('ba'))+18*(v('wk')-v('bk'))
 for k,x in [('score_v1',mat),('score_v2',second),('center_margin_v2',v('wc')-v('bc')),('score_guard_v2',int(abs(second)<=2000))]:assert abs(Decimal(z[k])-Decimal(x))<Decimal('0.000001'),(k,r['id'])
print('CSV_REFERENCE_PASS',len(a),'rows',len(a)*4,'cross-checks')
