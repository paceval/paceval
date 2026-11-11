#!/usr/bin/env python3
"""Offline test of an LLM-to-math tool boundary with reusable paceval graphs.

An LLM may propose an expression and task metadata, but it does not choose
its own execution privileges. Each contract is a separately reviewed,
versioned formula and a declared dimension/unit signature. Formula equality
is *deliberately exact*: this is a pilot of contract enforcement, not a
symbolic equivalence prover or a universal dimensional-analysis system.

Input JSONL -> validated contract proposals -> persistent C++ --stream process
-> JSONL results. No network, authentication, or actual LLM is bundled.
"""
import argparse
import json
import math
import pathlib
import subprocess

FIELDS=('x','y','t','k','w','c')
UNITS={'x':'1','y':'1','t':'s','k':'1/s','w':'1/s','c':'1'}
CONTRACTS={
    'damped_signal_v1':'exp(-k*t)*sin(w*t)+c',
    'harmonic_signal_v1':'sin(w*t)+c',
}
ALLOWED_KEYS={'request_id','contract_id','expression','units','variables'}

def screen(obj):
    if not isinstance(obj,dict) or set(obj)!=ALLOWED_KEYS:
        return 'INVALID_SCHEMA',None
    request_id=obj['request_id']
    if not isinstance(request_id,str) or not (1<=len(request_id)<=64) or not request_id.isascii():
        return 'INVALID_SCHEMA',None
    contract=obj['contract_id'];expression=obj['expression']
    if not isinstance(contract,str) or contract not in CONTRACTS:
        return 'UNKNOWN_CONTRACT',None
    if not isinstance(expression,str) or len(expression)>180 or expression!=CONTRACTS[contract]:
        return 'MODEL_MISMATCH',None
    if obj['units']!=UNITS:
        return 'UNIT_MISMATCH',None
    variables=obj['variables']
    if not isinstance(variables,dict) or set(variables)!=set(FIELDS):
        return 'INVALID_SCHEMA',None
    if any(type(variables[k]) not in (int,float) or not math.isfinite(variables[k]) for k in FIELDS):
        return 'DOMAIN_ERROR',None
    v={k:float(variables[k]) for k in FIELDS}
    if not (-1<=v['x']<=1 and -1<=v['y']<=1 and 0<=v['t']<=2 and
            0<=v['k']<=2 and 0<=v['w']<=4 and -1<=v['c']<=1):
        return 'DOMAIN_ERROR',None
    return 'OK', expression+'\t'+','.join(format(v[k],'.17g') for k in FIELDS)

def execute(binary,rows,timeout=30):
    # The single C++ child owns and reuses each paceval computation handle.
    pending=[];screened=[]
    for obj in rows:
        try: status,payload=screen(obj)
        except (ValueError,TypeError,OverflowError):status,payload='INVALID_SCHEMA',None
        if status=='OK':
            pending.append(payload)
            screened.append(None)
        else:
            screened.append({'status':status})
    results=[]
    if pending:
        process=subprocess.run([str(binary),'--stream'],input='\n'.join(pending)+'\n',
             stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,check=False)
        if process.returncode:
            raise RuntimeError('paceval C++ stream process failed: '+process.stderr[-500:])
        answers=[json.loads(x) for x in process.stdout.splitlines() if x.strip()]
        if len(answers)!=len(pending):
            raise RuntimeError('Incomplete C++ response stream')
        results=iter(answers)
    output=[]
    for request,entry in zip(rows,screened):
        result=next(results) if entry is None else entry
        output.append({'request_id':request.get('request_id') if isinstance(request,dict) else None,**result})
    return output

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--binary',required=True)
    parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    binary=pathlib.Path(args.binary).resolve()
    if not binary.is_file():raise SystemExit('C++ executable not found')
    rows=[]
    with open(args.input,encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:rows.append(json.loads(line))
                except json.JSONDecodeError:rows.append({'request_id':None})
    if len(rows)>256:raise SystemExit('Maximum of 256 structured requests')
    answers=execute(binary,rows)
    with open(args.output,'w',encoding='utf-8') as f:
        for answer in answers:f.write(json.dumps(answer,allow_nan=False,separators=(',',':'))+'\n')
    print('Validated offline LLM proposal workflow:',len(answers),'requests')
if __name__=='__main__':main()
