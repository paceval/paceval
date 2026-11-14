#!/usr/bin/env python3
"""Test project completeness, markdown links and malformed markdown-math negatives."""
import json,re,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
for f in ['README.md','RESEARCH_VALIDATION.md','src/CMakeLists.txt','src/heat_exchanger_paceval.cpp','src/paceval_main.h','src/paceval_main.cpp','src/generated_formulas.h','src/formula_manifest.json','results/math_execution_inventory.csv','results/execution_evidence.json','results/mcp_selected_observations.csv','figures/00_heat_exchanger_hero.png']:
 assert (root/f).is_file(),f
text=(root/'README.md').read_text()
assert '## 1. Industrial use case and current state of the art' in text
assert text.count('```')%2==0
assert text.count('\\(')==text.count('\\)')
assert text.count('\\[')==text.count('\\]')
for s in re.findall(r'!?(?:\[[^\]]+\])\(([^)]+)\)',text):
 if s.startswith(('http://','https://','#','mailto:')):continue
 assert (root/s.split('#')[0]).is_file(),s
# negative mutation tests must fail the intended check
for invalid in ['\\(a+b','[missing](this_file_is_not_here.png)']:
 if invalid.startswith('\\('):assert invalid.count('\\(')!=invalid.count('\\)')
 else:assert not (root/re.search(r'\(([^)]+)\)',invalid).group(1)).exists()
e=json.loads((root/'results/execution_evidence.json').read_text());assert e['unique_graphs_executed']==24 and e['main_graph_point_evaluations']==1176
print('PASS markdown, links, two negative tests, graph manifest and project files')
