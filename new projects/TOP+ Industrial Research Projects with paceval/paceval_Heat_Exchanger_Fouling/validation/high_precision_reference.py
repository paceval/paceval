#!/usr/bin/env python3
"""Independent 90-digit mpmath check of selected actual paceval MCP 4.26 observations.
This script does not call the paceval engine and cannot validate an unrun local SDK build.
"""
import csv,sys,math
from pathlib import Path
import mpmath as mp
mp.mp.dps=90
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
with (root/'examples/synthetic_corner_scenarios.csv').open() as f: inp={r['case_id']:r for r in csv.DictReader(f)}
with (root/'results/mcp_selected_observations.csv').open() as f: obs=list(csv.DictReader(f))
# mp.mpf(float(...)) intentionally represents the exact binary64 inputs to the remote engine.
f=lambda x:mp.mpf(float(x))
def evaluate(v):
 Th,Tc,Ch,Cc,Uc,A,Rf=map(lambda k:f(v[k]),['Th','Tc','Ch','Cc','Uc','A','Rf'])
 cm=min(Ch,Cc);cx=max(Ch,Cc);cr=cm/cx
 def Q(r):
  n=A/(1/Uc+r)/cm
  e= n/(1+n) if Ch==Cc else (1-mp.exp(-n*(1-cr)))/(1-cr*mp.exp(-n*(1-cr)))
  return cm*(Th-Tc)*e
 q=Q(Rf); qclean=Q(f(v['Rremain']))
 L=(f(v['D1'])-f(v['D2']))/mp.log(f(v['D1'])/f(v['D2']))
 q_lmtd=A/(1/Uc+Rf)*f(v['Fc'])*L
 def penalty(x):return f(v['Price'])*f(v['H'])*max(mp.mpf('0'),f(v['Qtarget'])-x)/1000
 advantage=penalty(q)-(f(v['Cclean'])+penalty(qclean))
 hot=Th-q/Ch;cold=Tc+q/Cc;pinch=min(Th-cold,hot-Tc)
 guard=int(q>=f(v['Qtarget']) and pinch>=f(v['Approach']) and f(v['DeltaP'])<=f(v['DeltaPmax']))
 cleaner=int(advantage>0 and Rf>f(v['Rremain']))
 return q,q_lmtd,advantage,guard,cleaner
checks=0
for o in obs:
 q,l,a,g,c=evaluate(inp[o['case_id']]);
 for field,ref in [('Q_NTU_v2_W',q),('Q_LMTD_v1_W',l),('cleaning_advantage_EUR',a)]:
  value=mp.mpf(o[field]); err=abs(value-ref)/max(mp.mpf('1'),abs(ref))
  assert err<mp.mpf('2e-11'),(o['case_id'],field,err)
  checks+=1
 assert int(o['operation_guard'])==g and int(o['cleaning_guard'])==c
print('PASS',len(obs),'remote scenarios,',checks,'independent high-precision numeric checks, plus 98 exact flags')
