#!/usr/bin/env python3
"""Check sha256 file-integrity manifest including all code, figures and sources."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1];file=root/'SHA256SUMS.txt'
assert file.is_file(),'Missing SHA256 manifest'
n=0
for entry in file.read_text().splitlines():
 digest,path=entry.split('  ',1)
 f=root/path;assert f.is_file(),('missing manifest target',path)
 assert hashlib.sha256(f.read_bytes()).hexdigest()==digest,('hash mismatch',path)
 n+=1
count=len([p for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and 'build' not in p.relative_to(root).parts and '__pycache__' not in p.parts])
assert n==count,(n,count)
print('SHA256 FILE MANIFEST PASSED',n,'files')
