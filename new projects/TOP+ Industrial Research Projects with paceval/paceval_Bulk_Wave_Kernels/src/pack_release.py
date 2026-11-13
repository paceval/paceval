#!/usr/bin/env python3
"""Build a reproducible GitHub archive from source, PDF, tested data and figures.
Exclude compile products, external paceval runtime binaries and Python caches.
"""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
DEST=R.parent/'WP044_Bulk_Wave_Kernels_Paceval_GitHub_Final.zip'
include=[]
for prefix in ('src','figures','examples','results','reference'):
    for p in sorted((R/prefix).rglob('*')):
        if not p.is_file():continue
        if '__pycache__' in p.parts or p.suffix in ('.pyc','.so','.o','.a','.exe') or p.name in ('CMakeCache.txt',):continue
        include.append(p)
include += [R/'README.md',R/'paceval_Bulk_Wave_Kernels_Whitepaper_EN.pdf']
include=sorted(set(include),key=lambda p:str(p.relative_to(R)))
manifest=R/'SHA256SUMS.txt'
manifest.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(R).as_posix()}\n' for p in include),encoding='utf-8')
include.append(manifest)
with zipfile.ZipFile(DEST,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for p in sorted(include):z.write(p,arcname=(R.name+'/'+p.relative_to(R).as_posix()))
with zipfile.ZipFile(DEST) as z:
    assert z.testzip() is None
    names=set(z.namelist())
    expected=set(R.name+'/'+p.relative_to(R).as_posix() for p in include)
    assert names==expected,(names-expected,expected-names)
    for entry in manifest.read_text().splitlines():
        digest,file=entry.split('  ',1)
        assert hashlib.sha256(z.read(R.name+'/'+file)).hexdigest()==digest,file
    assert not any('/build/' in x or x.endswith('.so') for x in names)
    print(f'ZIP VERIFIED {DEST} ({len(names)} files, {DEST.stat().st_size/1024/1024:.2f} MiB), SHA256 manifest consistent')
