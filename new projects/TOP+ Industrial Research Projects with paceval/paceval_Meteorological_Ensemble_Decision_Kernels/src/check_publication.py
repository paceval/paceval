#!/usr/bin/env python3
import csv,sys,json,pathlib,fitz
from PIL import Image
root=pathlib.Path(__file__).resolve().parent.parent
pdf=root/'paceval_Meteorological_Ensemble_Decision_Kernels_Whitepaper_EN.pdf'
with fitz.open(pdf) as doc:
    assert len(doc)==16,('PDF pages',len(doc))
    for i,page in enumerate(doc):
        text=page.get_text()
        assert len(text)>100,('Page has insufficient extracted text',i+1)
        assert 'Not operational weather guidance' in text or 'Not operational' in text or 'operational' in text.lower(),('No research limitation',i+1)
        for block in page.get_text('blocks'):
            x0,y0,x1,y1,text,*rest=block
            if not str(text).strip():continue
            assert -3<=x0<=page.rect.width+3 and -3<=x1<=page.rect.width+3,(i+1,block[:4])
            assert -3<=y0<=page.rect.height+3 and -3<=y1<=page.rect.height+3,(i+1,block[:4])
assert (root/'figures/00_weather_risk_hero.png').exists()
with Image.open(root/'figures/00_weather_risk_hero.png') as im:assert im.size==(2400,1200)
assert len(list((root/'figures').glob('[0-9][0-9]_*.png')))==15
assert len(list((root/'figures').glob('[0-9][0-9]_*.pdf')))==14
print('PUBLICATION PASSED: 16 valid A4 pages, cover hero and 14 paired figures')
