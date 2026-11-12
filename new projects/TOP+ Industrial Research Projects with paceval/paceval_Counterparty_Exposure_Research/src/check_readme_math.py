#!/usr/bin/env python3
"""Fail closed on known GitHub math regressions and missing project links."""
import re,sys
from pathlib import Path
from urllib.parse import unquote
root=Path(__file__).resolve().parents[1]
def validate(src):
    errs=[]; in_math=False; math_count=0
    for line in src.splitlines():
        if re.match(r'^```math\s*$',line):in_math=True;math_count+=1;continue
        if line.strip()=='```' and in_math:in_math=False;continue
        if in_math:
            if '$$' in line or re.search(r'(?<!\\)\$',line):errs.append('nested dollar delimiters')
            if r'\operatorname' in line or r'\newcommand' in line or r'\def' in line:errs.append('unsupported/blocked macro')
            if r'\[' in line or r'\]' in line:errs.append('nested display delimiter')
    if in_math:errs.append('unclosed math fence')
    if r'\operatorname' in src:errs.append('blocked operatorname')
    for env in ('aligned','cases','bmatrix'):
        if src.count('\\begin{'+env+'}')!=src.count('\\end{'+env+'}'):errs.append('unbalanced '+env)
    return errs,math_count
readme=(root/'README.md').read_text();errors,count=validate(readme)
for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)|!\[[^]]*\]\(([^)]+)\)',readme):
    link=(target[0] or target[1]).split('#')[0]
    if not link or ':' in link or link.startswith('#'):continue
    if not (root/unquote(link)).exists():errors.append('missing link: '+link)
assert validate('```math\n\\operatorname{route}(x)\n```')[0]
assert validate('```math\n$$x$$\n```')[0]
assert not validate('```math\n\\mathrm{route}(x)=x\n```')[0]
if errors:print('FAIL',errors);sys.exit(1)
print('PASS: GitHub math regression tests; math blocks:',count,'; relative links validated')
