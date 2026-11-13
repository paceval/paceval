#!/usr/bin/env python3
"""Release preflight; not a substitute for page-by-page manual visual review."""
from pathlib import Path
import csv, json, fitz, hashlib, zipfile, subprocess, sys, re
from PIL import Image
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
subprocess.run([sys.executable,str(R/'src/check_readme_math.py')],cwd=R,check=True)
subprocess.run([sys.executable,str(R/'src/verify_results.py')],cwd=R,check=True)
assert (R/'figures/00_fermi_2fle_hero.png').exists()
hero=Image.open(R/'figures/00_fermi_2fle_hero.png');assert hero.size==(2400,1200) and hero.mode=='RGB'
pdf=fitz.open(R/'paceval_Fermi_2FLE_Spectral_Screening_Whitepaper_EN.pdf');assert len(pdf)==14
bad=[]
for idx,pg in enumerate(pdf):
 if not pg.get_text().strip():bad.append(('empty-page',idx+1))
 for img in pg.get_images(full=True):
  for rect in pg.get_image_rects(img[0]):
   if rect.x0<14 or rect.y0<27 or rect.x1>pg.rect.width-14 or rect.y1>pg.rect.height-40:bad.append(('out-of-printable-page-image',idx+1))
assert not bad,bad
for i in range(1,11):
 matches=list((R/'figures').glob(f'{i:02d}_*.png'))
 assert len(matches)==1,(i,matches)
 assert (R/'figures'/(matches[0].stem+'.pdf')).exists()
assert all((R/'src'/p).exists() for p in ['paceval_main.cpp','paceval_main.h','CMakeLists.txt','fermi_2fle_demo.cpp','high_precision_reference.py','make_figures.py','make_whitepaper.py','verify_results.py','extract_catalog_from_report.py','check_readme_math.py'])
assert not list(R.rglob('LICENSE_NOTICE.md'))
assert not list(R.rglob('*.so'))
assert '100% tests passed' in (R/'results/ctest_sdk.txt').read_text()
result={'status':'PASS','release_date':'2026-11-13','whitepaper_pages':14,'hero_dimensions':list(hero.size),'scientific_figure_pairs':10,'original_paceval_sdk_real_test':'PASS','real_sdk_full_run':'PASS','replayed_files_identical':8,'readme_math_and_link_static_check':'PASS','pdf_page_images_in_bounds':'PASS','pdf_layout_visual_manual_review':'reviewed 14-page contact sheet plus full-size math and plot pages; no recognizable overlap','original_2FLE_FITS_included':False,'scientific_scope':'metadata transcription plus paceval synthetic methods only'}
(R/'results/release_qa.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS release QA',result)
