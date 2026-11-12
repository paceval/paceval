#!/usr/bin/env python3
"""Independent arbitrary-precision audit of exported paceval results.
Reimplements five mathematical families; never calls the paceval library.
"""
import csv, json
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'examples/requests.csv').open()))
checks=0; errors=[]
for row in rows[::40]:
    x,y,a,b,c=[mp.mpf(row[k]) for k in ['x','y','a','b','c']]
    tool=int(row['tool_id'])-1; fam=tool//10
    # Original k in C++ is 0.11 + 0.07 * index, rounded to 9 decimals in formula.
    k=mp.mpf(str(round(.11+.07*(tool%10),9)))
    if fam==0: exact=a*x*x+b*mp.log(1+x)+k*c*y
    elif fam==1: exact=a*mp.exp(-k*x)+b*mp.sin(x+y)+c*x*y
    elif fam==2: exact=a/(1+k*x*x)+b*mp.sqrt(1+x)+c*mp.cos(y)
    elif fam==3: exact=(a*x+b*y+c)/(1+k*x*x)+mp.sin(x*y)
    else: exact=a*mp.log(1+x*x)+b*mp.exp(-x*y*y)+k*c*x*x
    err=abs(mp.mpf(row['paceval'])-exact);errors.append(float(err));checks+=1
    assert err<mp.mpf('1e-10')*(1+abs(exact)), (row['request_id'],err)
out={'reference':'80-digit mpmath, independent expression definitions','checked':checks,'passed':checks,'maximum_abs_error':max(errors),'tolerance':'absolute error <=1e-10*(1+|oracle|)','sample':'every 40th scripted request','numeric_note':'CSV input strings are decimal representations of original double-precision binary values'}
(ROOT/'results/high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
