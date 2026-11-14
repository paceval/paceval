#!/usr/bin/env python3
"""Publication integrity: PDF, all figure pairs, cover dimensions and text-layer checks."""
from pathlib import Path
from PIL import Image
import fitz
R=Path(__file__).resolve().parent.parent
hero=R/'figures/00_distillation_hero.png'
with Image.open(hero) as im:
 assert im.size == (2400,1200),f'Unexpected hero size {im.size}'
 assert im.mode in ('RGB','RGBA')
figs=sorted((R/'figures').glob('[0-9][0-9]_*.png'))
assert len(figs)==13, f'Expected hero plus twelve figures, found {len(figs)}'
for f in figs[1:]:
 assert f.with_suffix('.pdf').is_file(), f'Missing vector plot {f}'
pdf=R/'paceval_Distillation_VLE_Kernels_Whitepaper_EN.pdf'
with fitz.open(pdf) as doc:
 page_count=len(doc)
 assert page_count>=11 and page_count<=19
 alltext=' '.join(page.get_text() for page in doc)
 for token in ['Distillation Column','Vapor-Liquid','Antoine','reboiler','Scientific limitations','NIST','250,000','73']:
  assert token.lower() in alltext.lower(), f'Missing expected document topic {token}'
 for i,page in enumerate(doc):
  assert len(page.get_text().strip())>60, f'Empty or unselectable page {i+1}'
  assert abs(page.rect.width-595)<3 and abs(page.rect.height-842)<3,'Not A4'
print('PUBLICATION PASS',len(figs),'cover and scientific images; PDF pages',page_count)
