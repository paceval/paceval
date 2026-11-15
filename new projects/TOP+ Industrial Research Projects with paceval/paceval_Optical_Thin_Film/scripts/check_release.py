#!/usr/bin/env python3
"""Strict release-scoped data and publication preflight."""
from pathlib import Path
import json,csv,sys
from PIL import Image
import fitz
p=Path(__file__).resolve().parents[1]
e=json.loads((p/'results'/'execution_evidence.json').read_text())
a=json.loads((p/'results'/'high_precision_audit.json').read_text())
b=json.loads((p/'results'/'inverse_reference_audit.json').read_text())
assert e['unique_graphs_created']==e['unique_graphs_executed']==33
assert e['site_count']==144 and e['spectral_sample_rows']==1296
assert a['pass'] and b['pass']
assert len(list(csv.DictReader((p/'results'/'site_summary.csv').open())))==e['site_count']
for k in ['spectral_samples.csv','objective_profiles.csv','alias_case.csv','alias_curve.csv','model_comparison.csv','native_audit.csv','formula_manifest.csv','math_execution_inventory.csv']:
 assert (p/'results'/k).stat().st_size>50,k
for i in range(1,11):
 files=list((p/'figures').glob(f'fig{i:02d}_*.png'))
 assert len(files)==1 and files[0].with_suffix('.pdf').is_file()
assert Image.open(p/'figures'/'00_optical_thin_film_cover.png').size==(2400,1200)
with fitz.open(p/'paceval_Optical_Thin_Film_Whitepaper_EN.pdf') as paper:
 assert len(paper)==15
 for n,page in enumerate(paper):
  for w in page.get_text('words'):
   assert w[0]>=-1 and w[2]<=page.rect.width+1 and w[1]>=-1 and w[3]<=page.rect.height+1,(n,w)
assert not list(p.rglob('libpaceval*.so'))
print('RELEASE CHECK PASS 15 PDF pages, 10 executed-data figures, all evidence artifacts, no external runtime')
