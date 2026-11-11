#!/usr/bin/env python3
"""Verifies reference behavior of versioned LLM mathematical contracts."""
import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from llm_contract_adapter import execute
p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--input',required=True)
a=p.parse_args()
with open(a.input,encoding='utf-8') as f:rows=[json.loads(x) for x in f if x.strip()]
responses=execute(a.binary,rows)
expected=['OK','OK','OK','UNIT_MISMATCH','MODEL_MISMATCH','DOMAIN_ERROR','UNKNOWN_CONTRACT','OK','OK']
assert [x['status'] for x in responses]==expected,responses
assert [responses[i]['reused_graph'] for i in (0,1,2,7,8)]==[False,True,True,False,True],responses
for i in (0,1,2,7,8):
 assert abs(responses[i]['result']-responses[i]['native_reference'])<1e-11
print('PASS: 9 structured proposals, 4 deliberate rejections, persistent graph reuse')
