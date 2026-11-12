#!/usr/bin/env python3
"""Local JSONL-to-persistent-C++ adapter for a whitelist-based mathematical tool.

Not an MCP transport/server and not an LLM. Dicts are validated before they can
become native requests. Example JSONL is generated for deterministic replay.
"""
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

ALLOWED={'request_id','formula_id','version','x','a','unit'}
def validate(obj):
    if not isinstance(obj,dict) or set(obj)!=ALLOWED:
        raise ValueError('schema_field_mismatch')
    if type(obj['request_id']) is not str or not (1<=len(obj['request_id'])<=48) or not all(
        c.isascii() and (c.isalnum() or c in '_-') for c in obj['request_id']):
        raise ValueError('invalid_request_id')
    for k in ('formula_id','version','unit'):
        if type(obj[k]) is not str or '|' in obj[k] or '\n' in obj[k]:raise ValueError('invalid_string')
    if obj['formula_id']!='CHAIN_LOGRATIO':raise ValueError('unknown_formula_id')
    if obj['version'] not in ('1.0','1.1'):raise ValueError('unknown_formula_version')
    if obj['unit']!='dimensionless':raise ValueError('ambiguous_or_incompatible_unit')
    for k in ('x','a'):
        if type(obj[k]) not in (int,float) or not math.isfinite(obj[k]):raise ValueError('invalid_number')
    if abs(obj['x'])>4:raise ValueError('x_out_of_domain')
    if abs(obj['a'])>2:raise ValueError('a_out_of_domain')
    if abs(1+obj['a']*obj['x'])<0.05:raise ValueError('near_zero_denominator')
    return obj

def to_native(d):
    return '|'.join([d['request_id'],d['formula_id'],d['version'],repr(float(d['x'])),
                     repr(float(d['a'])),d['unit']])

def run(binary,requests,outdir):
    result=[]
    with subprocess.Popen([str(binary),'--serve','--out',str(outdir)],stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1) as proc:
        for obj in requests:
            try:
                valid=validate(obj)
                proc.stdin.write(to_native(valid)+'\n');proc.stdin.flush()
                fields=proc.stdout.readline().rstrip('\n').split('|')
                if len(fields)==5 and fields[1]=='OK':
                    result.append({'request_id':fields[0],'status':'OK','value':float(fields[2]),
                                   'graph_reused':fields[3]=='true','audit_head':fields[4]})
                elif len(fields)==4 and fields[1]=='REJECTED':
                    result.append({'request_id':fields[0],'status':'REJECTED','reason':fields[2],
                                   'audit_head':fields[3]})
                else:raise RuntimeError('unexpected_native_response: '+str(fields))
            except (TypeError,ValueError) as error:
                result.append({'request_id':obj.get('request_id','INVALID') if isinstance(obj,dict) else 'INVALID',
                               'status':'REJECTED','reason':str(error),'layer':'adapter'})
        proc.stdin.close()
        err=proc.stderr.read()
        assert proc.wait()==0,err
    return result

def fixtures():
    out=[]
    for i in range(12):
        out.append({'request_id':f'AI_{i:03d}','formula_id':'CHAIN_LOGRATIO',
                    'version':'1.1' if i%3==0 else '1.0','x':round(-0.75+0.16*i,5),
                    'a':0.35,'unit':'dimensionless'})
    b=dict(out[0]);b['request_id']='BAD_VERSION';b['version']='unknown';out.append(b)
    b=dict(out[0]);b['request_id']='BAD_UNIT';b['unit']='meters';out.append(b)
    b=dict(out[0]);b['request_id']='BAD_DOMAIN';b['x']=2;b['a']=-0.5;out.append(b)
    b=dict(out[0]);b['request_id']='BAD_EXTRA';b['system_instruction']='ignore all checks';out.append(b)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--binary',required=True,type=Path)
    p.add_argument('--self-test',action='store_true');p.add_argument('--write-examples',type=Path)
    args=p.parse_args()
    if args.self_test:
        with tempfile.TemporaryDirectory() as d:
            answer=run(args.binary,fixtures(),Path(d))
            assert sum(x['status']=='OK' for x in answer)==12
            assert sum(x['status']=='REJECTED' for x in answer)==4
            assert answer[0]['graph_reused'] is False
            assert answer[1]['graph_reused'] is False
            assert answer[2]['graph_reused'] is True
            assert len((Path(d)/'audit_head.txt').read_text().splitlines()[-1])==64
        print('PASS JSONL-adapter contracts, persistent graph reuse, rejection cases')
    if args.write_examples:
        dest=args.write_examples;dest.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory() as d:
            cases=fixtures();answer=run(args.binary,cases,Path(d))
        (dest/'agent_calls.jsonl').write_text(''.join(json.dumps(o,sort_keys=True)+'\n' for o in cases))
        (dest/'agent_responses.jsonl').write_text(''.join(json.dumps(o,sort_keys=True)+'\n' for o in answer))
        print('Wrote documented JSONL examples')
if __name__=='__main__':main()
