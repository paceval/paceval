#!/usr/bin/env python3
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent.parent
skipped={'build','__pycache__','.git'}
files=sorted(f for f in R.rglob('*') if f.is_file() and not any(x in skipped for x in f.relative_to(R).parts) and f.name!='SHA256SUMS.txt' and not f.suffix in ('.so','.o','.a') and not f.name.endswith('.log'))
with open(R/'SHA256SUMS.txt','w') as out:
 for f in files:out.write(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n')
print('Wrote checksums for',len(files),'files')
