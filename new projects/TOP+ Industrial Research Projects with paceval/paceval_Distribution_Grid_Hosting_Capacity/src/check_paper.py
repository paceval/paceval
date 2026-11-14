#!/usr/bin/env python3
"""Check published A4 PDF, rendered page integrity and cover artwork proportions."""
from pathlib import Path
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[1]
pdf=R/'paceval_Distribution_Grid_Hosting_Capacity_Whitepaper_EN.pdf'
assert pdf.is_file()
image=Image.open(R/'figures'/'00_grid_hosting_hero.png')
assert image.size==(2400,1200)
doc=fitz.open(pdf)
assert len(doc)==14,len(doc)
for number,page in enumerate(doc,1):
 rect=page.rect
 assert abs(rect.width-595.276)<1 and abs(rect.height-841.89)<1
 text=page.get_text()
 assert len(text)>200,(number,len(text))
 for b in page.get_text('blocks'):
  if b[6]!=0:continue
  x0,y0,x1,y1=b[:4]
  assert x0>=-1 and y0>=-1 and x1<=rect.width+1 and y1<=rect.height+1,(number,b[:4])
 pix=page.get_pixmap(matrix=fitz.Matrix(.6,.6),alpha=False)
 assert pix.width>300 and pix.height>450
text=''.join(p.get_text() for p in doc)
for phrase in ['1. Industrial use case','13. Scientific limitations','research','hosting','5. Deterministic','29']:
 assert phrase.lower() in text.lower(),phrase
print('A4_PDF_14_PAGES_RENDER_VERIFIED',len(doc))
