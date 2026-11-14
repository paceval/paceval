#!/usr/bin/env python3
"""Archive-wide Markdown GitHub-math preflight, CommonMark parse and link check.
Checks EVERY .md in recursive output. Negative tests assert checker rejects errors.
"""
from pathlib import Path
import re,sys,tempfile
from urllib.parse import unquote,urlsplit
from markdown_it import MarkdownIt

def check(path):
 path=Path(path);files=list(sorted(path.rglob('*.md'))) if path.is_dir() else [path]
 if not files:raise ValueError('No markdown files found')
 links=0;blocks=0
 for md in files:
  data=md.read_text(encoding='utf8')
  parser=MarkdownIt('commonmark')
  tokens=parser.parse(data)
  if not any(t.type in ('heading_open','paragraph_open') for t in tokens):raise ValueError(f'No parsed markdown in {md}')
  # Remove properly parsed fenced code and inline code before math checks,
  # so source code examples may contain safe escapes without false alarms.
  pieces=[]; offset=0
  for token in tokens:
   if token.type=='fence':
    if token.info.strip().split(' ')[0]=='math':blocks+=1
    if token.info.strip().split(' ')[0]=='math' and ('$' in token.content or '\\(' in token.content or '\\[' in token.content):raise ValueError(f'Nested math delimiters in {md}')
  # Strip fenced code segments by line parser; preserve math fence presence.
  cleaned=[];infence=False
  for line in data.splitlines():
   f=re.match(r'^\s*(`{3,}|~{3,})(.*)$',line)
   if f:infence=not infence;continue
   if not infence:cleaned.append(line)
  if infence:raise ValueError(f'Unclosed code fence in {md}')
  stripped='\n'.join(cleaned)
  stripped=re.sub(r'`[^`\n]*`','',stripped)
  for pattern,label in [(r'\\\(',r'raw \\('),(r'\\\[',r'raw \\['),(r'\\operatorname\b','\\operatorname macro')]:
   if re.search(pattern,stripped):raise ValueError(f'{label} forbidden in {md}')
  if re.search(r'(?m)^\s*\$\$\s*$',stripped) and len(re.findall(r'(?m)^\s*\$\$\s*$',stripped))%2:raise ValueError(f'Unpaired display-math delimiters in {md}')
  if re.search(r'(?<!\\)\$\$.*\$\$',stripped):raise ValueError(f'Inline display math in {md}')
  for token in tokens:
   for child in [token]+list(token.children or []):
    if child.type not in ('link_open','image'):continue
    target=child.attrGet('href' if child.type=='link_open' else 'src')
    if not target:continue
    parts=urlsplit(target)
    if parts.scheme in ('http','https','mailto'):continue
    if parts.scheme or target.startswith('/') or target.startswith('file:'):
     raise ValueError(f'Unsafe local link target {target} in {md}')
    if parts.path and not (md.parent/unquote(parts.path)).is_file():raise ValueError(f'Broken relative link {target} in {md}')
    links+=1
 return {'files_checked':len(files),'local_links_checked':links,'math_fences':blocks,'status':'PASS'}

def selftest():
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'README.md';(Path(td)/'ok.png').write_bytes(b'foo')
  cases=['# Title\nWrong \\(x+y\\)\n','# Title\n\\operatorname{foo}\n','# Title\n$$\nabc\n','# Title\n```math\n$nested$\n```\n','# Title\n[bad](missing.csv)\n','# Title\n```python\nhello\n']
  # Last test is unclosed fence; preceding tests cover math, link errors.
  for case in cases:
   p.write_text(case,encoding='utf8')
   try:check(p)
   except ValueError:pass
   else:raise AssertionError('Markdown checker missed negative regression: '+repr(case))
  p.write_text('# Title\nInline $x+y$ and display:\n\n```math\nx^2+y^2\n```\n\n![ok](ok.png)\n',encoding='utf8')
  assert check(p)['status']=='PASS'
 print('ARCHIVE MARKDOWN NEGATIVE REGRESSION PASS')
if __name__=='__main__':
 if len(sys.argv)==2 and sys.argv[1]=='--selftest':selftest()
 elif len(sys.argv)==2:print('ARCHIVE MARKDOWN PASS',check(sys.argv[1]))
 else:raise SystemExit('Usage: check_markdown.py ROOT | --selftest')
