#!/usr/bin/env python3
"""Merge independent CTest/audit evidence into the machine-generated main-run manifest."""
from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[1];r=root/'results'
p=r/'execution_evidence.json';e=json.loads(p.read_text())
tests=(r/'ctest_report.txt').read_text()
m=re.search(r'(\d+)% tests passed, (\d+) tests failed out of (\d+)',tests)
if not m or m.group(1)!='100' or m.group(2)!='0':raise RuntimeError('No 100% passing CTest report')
a=json.loads((r/'scientific_audit.json').read_text())
if a.get('high_precision_check_status')!='PASS':raise RuntimeError('High precision audit not successful')
e['ctest_passed']=int(m.group(3));e['ctest_total']=int(m.group(3))
e['high_precision_checked_rows']=int(a['high_precision_endvalue_rows'])
e['high_precision_checks']=int(a['high_precision_checks'])
e['scientific_figures']=10
e['source_wp']='WP07 Advanced Chip Packaging Warpage and Cure Stress Screening'
e['run_evidence_semantics']='domain graphs exclude batch-layout/operator probes; scalar and batch calls are API invocations, and batch graph-point evaluations count formula x input-point combinations, not unique scenarios'
p.write_text(json.dumps(e,indent=2)+'\n',encoding='utf-8')
print('Evidence finalized:',e['ctest_passed'],'CTests,',e['high_precision_checks'],'independent precision checks')
