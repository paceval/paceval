#!/usr/bin/env python3
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent.parent
lines=(R/'SHA256SUMS.txt').read_text().splitlines();assert len(lines)>=40
for line in lines:
 value,relative=line.split('  ',1)
 path=(R/relative).resolve();assert path.is_relative_to(R.resolve()) and path.is_file()
 assert hashlib.sha256(path.read_bytes()).hexdigest()==value,f'Checksum failure: {relative}'
print('MANIFEST PASS',len(lines),'files')
