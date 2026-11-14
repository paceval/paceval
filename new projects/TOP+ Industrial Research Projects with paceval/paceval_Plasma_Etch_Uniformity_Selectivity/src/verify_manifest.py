#!/usr/bin/env python3
"""Verify every packaged payload against its SHA-256 content manifest."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1];m=root/'results'/'sha256_manifest.txt'
assert m.is_file()
rows=m.read_text().splitlines();assert len(rows)>30
for row in rows:
 h,p=row.split('  ',1);f=root/p
 assert f.is_file(),f'Missing manifest file {p}'
 assert hashlib.sha256(f.read_bytes()).hexdigest()==h,f'SHA256 changed: {p}'
print('MANIFEST_VERIFICATION_PASS',len(rows))
