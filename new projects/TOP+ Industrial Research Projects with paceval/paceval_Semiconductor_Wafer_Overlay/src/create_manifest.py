#!/usr/bin/env python3
"""Generate a manifest without including itself or temporary build artifacts."""
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent
lines=[]
for file in sorted(root.rglob('*')):
 if not file.is_file():continue
 rel=file.relative_to(root).as_posix()
 if rel=='SHA256SUMS.txt' or '/__pycache__/' in rel or rel.endswith('.pyc'):continue
 lines.append(hashlib.sha256(file.read_bytes()).hexdigest()+'  '+rel)
(root/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('SHA256 manifest:',len(lines),'files')
