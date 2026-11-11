#!/usr/bin/env python3
"""Independent high-precision audit (110 decimal digits); no calls to paceval.

This intentionally uses Python's AST and mpmath, not the C++ parser or its
floating-point math operations. It never compiles or eval()s expression code.
The 110-digit calculations are reference computations; sampled TINC inclusion
is reported without converting it into an untested global interval guarantee.
"""
import argparse, ast, csv, json, math, operator, pathlib, collections
import mpmath as mp
mp.mp.dps=110
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
     ast.Div:operator.truediv,ast.Pow:operator.pow}
FUN={'sin':mp.sin,'cos':mp.cos,'exp':mp.exp,'ln':mp.log,'sqrt':mp.sqrt,'tanh':mp.tanh}

def compute(node,env):
    if isinstance(node,ast.Expression):return compute(node.body,env)
    if isinstance(node,ast.Constant) and type(node.value) in (float,int):
        return mp.mpf(str(node.value))
    if isinstance(node,ast.Name):
        if node.id not in env:raise ValueError('Unknown variable: '+node.id)
        return env[node.id]
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
        v=compute(node.operand,env)
        return -v if isinstance(node.op,ast.USub) else v
    if isinstance(node,ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](compute(node.left,env),compute(node.right,env))
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in FUN and len(node.args)==1 and not node.keywords:
        return FUN[node.func.id](compute(node.args[0],env))
    raise ValueError('Unsupported syntax in audit')

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--cases',default='../examples/expressions.csv')
    cli.add_argument('--sweep',default='../examples/sweep.csv')
    cli.add_argument('--results',default='../examples/evaluation.csv')
    cli.add_argument('--tinc',default='../examples/tinc_samples.csv')
    cli.add_argument('--summary',default=None)
    args=cli.parse_args()
    with open(args.cases,newline='') as f:cases={row['case_id']:row for row in csv.DictReader(f)}
    with open(args.sweep,newline='') as f:sweep={int(row['sample']):row for row in csv.DictReader(f)}
    parsed={k:ast.parse(r['expression'].replace('^','**'),mode='eval') for k,r in cases.items() if r['expected_status']=='OK'}
    n=0;failed=0;maxabs=mp.mpf(0);outliers=[];statuses=collections.Counter()
    with open(args.results,newline='') as f:
        for r in csv.DictReader(f):
            statuses[r['status']]+=1
            if r['status']!='OK':continue
            k=r['case_id'];vals=sweep[int(r['sample'])]
            env={name:mp.mpf(float(vals[name])) for name in ('x','y','t','k','w','c')}
            exact=compute(parsed[k],env)
            value=mp.mpf(float(r['paceval_result']))
            err=abs(exact-value);maxabs=max(maxabs,err)
            n+=1
            if not mp.isfinite(exact) or err>mp.mpf('3e-11')*(1+abs(exact)):
                failed+=1;outliers.append((k,r['sample'],float(err)))
    tinc_rows=0;tinc_included=0;tinc_excluded=[]
    with open(args.tinc,newline='') as f:
        for r in csv.DictReader(f):
            env={name:mp.mpf(float(r[name])) for name in ('x','y','t','k','w','c')}
            exact=compute(parsed[r['case_id']],env)
            lo,hi=mp.mpf(float(r['lower'])),mp.mpf(float(r['upper']))
            tinc_rows+=1
            if lo<=exact<=hi:tinc_included+=1
            else:tinc_excluded.append({'case_id':r['case_id'],'sample':int(r['sample']),
              'distance_from_interval':mp.nstr(max(lo-exact,exact-hi,0),8)})
    result={'working_digits':110,'checked':n,'numerical_tolerance_failures':failed,
      'max_absolute_error':mp.nstr(maxabs,10),'rejected_cases':sum(v for k,v in statuses.items() if k!='OK'),
      'tinc_samples':tinc_rows,'tinc_contained':tinc_included,'tinc_not_contained':tinc_excluded,
      'numeric_outliers':outliers[:20]}
    if args.summary:pathlib.Path(args.summary).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if (failed==0 and n==2560 and tinc_rows==30 and tinc_included==tinc_rows and result['rejected_cases']==40) else 1
if __name__=='__main__':raise SystemExit(main())
