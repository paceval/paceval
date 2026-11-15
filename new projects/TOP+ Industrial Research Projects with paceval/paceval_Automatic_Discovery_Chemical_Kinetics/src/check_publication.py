#!/usr/bin/env python3
"""Verify publication PDF, all numerical research figures and GitHub structure."""
from pathlib import Path
import fitz
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'figures'
P=ROOT/'paceval_Automatic_Discovery_Chemical_Kinetics_Whitepaper_EN.pdf'
assert P.is_file() and P.stat().st_size>200_000
pdf=fitz.open(P);assert len(pdf)==14,('unexpected page count',len(pdf))
text=' '.join(x.get_text() for x in pdf)
for mandatory in ['Automatic Discovery','Executive summary','Scientific references','1,000','paceval','independent','synthetic']:
 assert mandatory.lower() in text.lower(),mandatory
for i,p in enumerate(pdf):
 assert p.rect.width>500 and p.rect.height>800
 assert p.get_text().strip(),('empty PDF page',i)
hero=Image.open(F/'00_chemical_kinetics_hero.png');assert hero.size==(2400,1200)
for i in range(1,14):
 files=list(F.glob(f'{i:02}_*.png'));assert len(files)==1,(i,files)
 assert files[0].with_suffix('.pdf').is_file()
 assert Image.open(files[0]).width>=500
for p in [ROOT/'README.md',ROOT/'docs/SCIENTIFIC_SCOPE.md',ROOT/'docs/REPRODUCIBILITY.md',ROOT/'docs/original_WP27_proposal.pdf']:
 assert p.is_file(),p
assert not any(ROOT.rglob('*.so'))
print('PUBLICATION PASSED',len(pdf),'PDF pages,',13,'data / architecture graphics, high-resolution hero')
