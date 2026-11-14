#!/usr/bin/env python3
"""Project integrity checks. Does not claim local SDK execution or GitHub preview."""
from pathlib import Path
import json,csv,subprocess,sys,re
from PIL import Image
R=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
manifest=json.loads((R/'src/formula_manifest.json').read_text())
evidence=json.loads((R/'results/execution_evidence.json').read_text())
for group,expected,count in [('edge',22,49),('network',25,25)]:
 assert len(manifest['groups'][group]['graphs'])==expected
 assert len({g['id'] for g in manifest['groups'][group]['graphs']})==expected
 for g in manifest['groups'][group]['graphs']:
  assert g['formula'] and g['mcp_handle_for_audit_only'] and g['version']
 data_file=R/'examples'/('synthetic_edge_grid.csv' if group=='edge' else 'synthetic_network_dispatch.csv')
 with data_file.open() as f:
  reader=csv.reader(f);rows=list(reader)
 assert len(rows)==count+1
 assert rows[0][1:]==manifest['groups'][group]['variables']
 assert all(len(r)==len(rows[0]) for r in rows[1:])
result_files={'mcp_edge_observed.csv':49,'mcp_network_observed.csv':25}
for fname,count in result_files.items():
 with (R/'results'/fname).open() as f:records=list(csv.DictReader(f))
 assert len(records)==count
 assert all(all(value!='' for value in rec.values()) for rec in records)
assert evidence['edge_graph_point_evaluations']==22*49
assert evidence['network_graph_point_evaluations']==25*25
assert evidence['independent_90_digit_checks']==547
assert evidence['local_sdk_build_executed'] is False
assert not list(R.rglob('*.so'))
assert not (R/'LICENSE_NOTICE.md').exists()
assert not (R/'docs/whitepaper.md').exists()
with Image.open(R/'figures/00_district_heating_hero.png') as im:assert im.size==(2400,1200) and im.mode=='RGB'
images=list((R/'figures').glob('*.png'))
assert len(images)>=12
for img in images:
 if img.name.startswith('00_'):continue
 assert (img.with_suffix('.pdf')).exists(),img
assert (R/'paceval_District_Heating_Thermal_Dispatch_Whitepaper_EN.pdf').stat().st_size>10000
try:
 import fitz
 pdf=fitz.open(R/'paceval_District_Heating_Thermal_Dispatch_Whitepaper_EN.pdf')
 assert len(pdf)>=10
 for i,p in enumerate(pdf):
  text=p.get_text()
  assert text.strip(),('empty page',i)
  assert len(p.get_images())>0 if i==0 else True
except ImportError:pass
subprocess.run([sys.executable,str(R/'src/check_readme_math.py')],check=True)
subprocess.run([sys.executable,str(R/'validation/high_precision_reference.py'),str(R)],check=True)
print('PROJECT INTEGRITY PASS: manifest, actual output tables, high precision audit, 2400x1200 hero, PDF and README links')
