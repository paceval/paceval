from pathlib import Path
from hashlib import sha256
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'SHA256SUMS.txt';assert manifest.is_file()
count=0
for line in manifest.read_text().splitlines():
    value,relative=line.split('  ',1)
    f=(ROOT/relative).resolve()
    assert f.is_relative_to(ROOT.resolve()) and f.is_file()
    assert sha256(f.read_bytes()).hexdigest()==value,relative
    count+=1
assert count>=45,count
print('PASS SHA-256 check',count,'archived files')
