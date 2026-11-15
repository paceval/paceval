#!/usr/bin/env python3
"""Append the shipped optimized-search addendum to regenerated 16-page base whitepaper.
Usage: python scripts/append_optimization_pdf.py BASE_WHITEPAPER.pdf [OUTPUT.pdf]
"""
import sys
from pathlib import Path
from pypdf import PdfReader,PdfWriter
root=Path(__file__).resolve().parents[1]
base=Path(sys.argv[1]) if len(sys.argv)>1 else root/'JOSHUA_Chess_Research_Base_Whitepaper_EN.pdf'
add=root/'docs/JOSHUA_Optimization_Addendum_EN.pdf'
out=Path(sys.argv[2]) if len(sys.argv)>2 else root/'JOSHUA_Chess_Research_Whitepaper_EN.pdf'
assert base!=out,'Use a distinct base document file'
w=PdfWriter()
for pdf in (base,add):
 for page in PdfReader(str(pdf)).pages:w.add_page(page)
with out.open('wb') as f:w.write(f)
print('Appended',add,'to',base,'=>',out,'pages',len(w.pages))
