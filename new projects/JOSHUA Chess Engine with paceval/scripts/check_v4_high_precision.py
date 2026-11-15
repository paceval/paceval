#!/usr/bin/env python3
"""85-digit independent numerical audit of saved V4 paceval outputs.
Evaluation only: does not call paceval or reuse the native C++ feedforward.
"""
import csv,json,sys,math
from pathlib import Path
import mpmath as mp
mp.mp.dps=85
source=Path(sys.argv[1]);model=json.loads(Path(sys.argv[2]).read_text());rows=list(csv.DictReader(source.open()))
assert len(rows)>=100 and all(r['case'] for r in rows)
cols=model['input_features'];assert len(cols)==48
fmt=lambda value:mp.mpf(str(value))
means=[fmt(z) for z in model['feature_mean']];scales=[fmt(z) for z in model['feature_scale']]
W=[[fmt(z) for z in row] for row in model['hidden_weights']]
b=[fmt(z) for z in model['hidden_bias']];ow=[fmt(z) for z in model['output_weights']];ob=fmt(model['output_bias'])
failed=[];maximum=0.0
for i,r in enumerate(rows):
 x=[mp.mpf(r[c]) for c in cols]
 h=[]
 for j in range(len(b)):
  z=b[j]+sum(W[j][k]*(x[k]-means[k])/scales[k] for k in range(48))
  h.append(mp.mpf(1)/(mp.mpf(1)+mp.exp(-z)))
 z=100*(ob+sum(ow[j]*h[j] for j in range(len(h))))
 clipped=min(mp.mpf(150),max(-mp.mpf(150),z))
 expected=mp.mpf(r['v3_score'])+clipped
 observed=mp.mpf(r['paceval_score'])
 native=mp.mpf(r['native_score'])
 error=float(abs(expected-observed));maximum=max(maximum,error)
 if error>5e-7 or abs(native-observed)>mp.mpf('5e-7'):
  failed.append((r['case'],error))
assert not failed,failed[:5]
print(f'V4_HIGH_PRECISION_PASS cases={len(rows)} digits=85 max_abs_error_cp={maximum:.3g}')
