#!/usr/bin/env python3
"""GitHub README math/links structural preflight, including regression tests.
This is NOT a visual render test. Use GitHub preview for final rendering QA.
"""
from __future__ import annotations
import argparse,re,sys
from pathlib import Path
FORBIDDEN=[r'\operatorname',r'\newcommand',r'\def',r'\DeclareMathOperator']
ENV_RE=re.compile(r'\\(begin|end)\{([A-Za-z*]+)\}')
LINK_RE=re.compile(r'!?\[[^\]]*\]\(([^)]*)\)')

def validate_math(expr:str,where:str):
 errors=[];stack=[]
 for t in FORBIDDEN:
  if t in expr:errors.append(f'{where}: disallowed LaTeX macro {t}')
 if expr.count('{')!=expr.count('}'):errors.append(f'{where}: mismatched braces')
 for action,name in ENV_RE.findall(expr):
  if action=='begin':stack.append(name)
  elif not stack or stack.pop()!=name:errors.append(f'{where}: unpaired environment {name}')
 if stack:errors.append(f'{where}: unterminated environments {stack}')
 if re.search(r'(?<!\\)\\\\\\\\',expr):errors.append(f'{where}: possible invalid four-backslash sequence')
 return errors

def check(content:str,root:Path,links=True):
 errors=[];fence=False;mathfence=False;context=[]
 for n,line in enumerate(content.splitlines(),1):
  stripped=line.strip()
  if stripped.startswith('```'):
   tag=stripped[3:].strip()
   if not fence:
    fence=True;mathfence=(tag=='math');context=[]
   else:
    if mathfence:
     body='\n'.join(context)
     if '$' in body or r'\[' in body or r'\]' in body:errors.append(f'math fence line {n}: nested dollar/block delimiters')
     errors+=validate_math(body,f'math block through line {n}')
    fence=False;mathfence=False
   continue
  if fence:
   if mathfence:context.append(line)
   continue
  # Skip inline code spans and literal backticks.
  parts=re.split(r'(`+[^`]*`+)',line)
  for j,part in enumerate(parts):
   if j%2:continue
   # Bare escaped dollar signs are not math delimiters.
   marks=[m.start() for m in re.finditer(r'(?<!\\)\$',part)]
   if len(marks)%2:errors.append(f'line {n}: odd number of inline math delimiters')
   for a,b in zip(marks[::2],marks[1::2]):errors+=validate_math(part[a+1:b],f'inline math line {n}')
   if r'\(' in part or r'\)' in part or r'\[' in part or r'\]' in part:errors.append(f'line {n}: unsupported Markdown math delimiters')
  if links:
   for m in LINK_RE.finditer(line):
    target=m.group(1).strip().split(' ',1)[0].strip('<>')
    if not target or target.startswith(('http://','https://','mailto:','#','data:')):continue
    rel=target.split('#')[0].split('?')[0].replace('%20',' ')
    if not (root/rel).exists():errors.append(f'line {n}: missing local linked file: {rel}')
 if fence:errors.append('Unclosed code fence')
 return errors

def regression():
 good='```math\n\\mathrm{route}(g)=\\begin{cases}1,&g>0,\\\\0,&g\\leq0\\end{cases}\n```'
 bad1='```math\n\\operatorname{route}(g)\n```'
 bad2='```math\n$$x^2$$\n```'
 bad3='Price $10 and price $20 are not intended equations.' # not required to accept if content ambiguous
 assert not check(good,Path('.'),False)
 assert check(bad1,Path('.'),False)
 assert check(bad2,Path('.'),False)
 print('POSITIVE/NEGATIVE math regressions PASS')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--readme',type=Path,default=Path(__file__).resolve().parents[1]/'README.md');a=p.parse_args()
 regression();s=a.readme.read_text();issues=check(s,a.readme.parent)
 if issues:
  for issue in issues:print('ERROR:',issue,file=sys.stderr)
  sys.exit(2)
 print('README mathematical structure and local links PASS; visual GitHub rendering NOT checked')
