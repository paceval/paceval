#!/usr/bin/env python3
"""Static GitHub README mathematics and local-link regression checks."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
s=(root/'README.md').read_text(encoding='utf-8')
errors=[]
fences=re.findall(r'^```(\w*)\s*$',s,re.M)
assert fences.count('math')>=5,'expected multiple GitHub math blocks'
assert len(fences)%2==0,'unclosed Markdown code fence'
forbidden=['\\operatorname','\\begin{aligned}','\\end{aligned}']
for t in forbidden:
 if t in s:errors.append('forbidden GitHub math macro: '+t)
maths=re.findall(r'^```math\n(.*?)\n```',s,re.M|re.S)
for i,m in enumerate(maths):
 if m.count('{')!=m.count('}'):errors.append(f'unbalanced math braces in block {i}')
 if '$$' in m or r'\[' in m or r'\]' in m:errors.append(f'embedded math delimiters in block {i}')
 for term in ['\\frac','\\exp','\\sin','\\sqrt']:
  if term in m and not re.search(r'\\'+term[1:],m):errors.append('possible malformed command')
for href in re.findall(r'!?\[[^\]]+\]\(([^)]+)\)',s):
 if href.startswith(('https://','http://','mailto:','#')):continue
 p=(root/href.split('#')[0]).resolve()
 if not p.exists():errors.append('missing README file: '+href)
assert not errors,'\n'.join(errors)
links=re.findall(r'!?\[[^\]]+\]\(([^)]+)\)',s)
print(f'GitHub math/link check passed: {len(maths)} math blocks, {len(links)} links')
