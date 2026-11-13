#!/usr/bin/env python3
"""Check consistency of all referenced research deliverables before publication."""
from pathlib import Path
from PIL import Image
import fitz,csv,json,hashlib
R=Path(__file__).resolve().parents[1];assert (R/'src/CMakeLists.txt').exists()
assert (R/'src/paceval_main.h').exists() and (R/'src/paceval_main.cpp').exists()
assert (R/'reference/WP_044_Parameterized_Bulk_Wave_Evaluation_Kernels.pdf').exists()
assert not any(R.glob('**/*.so'))
img=Image.open(R/'figures/00_bulk_wave_hero.png');assert img.size==(2400,1200)
for i in range(1,13):
    p=list((R/'figures').glob(f'{i:02d}_*.png'));assert len(p)==1,(i,p)
    assert p[0].with_suffix('.pdf').exists(),p[0]
    assert Image.open(p[0]).width>=900
pdf=fitz.open(R/'paceval_Bulk_Wave_Kernels_Whitepaper_EN.pdf');assert len(pdf)==16,len(pdf)
for i,page in enumerate(pdf):
    assert len(page.get_text().strip())>250,(i,'page unusually empty')
    w,h=page.rect.width,page.rect.height
    for b in page.get_text('blocks'):
        if b[6]!=0:continue
        assert b[0]>=-1 and b[1]>=-1 and b[2]<=w+1 and b[3]<=h+1,('clipped text',i+1,b[:4])
result=json.loads((R/'results/execution_summary.json').read_text());audit=json.loads((R/'results/high_precision_audit.json').read_text());assert result['paceval_persistent_graphs']==28 and result['paceval_batch_outputs']==663784 and audit['status']=='passed'
registry=list(csv.DictReader((R/'examples/formula_registry.csv').open()));assert len(registry)==28
assert len(list(csv.DictReader((R/'examples/grid_convergence.csv').open())))==12
assert len(list(csv.DictReader((R/'examples/parameterized_kernel_surface.csv').open())))==7623
assert (R/'results/sdk_execution.log').exists() and (R/'results/reproducibility_check.json').exists()
print('PASS release: 16 optically rendered PDF pages, 12 scientific figure pairs, 2400x1200 cover, original SDK, 28 graphs, provenance and results')
