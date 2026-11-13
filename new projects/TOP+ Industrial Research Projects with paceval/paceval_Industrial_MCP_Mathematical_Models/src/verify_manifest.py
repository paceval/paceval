import json,hashlib,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
a=json.loads((root/'generated/manifest.json').read_text())
for fname,r in a['formulas'].items():
 p=root/'generated'/fname;assert p.is_file(),fname
 s=p.read_bytes();assert hashlib.sha256(s).hexdigest()==r['sha256']
 assert len(s.decode().strip())==r['length']
print('PASS exact formula source SHA-256 checksums:',len(a['formulas']))
