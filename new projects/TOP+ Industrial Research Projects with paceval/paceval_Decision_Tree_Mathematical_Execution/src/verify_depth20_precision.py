#!/usr/bin/env python3
"""Independent 80-digit reference for the structured 20-level test; no SDK calls."""
import csv, json, sys
from pathlib import Path
from mpmath import mp
mp.dps=80
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
rows=list(csv.DictReader((root/'results/depth20_representative_cases.csv').open()))
assert len(rows)==15, ('unexpected coverage',len(rows))
maxdiff1=mp.mpf(0);maxdiff2=mp.mpf(0)
for row in rows:
    n=int(row['leaf_id']);k=int(row['ones'])
    assert n.bit_count()==k
    v1=(mp.mpf('0.07')+mp.mpf('0.0000003')*n+mp.mpf('0.002')*k+mp.mpf('0.03')*mp.sin(mp.mpf(n)/250000))
    v2=(mp.mpf('0.09')+mp.mpf('0.00000025')*n+mp.mpf('0.0014')*k+mp.mpf('0.04')*mp.sin(mp.mpf(n)/200000)+mp.mpf('0.005')*int(bool(n&(1<<19)) and bool(n&1)))
    d1=abs(v1-mp.mpf(row['score_v1']));d2=abs(v2-mp.mpf(row['score_v2']))
    maxdiff1=max(maxdiff1,d1);maxdiff2=max(maxdiff2,d2)
    assert d1<mp.mpf('1e-12') and d2<mp.mpf('1e-12'),row
result={'precision_decimal_digits':80,'sampled_leaf_indices':len(rows),'verified_score_values':len(rows)*2,'max_abs_discrepancy_v1_audit_only':mp.nstr(maxdiff1,9),'max_abs_discrepancy_v2_audit_only':mp.nstr(maxdiff2,9),'status':'PASS','scope':'Selected 15 representative leaves; full exhaustive path and native score checks occur in C++'}
(root/'results/depth20_80digit_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('Independent 80-digit depth-20 audit PASS:',len(rows),'leaves,',len(rows)*2,'scores')
