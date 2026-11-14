#!/usr/bin/env python3
"""SHA-256 content inventory, excluding itself and generated cache/build files."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
manifest=root/'results'/'sha256_manifest.txt'
entries=[]
for p in sorted(root.rglob('*')):
 if not p.is_file() or p==manifest or any(q in {'.git','__pycache__','build','reproduced','.pytest_cache'} for q in p.relative_to(root).parts):continue
 entries.append((hashlib.sha256(p.read_bytes()).hexdigest(),p.relative_to(root).as_posix()))
manifest.write_text(''.join(f'{h}  {p}\n' for h,p in entries))
print('MANIFEST_WRITTEN',len(entries))
