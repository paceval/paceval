#!/usr/bin/env python3
"""Project release hash manifest, excluding its own hash and release build directories."""
from pathlib import Path
import hashlib
base=Path(__file__).resolve().parents[1];out=base/'SHA256SUMS.txt'
all=sorted(p for p in base.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and not any(x in p.parts for x in ('build','__pycache__','.git')))
assert all
lines=[]
for path in all:
    assert not path.suffix=='.so','A shared library must not be bundled'
    lines.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.relative_to(base).as_posix())
out.write_text('\n'.join(lines)+'\n')
print('SHA256SUMS generated for',len(lines),'files')
