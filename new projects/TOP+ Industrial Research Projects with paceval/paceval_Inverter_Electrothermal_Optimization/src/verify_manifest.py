#!/usr/bin/env python3
"""Verify the canonical build- and runtime-independent SHA256 project list."""
from pathlib import Path
import hashlib
base=Path(__file__).resolve().parents[1]
p=base/'SHA256SUMS.txt'
assert p.is_file(), 'SHA256SUMS.txt missing'
seen=set()
for line in p.read_text().splitlines():
    digest,name=line.split('  ',1)
    path=(base/name).resolve()
    assert path.is_relative_to(base.resolve()) and path.is_file(),name
    assert path.name!='SHA256SUMS.txt'
    assert path.suffix!='.so'
    assert name not in seen
    seen.add(name)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest, name+' hash mismatch'
assert len(seen)>=35
print('PASS SHA-256 manifest:',len(seen),'files')
