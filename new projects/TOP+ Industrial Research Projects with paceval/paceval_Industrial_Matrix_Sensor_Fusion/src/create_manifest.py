from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
items=[]
for p in sorted(root.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(root)
    if str(rel)=='SHA256SUMS.txt' or '__pycache__' in rel.parts or rel.parts[0]=='build':continue
    items.append((hashlib.sha256(p.read_bytes()).hexdigest(),rel.as_posix()))
(root/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for h,name in items))
print(len(items),'file hashes written')
