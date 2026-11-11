#!/usr/bin/env python3
"""Offline JSONL tool-call adapter, not an MCP server and not an LLM.

Accepts one simple JSON object per line:
  {"request_id":"demo", "expression":"exp(-k*t)*sin(w*t)+c",
   "variables":{"x":0.2,"y":0.1,"t":0.5,"k":0.3,"w":1.2,"c":0.1}}
This adapter calls the compiled paceval-backed C++ binary with explicit argv,
not a shell. It rejects unknown keys, nonfinite numbers, missing variables and
unexpected types; the C++ parser independently checks all expression inputs.
No arbitrary expression execution, filesystem writes or network services.
"""
import argparse,json,math,subprocess,sys,pathlib
KEYS=('x','y','t','k','w','c')
def process(line,binary):
    payload=json.loads(line)
    if not isinstance(payload,dict) or set(payload)!={'request_id','expression','variables'}:
        raise ValueError('Tool arguments must contain exactly request_id, expression, variables')
    rid,expr,v=payload['request_id'],payload['expression'],payload['variables']
    if not isinstance(rid,str) or not(1<=len(rid)<=64) or not rid.isascii():
        raise ValueError('Invalid request ID')
    if not isinstance(expr,str) or not(1<=len(expr)<=180):
        raise ValueError('Invalid expression length')
    if not isinstance(v,dict) or set(v)!=set(KEYS):raise ValueError('Expected six named variables')
    if any(type(v[k]) not in (float,int) or not math.isfinite(float(v[k])) for k in KEYS):
        raise ValueError('Nonfinite or nonnumeric variable')
    values=','.join(format(float(v[k]),'.17g') for k in KEYS)
    proc=subprocess.run([str(binary),'--formula',expr,'--values',values],stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,encoding='utf8',timeout=10,check=False)
    if proc.returncode:
        return {'request_id':rid,'status':'TOOL_FAILURE','message':'Backend rejected arguments'}
    obj=json.loads(proc.stdout.strip());return {'request_id':rid,**obj}
def main():
    p=argparse.ArgumentParser();p.add_argument('--binary',required=True)
    p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();binfile=pathlib.Path(a.binary).resolve()
    if not binfile.is_file():raise SystemExit('Compiled C++ binary not found')
    with open(a.input,encoding='utf8') as f,open(a.output,'w',encoding='utf8') as out:
        for line in f:
            if not line.strip():continue
            try:answer=process(line,binfile)
            except (ValueError,TypeError,json.JSONDecodeError,subprocess.TimeoutExpired):
                answer={'request_id':None,'status':'INVALID_REQUEST'}
            out.write(json.dumps(answer,separators=(',',':'),allow_nan=False)+'\n')
    print('Offline structured tool adapter completed')
if __name__=='__main__':main()
