from pathlib import Path
from hashlib import sha256
ROOT=Path(__file__).resolve().parents[1]
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and not any(x in p.parts for x in ['build','__pycache__','.git']))
(ROOT/'SHA256SUMS.txt').write_text(''.join(sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files))
print('WROTE SHA256SUMS',len(files),'files')
