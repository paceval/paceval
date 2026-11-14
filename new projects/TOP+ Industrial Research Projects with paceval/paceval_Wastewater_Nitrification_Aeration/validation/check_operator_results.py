#!/usr/bin/env python3
"""Independent semantics audit for archived real paceval operator tests."""
from pathlib import Path
import json,sys
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
j=json.loads((R/'results'/'operator_remote_checks.json').read_text())
assert j['engine']=='paceval MCP 4.26' and j['graph_point_checks']==21 and not j['hasError']
results={r['id']:r['results'] for r in j['executed_expressions']}
assert results['percent_negative']==[-1,-1,-1]
assert results['mod_negative']==[9,9,9]
assert results['infix_min']==[4,4,4]
assert results['infix_max']==[5,5,5]
for i,(x,y,z) in enumerate(j['inputs']):
    assert results['logic_and'][i]==int(x<=2*y and z>=0)
    assert results['logic_not_or'][i]==int((not(x==y)) or z!=0)
    assert results['logic_xor'][i]==int((x==y)!=(z!=0))
print('PASS: 21 archived real paceval operator result checks independently evaluated.')
