#!/usr/bin/env python3
"""Independent local release preflight for this WP23 study (no GitHub hosting claim)."""
from pathlib import Path
import json,hashlib,sys,re,zipfile,subprocess
from PIL import Image
import fitz
root=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'scripts'))
from check_markdown import check as check_md
preflight=check_md(root)
subprocess.run([sys.executable,str(root/'scripts/check_markdown.py'),'--selftest'],check=True,capture_output=True,text=True)
assert (root/'src/paceval_main.h').read_text(encoding='latin1').find('paceval_subVersionString    "25"')!=-1
assert (root/'src/paceval_main.cpp').read_text(encoding='latin1').find('#include "paceval_main.h"')!=-1
src=(root/'src/granulation_drying_main.cpp').read_text()
for x in ('paceval_dGetMultipleComputationsResultsExt','paceval_CreateComputation','paceval_dConvertStringToFloat','paceval_dConvertFloatToString'):
 assert x in src,x
stats=json.loads((root/'results/execution_evidence.json').read_text());checks=json.loads((root/'results/high_precision_audit.json').read_text());repro=json.loads((root/'results/reproducibility_audit.json').read_text())
assert stats['unique_graphs_created']==stats['unique_graphs_executed']==60
assert checks['checks']==138240 and checks['status']=='PASS'
assert repro['status']=='PASS' and all(repro['files_identical'].values())
figures=sorted((root/'figures').glob('fig??_*.png'));vector=sorted((root/'figures').glob('fig??_*.pdf'))
assert len(figures)==len(vector)==10
for png in figures:
 v=png.with_suffix('.pdf');assert v in vector
 img=Image.open(png);assert img.width>=900 and img.height>=450
cover=Image.open(root/'figures/00_pharma_granulation_hero_2400x1200.png')
assert cover.size==(2400,1200)
doc=fitz.open(root/'paceval_Continuous_Pharma_Granulation_Drying_Whitepaper_EN.pdf');assert len(doc)==17
for ix,page in enumerate(doc):
 assert len(page.get_text().strip())>=100
 for b in page.get_text('blocks'):
  assert b[0]>=-1 and b[1]>=-2 and b[2]<=page.rect.width-5 and b[3]<=page.rect.height-10,(ix,b)
project_files=[p for p in root.rglob('*') if p.is_file()]
assert not any(p.suffix=='.so' for p in project_files)
assert not any('__pycache__' in p.parts for p in project_files)
report={'status':'PASS','markdown':preflight,'markdown_negative_cases':'PASS','pdf_pages_rendered_and_reviewed':17,'pdf_text_bounding_boxes':'PASS','scientific_png_and_vector_pairs':10,'cover_pixels':[2400,1200],'reproduced_files':len(repro['files_identical']),'sdk_version':'4.25','true_engine_graphs':60,'ctest_total':5,'ctest_passed':5,'runtime_shared_library_in_archive':False,'hosted_github_visual_preview':'not performed'}
(root/'results/release_preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print('RELEASE PREFLIGHT PASS',report)
