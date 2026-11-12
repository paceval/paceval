#!/usr/bin/env python3
"""Check GitHub Markdown math and local links. Includes failing and passing regression cases."""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
def inspect(md,check_links=False):
 errors=[]; in_fence=False;math=False;maths=[]; codecount=0
 for line in md.splitlines():
  match=re.match(r'^\s*(`{3,}|~{3,})([^`]*)$',line)
  if match:
   if not in_fence:
    in_fence=True;math=(match.group(2).strip()=='math');opening=match.group(1)[0];length=len(match.group(1));buf=[]
   elif match.group(1)[0]==opening and len(match.group(1))>=length:
    if math:maths.append('\n'.join(buf))
    in_fence=False;math=False
   continue
  if in_fence:
   if math:buf.append(line)
  else:
   if re.search(r'\\operatorname\b|\\newcommand\b|\\def\b',line):errors.append('forbidden macro')
   if any(x in line for x in ('\\[','\\]','\\(','\\)')):errors.append('legacy delimiter')
 if in_fence:errors.append('unclosed code fence')
 for m in maths:
  if '$$' in m or '\\[' in m or '\\]' in m:errors.append('nested math delimiter')
  if re.search(r'\\operatorname\b|\\newcommand\b|\\def\b',m):errors.append('forbidden macro')
  stack=[]
  for typ,env in re.findall(r'\\(begin|end)\{([A-Za-z*]+)\}',m):
   if typ=='begin':stack.append(env)
   elif not stack or stack.pop()!=env:errors.append('unbalanced environment')
  if stack:errors.append('unbalanced environment')
 if check_links:
  for url in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md):
   path=url.split('#')[0].strip('<>')
   if path and not re.match(r'\w+://|mailto:',path) and not (ROOT/path).exists():errors.append('missing '+path)
 return errors,len(maths)
if __name__=='__main__':
 md=(ROOT/'README.md').read_text()
 errors,number=inspect(md,True)
 for bad in ['```math\n\\operatorname{route}(g)\n```','```math\n$$x+1$$\n```','```math\n\\begin{cases} x \\end{aligned}\n```']:
  if not inspect(bad)[0]:errors.append('negative regression failure')
 if inspect('```math\n\\mathrm{route}(g)=x\n```')[0]:errors.append('positive regression failure')
 print('Math blocks:',number,'Local links:',len(re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md)))
 print('PASS: math and regression checks' if not errors else 'FAIL: '+str(errors))
 sys.exit(bool(errors))
