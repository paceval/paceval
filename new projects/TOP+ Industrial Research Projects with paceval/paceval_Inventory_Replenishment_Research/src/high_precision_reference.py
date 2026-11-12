#!/usr/bin/env python3
"""Independent Decimal(80) oracle for released scalar formula samples.

This is a reference for expressions, not a validation of inventory policy quality.
"""
from decimal import Decimal, getcontext
from pathlib import Path
import csv, json, sys
getcontext().prec=80
root=Path(__file__).resolve().parents[1]
D=Decimal
models={}
with (root/'examples'/'policy_registry.csv').open(newline='') as f:
 for row in csv.DictReader(f): models[int(row['policy_id'])]=row
checks=0
maxabs=D(0)
fail=[]
with (root/'examples'/'scenario_samples.csv').open(newline='') as f:
 for row in csv.DictReader(f):
  p=models[int(row['policy_id'])]
  mu=D(row['mean_units_per_day']);sig=D(row['sigma_units_per_day']);lead=D(row['lead_days']);rev=D(row['review_days']); ip=D(row['inventory_position_units']);trend=D(row['trend_units_per_day'])
  z=D(p['z_buffer_factor']);buffer=D(p['buffer_in_days']);trend_scale=D(p['trend_scale'])
  # The C++ constants were authored as binary64 and CSV decimal values are their round-trip representations.
  # Python Decimal therefore compares the released decimal values, not exact binary floating point expression inputs.
  t=mu*(lead+rev)+z*sig*(lead+rev).sqrt()+buffer*mu+trend_scale*trend*lead-ip
  g=mu*lead+z*sig*lead.sqrt()+buffer*mu-ip
  for k,ref in [('target_minus_position_units',t),('trigger_minus_position_units',g)]:
   observed=D(row[k]); delta=abs(observed-ref)
   maxabs=max(maxabs,delta)
   if delta>D('1e-10')*(1+abs(ref)):fail.append((row['policy_id'],row['sku_id'],k,str(delta)))
   checks+=1
report={'precision_decimal_digits':80,'comparisons':checks,'within_tolerance':checks-len(fail),'failed':len(fail),'maximum_absolute_distance_units':str(maxabs),'oracle_input_interpretation':'released CSV decimals (not exact binary64 input replay)','source':'examples/scenario_samples.csv','failed_examples':fail[:10]}
(root/'results').mkdir(exist_ok=True)
(root/'results'/'decimal_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
if fail:sys.exit(1)
