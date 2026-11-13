#!/usr/bin/env python3
"""Verify that original executions, figures and public-release references are complete."""
from pathlib import Path
import json,csv,hashlib
from PIL import Image
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
summary=json.loads((root/'results/execution_summary.json').read_text())
validation=json.loads((root/'results/high_precision_validation.json').read_text())
assert summary['paceval_graphs']==31 and summary['batch_graph_outputs']==308791
assert summary['coefficient_surface_points']==3721
assert validation['status']=='passed' and validation['high_precision_values']==1760
with (root/'results/math_execution_inventory.csv').open() as f:inv=list(csv.DictReader(f))
assert sum(r['owner']=='paceval' for r in inv)==31
assert all(r['api']=='paceval_dGetMultipleComputationsResultsExt' for r in inv if r['owner']=='paceval')
assert len(list(csv.DictReader((root/'examples/paceval_coefficient_surface.csv').open())))==3721
assert len(list(csv.DictReader((root/'examples/paceval_operating_sweep.csv').open())))==4800
assert len(list(csv.DictReader((root/'examples/paceval_rotor_time_series.csv').open())))==1440
assert Image.open(root/'figures/00_wind_turbine_hero.png').size==(2400,1200)
for i in range(1,12):
 matches=list((root/'figures').glob(f'{i:02d}_*.png'))
 assert len(matches)==1
 assert matches[0].with_suffix('.pdf').exists(),matches
pdf=root/'paceval_Wind_Turbine_Digital_Twin_Whitepaper_EN.pdf'
assert len(PdfReader(pdf).pages)==15
assert not list(root.rglob('LICENSE_NOTICE.md'))
assert (root/'references/WP_042_Wind_Turbine_Digital_Twin_Coefficient_Functions.pdf').exists()
files=list(root.rglob('*'));source=(root/'src/paceval_main.cpp')
assert source.exists() and (root/'src/paceval_main.h').exists()
report={'status':'passed','project':'WP_042','graphs':31,'batch_results':summary['batch_graph_outputs'],'high_precision_values':validation['high_precision_values'],'figure_pairs':11,'whitepaper_pages':15,'hero_pixels':[2400,1200],'original_sdk_cxx':True,'tested_library_separate':True,'scientific_scope':'synthetic_reduced_order_surrogate'}
(root/'results/release_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
