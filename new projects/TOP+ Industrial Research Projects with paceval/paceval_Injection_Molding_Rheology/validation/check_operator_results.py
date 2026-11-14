import json,sys
from pathlib import Path
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
data=json.loads((R/'results/remote_operator_selftests.json').read_text())
assert data['results']=={'negative_remainder':[-1,-1,-1],'negative_modulo':[9,9,9],'infix_min':[4,4,4],'infix_max':[5,5,5],'and_boundary':[1,1,0],'not_or':[0,1,1],'xor':[1,0,1]}
assert data['nonzero_error_codes']==0 and data['point_evaluations']==21
print('Operator remote evidence and independent truth table: PASS, 21 checks')
