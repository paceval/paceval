#!/usr/bin/env python3
"""Conservative GitHub README math/link checker with positive/negative self-tests.
This is a structural lint, not a claim that GitHub's remote rendering was observed.
"""
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BAD=(r'\operatorname',r'\newcommand',r'\def')
def inspect(source,checklinks=False):
    problems=[];fenced=False;math=False;mathblocks=0;inlines=0
    envs=[]
    for lineno,line in enumerate(source.splitlines(),1):
        stripped=line.strip()
        if re.match(r'^(`{3,}|~{3,})',stripped):
            if not fenced:math=stripped.lstrip('`~').strip().split(' ')[0]=='math';fenced=True;mathblocks+=int(math)
            else:fenced=False;math=False
            continue
        if math:
            if any(b in line for b in BAD):problems.append((lineno,'forbidden macro'))
            if '$' in line or r'\[' in line or r'\]' in line:problems.append((lineno,'nested math delimiter'))
            for name in re.findall(r'\\begin\{(\w+)\}',line):envs.append(name)
            for name in re.findall(r'\\end\{(\w+)\}',line):
                if not envs or envs.pop()!=name:problems.append((lineno,'mismatched math environment'))
        elif not fenced:
            if any(b in line for b in BAD):problems.append((lineno,'forbidden macro'))
            if (r'\(' in line or r'\)' in line or r'\[' in line or r'\]' in line) and not stripped.startswith('`'):
                problems.append((lineno,'legacy math delimiter'))
            clean=re.sub(r'`[^`]*`','',line)
            # Count only likely mathematics; currency prose isn't a math formula.
            inlines+=len(re.findall(r'(?<!\\)\$[^$\n]{1,300}(?<!\\)\$',clean))
        if checklinks and not fenced:
            for path in re.findall(r'!?(?:\[[^\]]+\])\(([^)]+)\)',line):
                path=path.split('#',1)[0].split('?',1)[0]
                if not path or path.startswith(('http://','https://','mailto:','#')):continue
                if not (ROOT/path).exists():problems.append((lineno,'missing local file '+path))
    if fenced:problems.append((0,'unclosed Markdown code fence'))
    if envs:problems.append((0,'unclosed math environment'))
    return problems,mathblocks,inlines

def main():
    text=(ROOT/'README.md').read_text()
    tests=[('valid', '```math\n\\mathrm{route}(x)=\\begin{cases}1,&x>0\\\\0,&x\\leq0\\end{cases}\n```',True),
           ('operatorname', '```math\n\\operatorname{route}(x)\n```',False),
           ('nested fences', '```math\n$$ x^2 $$\n```',False),
           ('unbalanced environment', '```math\n\\begin{cases} x\n```',False)]
    for label,case,valid in tests:
        errors,*_=inspect(case)
        assert (not errors)==valid,f'regression failed: {label}'
    problems,blocks,inline=inspect(text,True)
    if problems:
        for line,msg in problems:print(f'FAIL line {line}: {msg}')
        return 1
    print(f'PASS GitHub math structure: {blocks} blocks, {inline} inline expressions, linked files present; positive/negative regressions passed')
    return 0
if __name__=='__main__':sys.exit(main())
