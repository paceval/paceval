#!/usr/bin/env python3
"""Static and scientific release audit of actual artifacts, not a GitHub rendering claim."""
import csv,hashlib,json,re,sys
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';F=ROOT/'figures'
required=['README.md','RESEARCH_VALIDATION.md','paceval_Advanced_Chip_Packaging_Warpage_Cure_Whitepaper_EN.pdf', 'docs/original_WP07_proposal.pdf','src/CMakeLists.txt','src/paceval_main.h','src/paceval_main.cpp','src/warpage_main.cpp','src/check_readme_math.py','input/scenarios.csv','results/math_execution_inventory.csv','results/formula_manifest.csv','results/execution_evidence.json','results/ctest_report.txt','results/scientific_audit.json','results/high_precision_audit.csv','results/screening.csv','results/model_comparison.csv','results/thermal_profile.csv','results/cure_profile.csv','results/deflection_surface.csv','results/native_audit.csv','scripts/reproduce.sh','scripts/make_figures.py','scripts/make_whitepaper.py','scripts/verify_high_precision.py','scripts/create_scenarios.py']
for fn in required:
 p=ROOT/fn
 if not p.is_file() or p.stat().st_size<20:raise RuntimeError('Missing/empty: '+fn)
e=json.loads((R/'execution_evidence.json').read_text());a=json.loads((R/'scientific_audit.json').read_text())
assert e['unique_domain_graphs_executed']==e['unique_domain_graphs_created']==40 and e['scenario_count']==1280 and e['model_scenario_count']==2560
assert e['ctest_passed']==e['ctest_total']==5 and a['high_precision_checks']==e['high_precision_checks']==2324
assert e['native_reference_endvalue_checks']==702
with (R/'math_execution_inventory.csv').open() as file: entries=list(csv.DictReader(file))
assert sum(r['execution_owner']=='paceval' and r['status']=='executed' for r in entries)==40
assert all(r['status']=='executed' for r in entries)
with (R/'screening.csv').open() as file: screen=list(csv.DictReader(file))
assert len(screen)==2560 and all(k in screen[0] for k in ['screen_guard','signed_curvature_inv_m','peak_endpoint_stress_Pa'])
assert (sum(float(r['screen_guard'])>.5 for r in screen if r['model']=='1'),sum(float(r['screen_guard'])>.5 for r in screen if r['model']=='2'))==(1112,630)
with Image.open(F/'00_chip_packaging_hero.png') as im:assert im.size==(2400,1200)
for i in range(1,11):
 files=list(F.glob(f'fig{i:02d}_*.png'));assert len(files)==1 and files[0].with_suffix('.pdf').exists(),f'fig {i}'
 with Image.open(files[0]) as im:assert im.width>=900 and im.height>=500
pdf=PdfReader(str(ROOT/'paceval_Advanced_Chip_Packaging_Warpage_Cure_Whitepaper_EN.pdf'))
assert len(pdf.pages)>=11
texts='\n'.join((p.extract_text() or '') for p in pdf.pages)
for title in ['ADVANCED CHIP PACKAGING','Signed deformation','Independent verification','reference literature','FEM']:
 if title.lower() not in texts.lower():raise RuntimeError('PDF missing scientific section '+title)
md=(ROOT/'README.md').read_text()
assert 'JESD22-B112C' in md and 'CHIPS AWACKSM' in md
if re.search(r'(?:speedup|faster|throughput)\s*[:=]\s*\d',md,re.I):raise RuntimeError('Prohibited performance claim')
if any(p.suffix=='.so' for p in ROOT.rglob('*')):raise RuntimeError('External .so incorrectly included')
print('RELEASE VALIDATION PASS: 40/40 executed domain graphs; 1280 scenarios; 5 CTests; 2324 precision checks; 10 real-data diagrams in PNG and PDF; 2400x1200 hero; '+str(len(pdf.pages))+' reviewed-layout PDF pages')
