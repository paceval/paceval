#!/usr/bin/env python3
"""Deterministic, synthetic, lossless-dielectric optical samples. NOT measured wafers."""
import csv,math,random,sys
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'input'/'spectral_samples.csv'
seed=20261115
rng=random.Random(seed)
wavelengths=[405,445,485,525,565,605,665,725,785]
lines=[]
for i in range(144):
    ix=i%12;iy=i//12
    d=235+43*math.sin((ix+1)*.39)*math.cos((iy+2)*.29)+19*math.sin((ix+iy)*.23)
    alpha=.0028+0.0006*math.cos(ix*.31+iy*.13)
    nf=1.45+0.10*(ix/11)+.012*math.cos(iy*.51)
    ns=1.73+0.028*math.sin(iy*.41)
    offset=.015+.005*math.sin(ix*.21)
    for lam in wavelengths:
        lines.append([f'S{i:04d}',ix,iy,f'{d:.14g}',f'{alpha:.14g}',f'{nf:.14g}',f'{ns:.14g}',f'{offset:.14g}',lam,f'{rng.uniform(-.001,.001):.14g}',f'{rng.uniform(-.00035,.00035):.14g}'])
with out.open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['site_id','pixel_x','pixel_y','true_nm','alpha_per_nm','film_n','substrate_n','offset','wavelength_nm','noise_t','noise_r']);w.writerows(lines)
if '--check' in sys.argv:
    assert out.read_bytes()==out.read_bytes()
print(f'SYNTHETIC_INPUT rows={len(lines)} sites=144 seed={seed}, path={out}')
