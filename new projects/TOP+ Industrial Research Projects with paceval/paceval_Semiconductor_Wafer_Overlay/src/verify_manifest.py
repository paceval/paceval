#!/usr/bin/env python3
"""Verify SHA-256 for every released file except the manifest itself."""
import hashlib,sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent.parent)
manifest=root/'SHA256SUMS.txt'
lines=manifest.read_text(encoding='utf-8').splitlines()
for line in lines:
 digest,rel=line.split('  ',1)
 file=root/rel
 assert file.is_file(),f'Missing {rel}'
 assert hashlib.sha256(file.read_bytes()).hexdigest()==digest,f'Changed file {rel}'
print('PASS: SHA-256 integrity for',len(lines),'released files')
