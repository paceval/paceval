#!/usr/bin/env python3
"""JSONL agent-tool adapter: validates requests and executes one C++ batch.

This is a local offline schema demonstration, NOT a deployed MCP server,
LLM, or publicly accessible endpoint. The C++ program is the authority for
model IDs, dimensional validation, numeric domains and paceval execution.
No untrusted shell command is ever interpolated into a subprocess invocation.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import pathlib
import subprocess
import tempfile

COLS=['request_id','model_id','expression','output_unit']+[z for i in range(6) for z in (f'v{i}',f'u{i}')]+['expected_status']

def parse_agent_call(obj):
    if not isinstance(obj,dict) or set(obj)!={'name','arguments'} or obj['name']!='evaluate_engineering_formula':
        raise ValueError('unknown tool name or envelope fields')
    a=obj['arguments']
    if not isinstance(a,dict) or set(a)!={'request_id','model_id','expression','output_unit','inputs'}:
        raise ValueError('arguments must exactly match the documented tool schema')
    if not isinstance(a['inputs'],list) or len(a['inputs'])!=6:
        raise ValueError('inputs must contain exactly six ordered slots')
    r={k:a[k] for k in ['request_id','model_id','expression','output_unit']}
    for k in r:
        if not isinstance(r[k],str):raise ValueError('required string field is not a string')
        if any(x in r[k] for x in [',','\n','\r']):raise ValueError('CSV delimiter/control character is forbidden')
    for i,v in enumerate(a['inputs']):
        if not isinstance(v,dict) or set(v)!={'value','unit'}:
            raise ValueError('input slot must contain exactly value and unit')
        value,unit=v['value'],v['unit']
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)):
            raise ValueError('input value must be finite number or null')
        if not isinstance(unit,str) or any(z in unit for z in [',','\r','\n']):
            raise ValueError('unit must be a simple string')
        r[f'v{i}']='' if value is None else format(value,'.17g')
        r[f'u{i}']=unit
    r['expected_status']=''
    return r

def run(requests,engine,output):
    rows=[];schema_errors=[];ids=set()
    with open(requests,encoding='utf-8') as f:
        for line_no,line in enumerate(f,1):
            if not line.strip():continue
            try:
                obj=json.loads(line)
                r=parse_agent_call(obj)
                if r['request_id'] in ids:raise ValueError('duplicate request_id')
                ids.add(r['request_id'])
                rows.append(r)
            except (ValueError,TypeError,KeyError) as e:
                schema_errors.append({'line':line_no,'status':'SCHEMA_ERROR','reason':str(e)})
    result=[]
    if rows:
        with tempfile.TemporaryDirectory(prefix='paceval_agent_') as tmp:
            p=pathlib.Path(tmp)
            with (p/'calls.csv').open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=COLS);writer.writeheader();writer.writerows(rows)
            proc=subprocess.run([str(pathlib.Path(engine).resolve()),'--cases',str(p/'calls.csv'),
                                 '--output',str(p/'results.csv'),'--tinc',str(p/'unused_tinc.csv'),
                                 '--skip-tinc','--batch','64'],capture_output=True,text=True,check=False)
            if proc.returncode:
                raise RuntimeError(f'C++ backend returned {proc.returncode}: {proc.stderr}')
            with (p/'results.csv').open(newline='',encoding='utf-8') as f:
                result=list(csv.DictReader(f))
    with open(output,'w',encoding='utf-8') as f:
        for row in result:
            response={'request_id':row['request_id'],'model_id':row['model_id'],
                      'status':row['status'],'result':None,'unit':None}
            if row['status']=='OK':
                response.update(result=float(row['result']),unit=row['unit'])
            f.write(json.dumps(response,sort_keys=True)+'\n')
        for row in schema_errors:f.write(json.dumps(row,sort_keys=True)+'\n')
    print(f'JSONL tool calls: {len(rows)} forwarded to paceval; {len(schema_errors)} rejected by schema; output: {output}')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--requests',required=True)
    ap.add_argument('--engine',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    run(a.requests,a.engine,a.output)
