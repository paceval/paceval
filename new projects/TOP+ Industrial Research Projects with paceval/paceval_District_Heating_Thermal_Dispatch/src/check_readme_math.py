#!/usr/bin/env python3
"""Conservative structural GitHub Markdown math and local-link checker.
An actual GitHub preview is NOT implied by passing this check.
"""
import pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
BAD=r'\\(?:operatorname|newcommand|def)\b'
BEGIN=re.compile(r'\\(begin|end)\{([A-Za-z*]+)\}')
LINK=re.compile(r'!?\[[^\]]*\]\(([^)]+)\)')
def balanced_braces(s):
 count=0
 for ch in s:
  if ch=='{':count+=1
  elif ch=='}':
   count-=1
   if count<0:return False
 return count==0
def check(text,base):
 errs=[];fence=None;block=[];lines=text.splitlines()
 for ix,line in enumerate(lines,1):
  match=re.match(r'^\s*(`{3,}|~{3,})([a-zA-Z]*)\s*$',line)
  if match:
   marker=match.group(1)
   if fence is None:
    fence=(marker[0],len(marker),match.group(2).lower(),ix);block=[]
   elif marker[0]==fence[0] and len(marker)>=fence[1] and not match.group(2):
    if fence[2]=='math':
     data='\n'.join(block)
     if re.search(BAD,data):errs.append(f'line {fence[3]}: forbidden LaTeX macro')
     if '$' in data or '\\[' in data or '\\]' in data:errs.append(f'line {fence[3]}: nested math delimiters')
     if not balanced_braces(data):errs.append(f'line {fence[3]}: unbalanced braces')
     stack=[]
     for m in BEGIN.finditer(data):
      if m.group(1)=='begin':stack.append(m.group(2))
      elif not stack or stack.pop()!=m.group(2):errs.append(f'line {fence[3]}: incorrect environment nesting')
     if stack:errs.append(f'line {fence[3]}: unclosed math environment')
     if re.search(r'(?<!\\)\\(?!\\)(?:end|begin)\b(?!\{)',data):errs.append('malformed math begin/end')
    fence=None;block=[]
   else:block.append(line)
   continue
  if fence is not None:block.append(line);continue
  # Exclude inline code from the plain prose check.
  clean=re.sub(r'`[^`]*`','',line)
  if re.search(BAD,clean):errs.append(f'line {ix}: forbidden LaTeX command')
  if '\\[' in clean or '\\]' in clean or '\\(' in clean or '\\)' in clean:errs.append(f'line {ix}: non-GitHub math delimiter')
  clean=re.sub(r'\\\$','',clean)
  if clean.count('$')%2:errs.append(f'line {ix}: unmatched inline math dollar')
  for target in LINK.findall(line):
   target=target.split(' ')[0].split('#')[0]
   if not target or target.startswith(('http://','https://','mailto:','data:','#')):continue
   if not (base/target).exists():errs.append(f'line {ix}: broken relative link {target}')
 if fence is not None:errs.append('unterminated code/math fence')
 return errs
def selftest():
 base=ROOT
 cases=[('```math\n\\mathrm{route}(x) = x^2\n```',True),
        ('```math\n$$x^2$$\n```',False),
        ('```math\n\\operatorname{route}(x)\n```',False),
        ('```math\n\\begin{cases} x & x>0\\\\ y & x\\leq 0\\end{cases}\n```',True),
        ('```math\n\\begin{aligned} x\\end{cases}\n```',False),
        ('missing link: [x](not_existing_file_734.txt)',False)]
 for i,(sample,should_pass) in enumerate(cases):
  success=not check(sample,base)
  if success!=should_pass:raise SystemExit('Selftest '+str(i)+' wrong result '+str(check(sample,base)))
 print('Positive/negative math-and-link regression tests passed:',len(cases))
if __name__=='__main__':
 selftest()
 p=ROOT/'README.md';errors=check(p.read_text(encoding='utf-8'),ROOT)
 if errors:
  for e in errors:print('FAIL',e)
  raise SystemExit(1)
 print('README structural GitHub math and local link checks passed')
