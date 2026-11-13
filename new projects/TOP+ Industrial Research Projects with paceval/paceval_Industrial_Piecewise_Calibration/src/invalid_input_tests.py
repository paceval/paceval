"""Exercise domain, finite-value and schema rejection before model graph execution."""
from pathlib import Path
import subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1]
exe=Path(sys.argv[1]);src=(R/'examples/synthetic_sensor_inputs.csv').read_text().splitlines()
assert len(src)>128
cases={'out_of_range_x':(2,'1.01'),'out_of_range_temperature':(3,'75.0'),
       'nonfinite_x':(2,'nan'),'negative_uncertainty':(7,'-1'),
       'malformed_csv':(None,None)}
with tempfile.TemporaryDirectory(prefix='calib_reject_') as path:
   root=Path(path);(root/'examples').mkdir();(root/'results').mkdir()
   for label,(i,val) in cases.items():
      lines=src.copy();cols=lines[1].split(',')
      if i is None: lines[1]=','.join(cols[:-2])
      else:cols[i]=val;lines[1]=','.join(cols)
      (root/'examples/synthetic_sensor_inputs.csv').write_text('\n'.join(lines)+'\n')
      p=subprocess.run([str(exe),str(root),'128'],capture_output=True,text=True,timeout=15)
      if p.returncode==0:raise AssertionError(f'{label} incorrectly accepted')
      print('PASS invalid input rejected:',label)
