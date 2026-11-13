"""Run 65,536-interval, dual-model stress proof without overwriting base results.
Usage: python3 src/run_large_capacity.py /path/to/industrial_calibration
Requires mpmath for independent high precision verification.
"""
from pathlib import Path
import sys, subprocess, shutil, tempfile
HERE=Path(__file__).resolve().parents[1]
bin=Path(sys.argv[1]).resolve()
assert bin.is_file(),bin
out=HERE/'results/large_capacity'
out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='paceval_calibration_') as tmp:
 temp=Path(tmp);(temp/'examples').mkdir();(temp/'results').mkdir()
 shutil.copy2(HERE/'examples/synthetic_sensor_inputs.csv',temp/'examples')
 subprocess.run([str(bin),str(temp),'256','65536','512'],check=True)
 subprocess.run([sys.executable,str(HERE/'src/independent_reference.py'),str(temp)],check=True)
 for p in (temp/'results').iterdir():shutil.copy2(p,out/p.name)
 print('Saved independently audited large-capacity graph evidence to',out)
