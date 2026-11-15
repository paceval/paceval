#!/usr/bin/env python3
"""Deterministic synthetic (not observed) asset and liability EUR payments."""
from pathlib import Path
import random,csv,io,sys,hashlib
SEED=20261115

def generate():
 rng=random.Random(SEED)
 maturities=[.25,.5,.75,1.,1.5,2.,3.,4.,5.,7.,10.,12.,15.,18.,22.,25.,30.]
 scenarios=[('BASE',0,0,0),('PARALLEL_UP',.02,0,0),('PARALLEL_DOWN',-.02,0,0),('STEEPENER',0,-.016,.019),('FLATTENER',0,.024,-.014),('SHORT_UP',0,.03,0),('SHORT_DOWN',0,-.03,0),('MIXED',.003,-.020,.012)]
 flows=[]
 for i in range(1024):
  side='ASSET' if i<512 else 'LIABILITY';t=max(.05,rng.choice(maturities)+(rng.random()-.5)*.04)
  if side=='ASSET':t*=.86;amount=rng.uniform(.4,1.9)
  else:t*=1.18;amount=rng.uniform(.45,1.85)
  flows.append((f'CF{i+1:05d}',side,t,amount))
 out=io.StringIO(newline='');w=csv.writer(out,lineterminator='\n');w.writerow(['scenario','cashflow_id','side','t_year','amount_eur_m','rlevel','rslope','rhump','tau','parallel','shortshock','longshock'])
 for scenario,par,short,long in scenarios:
  for ident,side,t,amount in flows:w.writerow([scenario,ident,side,f'{t:.15g}',f'{amount:.15g}','0.017','0.012','0.004','6.0',f'{par:.15g}',f'{short:.15g}',f'{long:.15g}'])
 return out.getvalue()
if __name__=='__main__':
 target=Path(__file__).resolve().parents[1]/'input/cashflows_scenarios.csv';s=generate()
 if '--check' in sys.argv:
  assert target.read_text(encoding='utf8')==s,'Synthetic generator reproduction failed'
  print('PASS deterministic input reproduction, SHA256',hashlib.sha256(s.encode()).hexdigest())
 else:target.write_text(s,encoding='utf8')
