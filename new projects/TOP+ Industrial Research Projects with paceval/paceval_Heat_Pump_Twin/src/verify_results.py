#!/usr/bin/env python3
"""Read recorded SDK outputs, check shape, physics/accounting and inventory consistency."""
from pathlib import Path
import csv,json,math
root=Path(__file__).resolve().parent.parent
read=lambda n:list(csv.DictReader((root/'examples'/n).open()))
a=read('operating_candidates.csv');s=read('performance_surface.csv');t=read('seven_day_replay.csv');v=read('versioned_model_sweep.csv');r=read('formula_registry.csv');i=read('../results/math_execution_inventory.csv')
assert len(a)==6000 and len(s)==3721 and len(t)==168 and len(v)==101 and len(r)==23
assert len(i)==26 and sum(row['execution_owner']=='paceval' for row in i)==23
for row in a:
 f=lambda k:float(row[k]);h=f('delivered_heat_kw');p=f('total_electric_kw')
 assert math.isfinite(h) and h>0 and p>0
 assert abs(f('system_cop_v1')-h/p)<1e-9
 assert abs(f('source_extracted_heat_kw')-(h-f('compressor_electric_kw')))<1e-9
 assert abs(f('delivered_heat_kwh')-h*f('hours'))<1e-9
 passed=int(f('heat_demand_margin_kw')>=0 and f('electric_limit_margin_kw')>=0 and f('cop_limit_margin')>=0)
 assert int(row['screen_pass'])==passed
 assert f('synthetic_defrost_modifier')>0 and f('effective_cop_v1')>0
heat=sum(float(x['heat_kwh']) for x in t)
electric=sum(float(x['electric_kw']) for x in t)
assert heat>electric>0
assert max(float(x['system_cop']) for x in t)<10
summary={'status':'PASS','candidate_rows':len(a),'surface_rows':len(s),'seven_day_rows':len(t),'version_points':len(v),
         'paceval_graphs':len(r),'execution_inventory_rows':len(i),'heat_energy_kwh':heat,'electric_energy_kwh':electric,'energy_ratio':heat/electric}
(root/'results'/'scientific_consistency_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print('PASS: scientific consistency, 6000 records, surface, replay, inventory')
