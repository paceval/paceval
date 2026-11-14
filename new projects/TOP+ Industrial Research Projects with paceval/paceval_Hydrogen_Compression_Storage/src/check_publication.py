from pathlib import Path
from PIL import Image
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/'paceval_Hydrogen_Compression_Storage_Whitepaper_EN.pdf'
assert pdf.is_file()
r=PdfReader(str(pdf));assert len(r.pages)==14,f'Expected 14 reviewed A4 pages, got {len(r.pages)}'
for i,p in enumerate(r.pages):
    assert int(p.mediabox.width)==595 and int(p.mediabox.height)==841
    assert p.extract_text().strip(),f'Page {i+1} unexpectedly has no extractable text'
cover=Image.open(ROOT/'figures/00_hydrogen_compression_hero.png')
assert cover.size==(2400,1200)
charts=list((ROOT/'figures').glob('*.png'))
assert len(charts)==14,(len(charts),charts)
readme=(ROOT/'README.md').read_text(encoding='utf-8')
for term in ['intercooling','Hydrogen','Gaseous','Original','real-gas','Synthetic','49','100,000','9,081,056']:
    assert term.lower() in readme.lower(),term
text=' '.join(x.extract_text() for x in r.pages)
for phrase in ['High','polytropic','Original','mathematical','storage','11 | Interpretation','References']:
    assert phrase.lower() in text.lower(),phrase
print('PASS publication, 14/14 extractable A4 pages, 14 images, 2400x1200 marketing cover')
