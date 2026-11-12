#!/usr/bin/env python3
"""Static GitHub math/link checker with negative and positive regression tests."""
import re,sys
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parent.parent
BAD=re.compile(r'\\(?:operatorname|newcommand|def)\b')
ENV=re.compile(r'\\(begin|end)\{([A-Za-z*]+)\}')
LINK=re.compile(r'!?(?:\[[^]]*\])\(([^)]+)\)')

def check(text,resolve=False):
 errors=[];blocks=[];inline=[];openf=False;code=False; math=False;buf=[]
 for line in text.splitlines():
  stripped=line.strip()
  if stripped.startswith('```') or stripped.startswith('~~~'):
   prefix=stripped[:3]
   if not openf:
    openf=True;code=True;math=(stripped[3:].strip()=='math');buf=[]
   else:
    if math:blocks.append('\n'.join(buf))
    openf=False;code=False;math=False
   continue
  if math:buf.append(line)
  elif not code:
   # Remove literal inline code, then inspect mathematical delimiters.
   clean=re.sub(r'`[^`]*`','',line)
   if re.search(r'(?<!\\)\\[\[\]()]',clean):errors.append('non-GitHub legacy math delimiter')
   fragments=re.findall(r'(?<!\\)\$([^$]+)(?<!\\)\$',clean)
   inline.extend(fragments)
   if clean.count('$')%2:errors.append('unbalanced inline dollar delimiter')
 if openf:errors.append('unterminated fenced code block')
 for s in blocks+inline:
  if BAD.search(s):errors.append('disallowed TeX macro')
  if '$' in s or re.search(r'\\[\[\]]',s):errors.append('nested math delimiter')
  stack=[]
  for typ,env in ENV.findall(s):
   if typ=='begin':stack.append(env)
   elif not stack or stack.pop()!=env:errors.append('unmatched TeX environment')
  if stack:errors.append('unclosed TeX environment')
  if s.count('{')!=s.count('}'):errors.append('unbalanced TeX braces')
 if resolve:
  for dest in LINK.findall(text):
   dest=unquote(dest.split('#')[0].strip().split(' ')[0])
   if not dest or '://' in dest or dest.startswith(('mailto:','#')):continue
   if not (ROOT/dest).exists():errors.append('missing local link: '+dest)
 return errors,len(blocks),len(inline)

def regression():
 good='''## T\n```math\n\\mathrm{route}(x)=\\begin{cases}1,&x>0,\\\\0,&x<=0\\end{cases}\n```'''
 bad1='```math\n\\operatorname{route}(x)\n```'
 bad2='```math\n$$x^2$$\n```'
 assert not check(good)[0]
 assert check(bad1)[0] and check(bad2)[0]
 print('PASS positive and negative math regression cases')
if __name__=='__main__':
 regression();e,n,m=check((ROOT/'README.md').read_text(encoding='utf-8'),True)
 for error in e:print('FAIL',error)
 print('math blocks:',n,'inline:',m,'local links checked')
 sys.exit(bool(e))
