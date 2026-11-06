#!/usr/bin/env python3
import csv,json,re,subprocess,sys,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
binary=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else root/'bin/braneworld_v13_linux_x86_64'
reference=1.03771487669293765152978766858
rows=[]
for n in (250,500,1000,2000,4000):
    p=subprocess.run([str(binary),'--backend','native','--steps',str(n),'--output',str(root/'results'/f'temp_convergence_{n}')],capture_output=True,text=True,check=True,cwd=root)
    m=re.search(r'delta=([0-9.eE+-]+) relative_pct=([0-9.eE+-]+)',p.stdout)
    assert m
    value=float(m.group(1)); rows.append(dict(steps=n,advance=value,abs_error=abs(value-reference),relative_pct=float(m.group(2))))
    for file in (root/'results'/f'temp_convergence_{n}.native.csv',):
       file.unlink(missing_ok=True)
with (root/'validation'/'convergence_v13.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(json.dumps(rows,indent=2))
