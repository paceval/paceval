from pathlib import Path
import subprocess,sys,hashlib
p=Path(__file__).resolve().parents[1]/'input'/'spectral_samples.csv'
a=p.read_bytes();subprocess.run([sys.executable,str(Path(__file__).parent/'generate_input.py')],check=True);b=p.read_bytes()
assert a==b
print('Deterministic input generation PASS',len(b),hashlib.sha256(b).hexdigest())
