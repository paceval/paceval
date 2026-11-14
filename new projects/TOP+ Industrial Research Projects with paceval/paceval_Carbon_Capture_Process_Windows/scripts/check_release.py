#!/usr/bin/env python3
"""Release preflight: archive contents, math, source/results coherence, PDF.
Outside the CTest run so final ZIP can be checked separately.
"""
from pathlib import Path
import json,csv,subprocess,zipfile,sys
from PIL import Image
import fitz
from check_markdown import check as markdown_check
ROOT=Path(__file__).resolve().parents[1]

def audit():
 ev=json.loads((ROOT/'results/execution_evidence.json').read_text());assert ev['unique_graphs_executed']==ev['unique_graphs_created']==56
 with (ROOT/'results/math_execution_inventory.csv').open(newline='') as f:
  inventory=list(csv.DictReader(f));assert sum(1 for x in inventory if x['status']=='executed' and x['paceval_graph_id'])==56
 with (ROOT/'results/screening.csv').open(newline='') as f:
  output=list(csv.DictReader(f));assert len(output)==6144
 markdown=markdown_check(ROOT)
 with Image.open(ROOT/'figures/00_carbon_capture_hero.png') as im:assert im.size==(2400,1200)
 figs=list((ROOT/'figures').glob('fig*.png'));vectors=list((ROOT/'figures').glob('fig*.pdf'));assert len(figs)==len(vectors)==10
 pdf=fitz.open(ROOT/'paceval_Carbon_Capture_Process_Windows_Whitepaper_EN.pdf')
 assert len(pdf)==14
 for i,page in enumerate(pdf):
  txt=page.get_text('text');assert len(txt.strip())>110,f'Blank page {i+1}'
  for b in page.get_text('blocks'):
   x0,y0,x1,y1,*_=b
   assert x0>=-2 and y0>=-2 and x1<=page.rect.width+2 and y1<=page.rect.height+2,f'Overflow on page {i+1}: {b[:4]}'
 with (ROOT/'results/high_precision_audit.json').open() as f:hp=json.load(f)
 assert hp['checks_passed']==8672 and hp['status']=='PASS'
 return {'archive_markdown':markdown,'research_graphs_executed':ev['unique_graphs_executed'],'model_case_rows':len(output),'high_precision_checks':hp['checks_passed'],'pdf_pages':len(pdf),'hero_image_resolution':[2400,1200],'science_png_figures':len(figs),'science_vector_figures':len(vectors),'pdf_text_blocks_inside_page':True,'release_preflight':'PASS'}
if __name__=='__main__':
 obj=audit();(ROOT/'results/release_qa.json').write_text(json.dumps(obj,indent=2)+'\n');print('RELEASE QA PASS',obj)
