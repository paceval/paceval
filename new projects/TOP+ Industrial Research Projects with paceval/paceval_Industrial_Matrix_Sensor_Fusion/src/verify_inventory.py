#!/usr/bin/env python3
import csv,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
r=root/'results';registry=list(csv.DictReader((r/'graph_registry.csv').open()))
inventory=list(csv.DictReader((r/'math_execution_inventory.csv').open()))
assert len(registry)>=16
for item in registry:
    assert int(item['actual_graph_outputs'])>0,item['graph_id']
    assert int(item['actual_api_calls'])>0,item['graph_id']
    assert any(it['function_id']==item['graph_id'] and it['execution_owner']=='paceval' for it in inventory)
assert any(it['execution_owner']=='C++ host' for it in inventory)
assert any(it['execution_owner']=='C++ reference' for it in inventory)
print(f'PASS {len(registry)} registered, genuinely evaluated paceval graphs, host roles documented')
