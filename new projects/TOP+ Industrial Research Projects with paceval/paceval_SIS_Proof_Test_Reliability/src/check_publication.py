#!/usr/bin/env python3
"""Independent publication structure guard; does not assert a GitHub web preview."""
import json,csv
from pathlib import Path
import fitz
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/'paceval_SIS_Proof_Test_Reliability_Whitepaper_EN.pdf'
assert pdf.is_file() and pdf.stat().st_size>140000
pages=fitz.open(pdf)
assert len(pages)==16,('Whitepaper page count',len(pages))
text='\n'.join(p.get_text() for p in pages)
for item in ['Proof-Test','Safety Instrumented','Independent','Common-cause','IEC 61511','paceval','synthetic','reproducibility','not']:
 assert item.lower() in text.lower(),item
for i,p in enumerate(pages):
 assert p.rect.width>500 and p.rect.height>800,(i,'non-A4 page')
 assert len(p.get_text().strip())>250,(i,'empty or placeholder page')
hero=Image.open(ROOT/'figures/00_sis_proof_test_hero.png')
assert hero.size==(2400,1200)
for i in range(1,14):
 figs=list((ROOT/'figures').glob(f'{i:02d}_*.png'))
 assert len(figs)==1,(i,figs)
 assert figs[0].with_suffix('.pdf').is_file()
 assert Image.open(figs[0]).width>=700
assert (ROOT/'docs/original_WP29_proposal.pdf').is_file()
assert len(list((ROOT/'results').glob('*.csv')))>=7
assert not list(ROOT.rglob('*.so'))
evidence=json.loads((ROOT/'results/execution_evidence.json').read_text())
assert evidence['unique_graphs_executed']==40
assert evidence['scenario_count']==100000
assert evidence['graph_point_evaluations']==4003704
assert evidence['safety_certification'] is False
assert (ROOT/'results/high_precision_audit.json').is_file()
with (ROOT/'results/formula_registry.csv').open(newline='') as f:
    reg=list(csv.DictReader(f));assert len(reg)==40
print('PASS research publication: 16 independently renderable PDF pages, 13 source-data diagrams, 40 executed domain graphs, no external shared runtime')
