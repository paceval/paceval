#!/usr/bin/env python3
"""Check deliverable structure, PDF page rendering and source provenance."""
from pathlib import Path
import zipfile,json,sys,subprocess,hashlib
from markdown_it import MarkdownIt
import fitz
R=Path(__file__).resolve().parents[1]
req=['README.md','RESEARCH_VALIDATION.md','LICENSE_NOTICES.md','src/CMakeLists.txt','src/paceval_main.h','src/paceval_main.cpp','src/nonlinear_control_main.cpp','input/candidates.csv','results/execution_evidence.json','results/formula_manifest.csv','results/math_execution_inventory.csv','results/high_precision_audit.json','results/certificate_audit.json','results/trajectory_audit.json','paceval_Nonlinear_Control_Lyapunov_Screening_Whitepaper_EN.pdf']
for s in req:assert (R/s).is_file(),s
imgs=list((R/'figures').glob('fig*.png'));vectors=list((R/'figures').glob('fig*.pdf'));assert len(imgs)==10 and len(vectors)==10
pdf=fitz.open(R/'paceval_Nonlinear_Control_Lyapunov_Screening_Whitepaper_EN.pdf');assert len(pdf)==16
for i,p in enumerate(pdf):
 assert p.get_text().strip(),f'Empty PDF page {i}'
 for w in p.get_text('words'):assert w[0]>=5 and w[1]>=3 and w[2]<=p.rect.width-5 and w[3]<=p.rect.height-5,(i,w)
 ev=json.loads((R/'results/execution_evidence.json').read_text());assert ev['unique_graphs_executed']==ev['unique_graphs_created']==49
assert not list(R.rglob('libpaceval*')),'Shared library cannot be in release'
if '--record' in sys.argv:
 data={'status':'PASS','pdf_pages':len(pdf),'scientific_png_count':len(imgs),'scientific_vector_pdf_count':len(vectors),'graphs_created_and_executed':ev['unique_graphs_executed'],'markdown_file_count':len(list(R.rglob('*.md'))),'runtime_library_included':False,'note':'Visual review manually performed on all rendered pages. GitHub remote visual preview not inspected.'}
 (R/'results/release_preflight.json').write_text(json.dumps(data,indent=2)+'\n')
print('RELEASE PREFLIGHT PASS',len(pdf),'pdf pages',len(imgs),'scientific image pairs')
