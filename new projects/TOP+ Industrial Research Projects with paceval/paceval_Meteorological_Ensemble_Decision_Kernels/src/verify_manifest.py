#!/usr/bin/env python3
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent.parent
obj=json.loads((root/'SHA256_MANIFEST.json').read_text())
assert obj['schema']=='sha256-file-integrity-v1'
for name,want in obj['files'].items():
    p=(root/name)
    assert p.is_file(),name
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    assert got==want,('SHA256 changed',name)
print('MANIFEST PASSED:',len(obj['files']),'file hashes')
