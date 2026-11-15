#!/usr/bin/env python3
"""Release structural and scientific-evidence preflight, not a substitute for tests."""
from pathlib import Path
import json,csv,sys
from check_markdown import check
root=Path(__file__).resolve().parents[1]
r=root/'results'
required=['README.md','RESEARCH_VALIDATION.md','LICENSE_NOTICES.md','src/CMakeLists.txt','src/alm_stress.cpp','src/paceval_main.h','src/paceval_main.cpp','input/cashflows_scenarios.csv','results/execution_evidence.json','results/math_execution_inventory.csv','results/formula_manifest.csv','results/cashflow_valuations.csv','results/scenario_summary.csv','results/maturity_buckets.csv','results/stress_surface.csv','results/high_precision_audit.json','results/invariant_audit.json','paceval_ALM_Interest_Rate_Stress_Whitepaper_EN.pdf']
for v in required:
 assert (root/v).is_file(),f'missing release file: {v}'
assert not list(root.rglob('*.so')),'External shared library accidentally packaged'
e=json.loads((r/'execution_evidence.json').read_text());high=json.loads((r/'high_precision_audit.json').read_text());inv=json.loads((r/'invariant_audit.json').read_text())
assert e['unique_graphs_executed']==e['unique_graphs_created'] and e['unique_graphs_executed']>=25
assert e['scenario_count']==8 and e['cashflow_count']==1024 and e['input_rows']==8192
assert high['status']=='passed' and inv['status']=='passed'
with (r/'math_execution_inventory.csv').open() as f:
 rows=list(csv.DictReader(f))
assert sum(x['execution_owner']=='paceval' and x['status']=='executed' for x in rows)==e['unique_graphs_executed']
assert len(list((root/'figures').glob('fig*_*.png')))==10
assert len(list((root/'figures').glob('fig*_*.pdf')))==10
import fitz
pdf=fitz.open(root/'paceval_ALM_Interest_Rate_Stress_Whitepaper_EN.pdf')
assert len(pdf)>=15
for page in pdf:
 for block in page.get_text('dict')['blocks']:
  if block.get('type')!=0:continue
  for line in block['lines']:
   for span in line['spans']:
    box=span['bbox']
    assert box[0]>=-3 and box[2]<=page.rect.width+3 and box[1]>=-3 and box[3]<=page.rect.height+3,(page.number,span['text'],box)
a=check(root)
print('PASS release preflight',e['unique_graphs_executed'],'original graph paths,',len(pdf),'PDF pages,',a['files_checked'],'Markdown files,',a['local_links_checked'],'local links')
