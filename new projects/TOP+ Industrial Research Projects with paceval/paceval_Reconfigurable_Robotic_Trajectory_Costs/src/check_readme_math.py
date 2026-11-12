#!/usr/bin/env python3
"""Structural GitHub math/link linter with explicit positive/negative regressions."""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
def inspect(data):
 errors=[];inside=None;math=[];inline=[]
 for n,line in enumerate(data.splitlines(),1):
  fence=re.match(r'^\s*(```|~~~)([A-Za-z]*)\s*$',line)
  if fence:
   if inside is None:inside=(fence.group(1),fence.group(2),n);math=[]
   elif fence.group(1)==inside[0]:
    if inside[1]=='math':
     s='\n'.join(math)
     if re.search(r'(?<!\\)\$|\\\[|\\\]',s):errors.append('nested delimiter in math block')
     if any(c in s for c in ['\\operatorname','\\newcommand','\\def']):errors.append('unsupported macro in math block')
     stack=[]
     for token in re.finditer(r'\\(begin|end)\{([A-Za-z*]+)\}',s):
      kind,name=token.groups()
      if kind=='begin':stack.append(name)
      elif not stack or stack.pop()!=name:errors.append('unbalanced LaTex environment')
     if stack:errors.append('unclosed math environment')
    inside=None
   continue
  if inside:
   if inside[1]=='math':math.append(line)
   continue
  line=re.sub(r'`[^`]*`','',line)
  inline.append(line)
 if inside is not None:errors.append('unclosed fenced block')
 cleaned='\n'.join(inline)
 if '\\operatorname' in cleaned:errors.append('unsupported macro')
 if re.search(r'\\\(|\\\)|\\\[|\\\]',cleaned):errors.append('old GitHub math delimiters')
 # Dollar signs inside inline math are paired; ignores escaped dollar signs.
 for line in inline:
  if len(re.findall(r'(?<!\\)\$',line))%2:errors.append('unbalanced inline dollars')
 return errors

def check_links(data):
 missing=[]
 for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',data):
  path=target.split('#')[0].split('?')[0]
  if not path or re.match(r'(?i)^(https?://|mailto:)',path):continue
  if not (ROOT/path).exists():missing.append(path)
 return missing

def main():
 assert not inspect('```math\n\\mathrm{route}(g)=g\n```')
 assert inspect('```math\n\\operatorname{route}(g)=g\n```')
 assert inspect('```math\n$$ x^2 $$\n```')
 assert inspect('```math\n\\begin{cases}x&x>0\\end{aligned}\n```')
 data=(ROOT/'README.md').read_text(encoding='utf-8');errors=inspect(data);missing=check_links(data)
 if errors or missing:
  print('FAIL math:',errors,'missing links:',missing);return 1
 print('PASS GitHub structural math, four regression cases and',len(re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',data)),'local/remote markdown links; all local files exist')
 return 0
if __name__=='__main__':sys.exit(main())
