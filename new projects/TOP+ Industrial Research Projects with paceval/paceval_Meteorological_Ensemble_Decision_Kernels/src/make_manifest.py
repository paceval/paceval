#!/usr/bin/env python3
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parent.parent
entries={}
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.name=='SHA256_MANIFEST.json' or '__pycache__' in p.parts or p.suffix=='.pyc':continue
    relative=p.relative_to(root).as_posix()
    entries[relative]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'SHA256_MANIFEST.json').write_text(json.dumps({'schema':'sha256-file-integrity-v1','files':entries},indent=2,sort_keys=True)+'\n')
print('MANIFEST GENERATED:',len(entries),'verified paths')
