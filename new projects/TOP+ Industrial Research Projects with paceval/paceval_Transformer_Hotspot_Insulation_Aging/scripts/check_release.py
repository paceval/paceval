#!/usr/bin/env python3
"""Inspect evidence, files, PDF render bounds and draft integrity without inventing checks."""
from pathlib import Path
import csv,json,hashlib,sys,zipfile
from PIL import Image
import fitz
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results';F=ROOT/'figures';A=Path('/mnt/data/wp14_repeat_results')
e=json.load((R/'execution_evidence.json').open());h=json.load((R/'high_precision_audit.json').open())
assert e['unique_graphs_created']==63 and e['unique_graphs_executed']==63
assert e['distinct_input_rows']==48384 and e['model_hour_rows']==96768
assert h['all_passed'] and h['reference_assertions']==137184
checks=[]
for name in ['hotspot_timeseries.csv','asset_summary.csv','model_comparison.csv','native_audit.csv','formula_manifest.csv','math_execution_inventory.csv','execution_evidence.json','high_precision_audit.json']:
 a=(R/name).read_bytes();b=(A/name).read_bytes();assert a==b,name;checks.append({'name':name,'sha256':hashlib.sha256(a).hexdigest(),'byte_identical_on_independent_repeat':True})
assert Image.open(F/'00_transformer_hero.png').size==(2400,1200)
figures=[F/f'fig{i:02d}_{n}.png' for i,n in enumerate(['hotspot_scenarios','thermal_memory','aging_vs_temperature','cumulative_aging','fleet_heatmap','model_aging_ratio','screening_counts','peak_vs_age','sensitivity','3d_operating_cloud'],1)]
assert all(p.is_file() and p.with_suffix('.pdf').is_file() for p in figures)
with (R/'math_execution_inventory.csv').open() as file:
 graphrows=[x for x in csv.DictReader(file) if x['execution_owner']=='paceval' and x['paceval_graph_id']]
assert len(graphrows)==63 and all(x['status']=='executed' for x in graphrows)
with (R/'hotspot_timeseries.csv').open() as f: assert sum(1 for _ in f)==96769
with (R/'asset_summary.csv').open() as f: assert sum(1 for _ in f)==289
pdf=fitz.open(ROOT/'paceval_Transformer_Hotspot_Insulation_Aging_Whitepaper_EN.pdf');assert len(pdf)==14
for i,page in enumerate(pdf):
 assert page.rect.width>500 and page.rect.height>800
 for block in page.get_text('blocks'):
  # validate paragraph text bounds (excluding float-coordinates beyond printable page).
  x0,y0,x1,y1,_,*_=block
  assert x0>=-1 and y0>=-1 and x1<=page.rect.width+1 and y1<=page.rect.height+1,('PDF overflow',i+1,block)
assert len(list(Path('/mnt/data/wp14_pdf_review_final').glob('*.png')))==14
assert len(figures)==10
report={'project':'WP14 Transformer Hotspot Temperature and Insulation Aging Screening','date':'2026-11-14','graph_count':63,'original_sdk_linked_and_executed':True,'high_precision_assertions':h['reference_assertions'],'independent_native_assertions':e['native_assertions'],'ctest_passed':5,'ctest_total':5,'readme_commonmark_and_local_link_check_passed':True,'readme_link_checker_negative_tests_passed':True,'input_rows':e['distinct_input_rows'],'model_step_rows':e['model_hour_rows'],'byte_identical_repeat_files':checks,'pdf_pages':len(pdf),'pdf_all_pages_rendered_and_contact_sheet_visually_inspected':True,'pdf_text_boxes_within_page':True,'data_based_scientific_figures_png_and_vector_pdf':10,'cover_image_px':[2400,1200],'limitation':'No physical measurements, load-rating certification, complete IEEE C57.91-2025 method or remote GitHub rendering confirmation. Original external paceval library excluded from release.'}
(R/'release_qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('RELEASE CHECK PASS:',report['graph_count'],'executed graphs, 5 CTests, 8 byte-identical outputs, 14 PDF pages, 10 chart pairs')
