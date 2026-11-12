#!/usr/bin/env python3
"""Independent integrity and mathematical verification of released CSVs.

This checks all 10,000 exported scalar requests, their 2,000 compositions,
the frozen registry and all 3,721 surface points, without using paceval.
It does not repeat the SDK execution; CTest does that independently.
"""
import csv, math, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(name):return list(csv.DictReader((R/'examples'/name).open()))
registry=read('tool_registry.csv');requests=read('requests.csv');surface=read('response_surface.csv');version=read('version_audit.csv')
assert len(registry)==51 and len(requests)==10000 and len(surface)==3721 and len(version)==1
models={(int(r['tool_id']),int(r['version'])):r for r in registry}
def eval_native(tool_id,x,y,a,b,c):
    model=models[(tool_id,1)];family=int(model['family']);k=float(model['k'])
    if family==0:return a*x*x+b*math.log1p(x)+k*c*y
    if family==1:return a*math.exp(-k*x)+b*math.sin(x+y)+c*x*y
    if family==2:return a/(1+k*x*x)+b*math.sqrt(1+x)+c*math.cos(y)
    if family==3:return (a*x+b*y+c)/(1+k*x*x)+math.sin(x*y)
    return a*math.log1p(x*x)+b*math.exp(-x*y*y)+k*c*x*x
max_error=0.0;composition_count=0
for row in requests:
    tid=int(row['tool_id']);x,y,a,b,c=[float(row[q]) for q in ('x','y','a','b','c')]
    expected=eval_native(tid,x,y,a,b,c);actual=float(row['paceval']);d=abs(actual-expected)
    assert d<1e-10*(1+abs(expected)),(tid,d);max_error=max(max_error,d)
    if row['composed_value']:
        second=((int(row['request_id'])-1+17)%50)+1
        expected2=eval_native(second,x,math.tanh(actual),a,b,c);actual2=float(row['composed_value'])
        assert abs(expected2-actual2)<1e-10*(1+abs(expected2));composition_count+=1
for row in surface:
    x,y,z=float(row['x']),float(row['y']),float(row['paceval'])
    ref=eval_native(23,x,y,0.9,0.8,0.7)
    assert abs(ref-z)<1e-10*(1+abs(ref))
assert composition_count==2000
out={'registry_rows':len(registry),'requests':len(requests),'compositions_checked':composition_count,'surface_points_checked':len(surface),'max_request_oracle_discrepancy':max_error,'status':'PASS'}
(R/'results/reproducibility_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
