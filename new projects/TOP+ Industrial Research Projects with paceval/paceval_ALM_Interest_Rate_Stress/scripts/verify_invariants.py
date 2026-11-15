#!/usr/bin/env python3
"""Check independent portfolio accounting and model-invariant implications."""
import csv,sys,json
from pathlib import Path
from collections import defaultdict

def read(p):
 with open(p,newline='',encoding='utf8') as f:return list(csv.DictReader(f))

def main(root):
 root=Path(root);s=read(root/'scenario_summary.csv');v=read(root/'cashflow_valuations.csv');b=read(root/'maturity_buckets.csv');c=read(root/'model_comparison.csv')
 refs={(r['model'],r['scenario']):r for r in s};assert len(refs)==16
 checks=0
 for r in s:
  a=float(r['asset_pv_eur_m']);l=float(r['liability_pv_eur_m']);g=float(r['net_gap_eur_m']);assert abs(a-l-g)<2e-8;checks+=1
  assert a>0 and l>0 and float(r['asset_duration_years'])>0 and float(r['liability_duration_years'])>0;checks+=1
  assert int(float(r['loss_guard']))==(float(r['loss_margin_eur_m'])>=0);checks+=1
 for k,r in refs.items():
  if k[0]=='V1' and k[1] in ('STEEPENER','FLATTENER','SHORT_UP','SHORT_DOWN'):
   assert abs(float(r['delta_eve_eur_m']))<1e-9;checks+=1
 # independently recompute PV by scenario, plus all tenor buckets
 agg=defaultdict(lambda:[0.,0.]);bb=defaultdict(lambda:[0.,0.])
 for r in v:
  key=(r['model'],r['scenario']);bucket=float(r['t_year']);bucket=(0 if bucket<1 else 1 if bucket<3 else 2 if bucket<5 else 3 if bucket<10 else 4 if bucket<20 else 5)
  side=0 if r['side']=='ASSET' else 1;pv=float(r['pv_eur_m']);agg[key][side]+=pv;bb[key+(bucket,)][side]+=pv
  assert float(r['discount_factor'])>0 and float(r['rate_margin'])>=0 and float(r['guard'])==1;checks+=1
 for (m,sc),sumval in agg.items():
  a=refs[m,sc];assert abs(float(a['asset_pv_eur_m'])-sumval[0])<1e-7 and abs(float(a['liability_pv_eur_m'])-sumval[1])<1e-7;checks+=2
 for r in b:
  key=(r['model'],r['scenario'],int(r['bucket']));target=bb[key];assert abs(float(r['asset_pv_eur_m'])-target[0])<1e-7 and abs(float(r['liability_pv_eur_m'])-target[1])<1e-7;checks+=2
 assert len(c)==8
 for r in c:
  a=refs['V1',r['scenario']];b=refs['V2',r['scenario']];assert abs(float(r['gap_difference_eur_m'])-(float(b['net_gap_eur_m'])-float(a['net_gap_eur_m'])))<1e-8;checks+=1
 o={'status':'passed','independent_accounting_and_domain_checks':checks,'scenario_versions':len(refs),'input_valuations':len(v),'maturity_bucket_rows':len(b)}
 (root/'invariant_audit.json').write_text(json.dumps(o,indent=2)+'\n')
 print('PASS accounting and curve invariants:',checks,'checks')
if __name__=='__main__':main(sys.argv[1])
