#!/usr/bin/env python3
"""Conservative GitHub math-fence, bracket, local-link and negative-regression check."""
from pathlib import Path
import re,sys

def validate(s,path):
    stack=[];inside=False;inline=[]
    for line in s.splitlines():
      if line.strip().startswith('```'):
        if not inside:
          inside=line.strip()=='```math'
          if not inside and line.strip()!='```':continue
        else:inside=False
        continue
      if inside:
        if '$' in line or '\\operatorname' in line or '\\newcommand' in line or '\\def' in line or '\\[' in line or '\\]' in line:
            raise ValueError('Invalid math fence delimiter or command')
        for m in re.finditer(r'\\(begin|end)\{([A-Za-z]+)\}',line):
            if m.group(1)=='begin':stack.append(m.group(2))
            elif not stack or stack.pop()!=m.group(2):raise ValueError('Unbalanced LaTeX environment')
    if inside or stack:raise ValueError('Unclosed math fence/environment')
    if '\\operatorname{' in s:raise ValueError('Forbidden operatorname')
    for dest in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',s):
      if dest.startswith(('http:','https:','#','mailto:')):continue
      if not (path.parent/dest.split('#')[0]).exists():raise ValueError('Broken link '+dest)

def run(root):
    root=Path(root);s=(root/'README.md').read_text();validate(s,root/'README.md')
    for bad in ['```math\n$$x$$\n```','```math\n\\operatorname{route}(x)\n```']:
      try:validate(bad,root/'README.md')
      except ValueError:pass
      else:raise AssertionError('Negative regression case incorrectly passed')
    validate('```math\n\\mathrm{route}(x)=x^2\n```',root/'README.md')
    print('PASS: README math and local links; negative regression checks')
if __name__=='__main__':run(sys.argv[1])
