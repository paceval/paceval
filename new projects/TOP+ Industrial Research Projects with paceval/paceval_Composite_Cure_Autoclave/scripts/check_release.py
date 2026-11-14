#!/usr/bin/env python3
"""Technical release preflight. All assertions are about actual files, not claims."""
from pathlib import Path
import csv,hashlib,json,os,sys,zipfile
from PIL import Image
import fitz
p=Path(__file__).resolve().parents[1]
files=[p/'README.md',p/'RESEARCH_VALIDATION.md',p/'LICENSE_NOTICES.md',p/'src/CMakeLists.txt',p/'src/composite_cure_main.cpp',p/'src/paceval_main.cpp',p/'src/paceval_main.h',p/'results/math_execution_inventory.csv',p/'results/formula_manifest.csv',p/'results/execution_evidence.json',p/'results/high_precision_audit.json',p/'results/trajectory_audit.json',p/'paceval_Composite_Cure_Autoclave_Whitepaper_EN.pdf',p/'figures/00_composite_cure_hero.png']
assert all(x.is_file() for x in files),'Missing file in publication package'
assert Image.open(p/'figures/00_composite_cure_hero.png').size==(2400,1200)
with fitz.open(p/'paceval_Composite_Cure_Autoclave_Whitepaper_EN.pdf') as f:
 assert len(f)==14, f'Expected 14 PDF pages, got {len(f)}'
 for num,page in enumerate(f,1):
  text=page.get_text()
  assert text.count('PACEVAL.')>=1 and len(text)>200, f'Empty or incomplete PDF page {num}'
  bbox=page.rect
  for word in page.get_text('words'):
   x0,y0,x1,y1=word[:4]
   assert x0>=-1 and y0>=-1 and x1<=bbox.width+1 and y1<=bbox.height+1, f'Clipped PDF text page {num}: {word[4]}'
for n in range(1,11):
 name=next((p/'figures').glob(f'fig{n:02}_*.png'),None)
 assert name is not None and name.with_suffix('.pdf').is_file(),f'Missing PNG/vector figure {n}'
proof=json.loads((p/'results/execution_evidence.json').read_text())
with (p/'results/math_execution_inventory.csv').open(newline='') as f:
 inventory=list(csv.DictReader(f))
with (p/'results/formula_manifest.csv').open(newline='') as f:
 manifest=list(csv.DictReader(f))
assert proof['unique_graphs_created']==proof['unique_graphs_executed']==60
assert len(manifest)==60 and sum(x['status']=='executed' and bool(x['paceval_graph_id']) for x in inventory)==60
with (p/'results/screening.csv').open(newline='') as f:screen=list(csv.DictReader(f))
assert len(screen)==72 and sum(int(x['screening_guard']) for x in screen if x['model']=='V1')==proof['feasible_V1'] and sum(int(x['screening_guard']) for x in screen if x['model']=='V2')==proof['feasible_V2']
assert json.loads((p/'results/high_precision_audit.json').read_text())['status']=='PASS'
assert json.loads((p/'results/trajectory_audit.json').read_text())['status']=='PASS'
assert not any('.so' in x.name for x in p.rglob('*') if x.is_file()),'Do not redistribute original runtime'
print('SOURCE PREFLIGHT PASS',len(list(p.rglob('*.md'))),'Markdown files;',proof['unique_graphs_executed'],'executed graphs;',len(screen),'screened model recipes; 14 rendered PDF pages')
if len(sys.argv)==2 and sys.argv[1]=='--json':
 (p/'results/release_preflight.json').write_text(json.dumps({'status':'PASS','executed_graphs':60,'recipes':36,'versions':2,'scientific_png_and_pdf_figures':10,'pdf_pages':14,'runtime_in_archive':False},indent=2)+'\n')
