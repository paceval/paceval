#!/usr/bin/env python3
"""Release preflight: no external binaries, exact evidence, GitHub math and local links."""
from pathlib import Path
import sys,json,csv,zipfile,hashlib
from check_markdown import check,selftest
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
checks=check(root);selftest()
files=[p for p in root.rglob('*') if p.is_file()]
assert not any(p.suffix=='.so' for p in files),'External binary runtime must not be bundled'
assert (root/'src/paceval_main.h').is_file() and (root/'src/paceval_main.cpp').is_file()
assert (root/'src/CMakeLists.txt').is_file()
assert len(list((root/'figures').glob('fig??_*.png')))==10
assert len(list((root/'figures').glob('fig??_*.pdf')))==10
j=json.loads((root/'results/execution_evidence.json').read_text());c=json.loads((root/'results/exact_interval_audit.json').read_text());hp=json.loads((root/'results/high_precision_audit.json').read_text())
assert j['unique_graphs_executed']==j['unique_graphs_created']==43
assert c['certificate_count']==2*j['trajectory_pair_count']
assert c['uncertified_case_count']==0
assert hp['independent_checks']>1000
for fn in ('screening.csv','model_comparison.csv','native_audit.csv','math_execution_inventory.csv','formula_manifest.csv','exact_interval_certificates.csv','fine_clearance.csv'):
 assert (root/'results'/fn).is_file(),fn
summary={'status':'PASS','markdown_preflight':checks,'unique_graphs':j['unique_graphs_executed'],'exact_rational_certificates':c['certificate_count'],'high_precision_assertions':hp['independent_checks'],'scientific_figures':10,'total_files':len(files),'external_runtime_included':False}
(root/'results/release_preflight.json').write_text(json.dumps(summary,indent=2)+'\n')
print('RELEASE PREFLIGHT PASS',json.dumps(summary))
