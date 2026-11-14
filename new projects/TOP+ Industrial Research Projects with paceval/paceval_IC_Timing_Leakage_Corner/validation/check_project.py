#!/usr/bin/env python3
"""Check published artifact structure and traceability without faking an SDK runtime."""
import csv,hashlib,json,pathlib,sys
from PIL import Image
import fitz
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]
def check(cond,msg):
 if not cond:raise RuntimeError(msg)
manifest=json.loads((root/'src/formula_manifest.json').read_text())
audit=json.loads((root/'results/high_precision_audit.json').read_text());ev=json.loads((root/'results/execution_evidence.json').read_text())
check(len(manifest['graphs'])==22,'Graph inventory count');check(audit['status']=='PASS' and audit['regular_graph_point_checks']==1162,'Independent numerical audit failed')
check(audit['tinc_printed_interval_checks']==24 and audit['tinc_printed_interval_inclusions']==24,'TINC pointwise checks')
check(ev['actual_remote_calls']['main_graph_point_evaluations']==2134,'Graph point count')
check(ev['actual_remote_calls']['total_all_remote_graph_point_evaluations']==2179,'Total remote graph point count')
with (root/'results/mcp_corner_grid_recorded_81.csv').open() as f:check(len(list(csv.DictReader(f)))==81,'Grid row count')
with (root/'results/mcp_path_snapshots_recorded_16.csv').open() as f:check(len(list(csv.DictReader(f)))==16,'Snapshot row count')
with (root/'results/mcp_operator_selftest_record.csv').open() as f:
 ops=list(csv.DictReader(f));check(len(ops)==21 and all(x['expected']==x['actual'] for x in ops),'Operator checks')
hero=root/'figures/00_ic_timing_leakage_hero.png'
with Image.open(hero) as im:check(im.size==(2400,1200) and im.mode in ('RGB','RGBA'),'Hero properties')
for j in range(1,11):
 matched=list((root/'figures').glob(f'{j:02d}_*.png'));check(len(matched)==1,f'Figure {j} missing/duplicated')
 check(matched[0].with_suffix('.pdf').exists(),f'Figure {j} vector version missing')
pdf=root/'paceval_IC_Timing_Leakage_Corner_Whitepaper_EN.pdf';p=fitz.open(pdf)
check(len(p)==13,'Expected 13-page PDF')
page0=p[0]
positions=[]
for image in page0.get_images(full=True):positions.extend(page0.get_image_rects(image[0]))
check(len(positions)==1,'Cover image count')
actual_ratio=positions[0].width/positions[0].height
check(abs(actual_ratio-2.0)<0.015,'Cover image ratio distorted')
check(pdf.stat().st_size>500000,'Suspiciously small PDF')
for i,page in enumerate(p):
 txt=page.get_text();check(len(txt)>450,f'Unexpectedly empty page {i+1}')
 rect=page.rect
 for b in page.get_text('blocks'):
  # fitz 'blocks' includes image blocks; their bounds are page-relative.
  if b[0]<-2 or b[1]<-2 or b[2]>rect.width+2 or b[3]>rect.height+2:
   raise RuntimeError(f'Out-of-page graphic/text block page {i+1}: {b[:4]}')
for rel in ['src/paceval_main.h','src/paceval_main.cpp','src/ic_corner_paceval.cpp','src/test_numeric_conversions.cpp','src/test_operator_semantics.cpp','src/CMakeLists.txt','src/check_readme_math.py','results/math_execution_inventory.csv','results/execution_evidence.json','results/high_precision_audit.json','docs/Original_WP08_Research_Proposal.pdf','README.md','RESEARCH_VALIDATION.md']:
 check((root/rel).is_file(),'Missing '+rel)
check(not any(root.rglob('*.so')),'Runtime binary accidentally included')
result={'status':'PASS','pdf_page_count':len(p),'hero_pixel_size':[2400,1200],'hero_embedded_ratio':actual_ratio,
'numbered_figure_pairs':10,'nonempty_pdf_pages_checked':len(p),'readme_check':'Run separately: python src/check_readme_math.py',
'original_local_sdk_binary_test':'NOT EXECUTED','observed_mcp_version':'4.26','ordinary_independent_checks':1162,'tinc_inclusions':24,
'source_kind':'Actually evaluated remote MCP expressions plus independently generated original SDK-ready C++ source'}
(root/'results/project_integrity_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
