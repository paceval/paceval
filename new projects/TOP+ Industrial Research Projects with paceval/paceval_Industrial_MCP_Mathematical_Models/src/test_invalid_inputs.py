#!/usr/bin/env python3
"""Real rejection tests for malformed inputs, with the genuine SDK executable."""
from pathlib import Path
import subprocess,sys,tempfile,shutil
project=Path(sys.argv[1]); executable=Path(sys.argv[2])
original=(project/'examples/synthetic_machine_cases.csv').read_text()
with tempfile.TemporaryDirectory() as tmp:
 r=Path(tmp);(r/'examples').mkdir();(r/'generated').symlink_to(project/'generated',target_is_directory=True)
 def rejects(csv,expected):
  (r/'examples/synthetic_machine_cases.csv').write_text(csv)
  p=subprocess.run([str(executable),str(r),'--verify-only'],capture_output=True,text=True)
  assert p.returncode!=0 and expected in p.stderr,(p.returncode,p.stderr)
 header,*lines=original.splitlines()
 a=lines.copy();part=a[0].split(',');part[1]='1.2';a[0]=','.join(part);rejects('\n'.join([header]+a)+'\n','Out-of-domain')
 b=lines.copy();part=b[0].split(',');part[4]='NaN';b[0]=','.join(part);rejects('\n'.join([header]+b)+'\n','Invalid finite')
 rejects(original.replace('case_id,x,y,z,temp,target,tol,raw,scenario','case_id,x,temp,z,y,target,tol,raw,scenario',1),'Unexpected dataset schema')
print('PASS actual C++ input validation rejected three invalid input classes')
