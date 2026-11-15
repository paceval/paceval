#!/usr/bin/env python3
"""Freeze all source, data, picture, document hashes except the manifest itself."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
rows=[]
for p in sorted(root.rglob('*')):
 if not p.is_file() or p.name=='SHA256SUMS.txt' or 'build' in p.relative_to(root).parts or '__pycache__' in p.parts:continue
 rows.append((hashlib.sha256(p.read_bytes()).hexdigest(),p.relative_to(root).as_posix()))
(root/'SHA256SUMS.txt').write_text(''.join(f'{a}  {b}\n' for a,b in rows),encoding='utf-8')
print('Manifest generated for',len(rows),'files')
