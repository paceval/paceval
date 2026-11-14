#!/usr/bin/env python3
"""Markdown-it CommonMark parse plus actual local-link + math-contract QA.

Strict enough to reject invalid local targets and common malformed link/fence
syntax, with separate negative tests to ensure the checker is active.
"""
from pathlib import Path
import re,sys,tempfile
from urllib.parse import urlsplit,unquote
from markdown_it import MarkdownIt

def check(source):
 path=Path(source);data=path.read_text(encoding='utf8')
 if data.count('```')%2:raise ValueError('Unclosed fenced code block')
 parser=MarkdownIt('commonmark');tokens=parser.parse(data)
 if not any(t.type=='heading_open' for t in tokens):raise ValueError('Missing Markdown structure')
 if '## 1. Industrial use case and current state of the art' not in data:raise ValueError('Missing required industrial introduction')
 for term in ['E_next','Ppv','eta_ch','STEP_FEASIBILITY','69 / 69']:
  if term not in data:raise ValueError('Missing mathematical model marker '+term)
 links=0
 for token in tokens:
  stack=[token]+(token.children or [])
  for child in stack:
   if child.type in ('link_open','image'):
    target=child.attrGet('href') if child.type=='link_open' else child.attrGet('src')
    if target is None:continue
    parsed=urlsplit(target)
    if parsed.scheme in ('http','https','mailto'):continue
    if parsed.scheme or target.startswith('/') or target.startswith('file:'):raise ValueError('Unsafe/non-relative target: '+target)
    filepath=path.parent/unquote(parsed.path)
    if not filepath.is_file():raise ValueError('Missing local link target: '+target)
    links+=1
 if links<8:raise ValueError('Too few verified local resource links')
 return links
if __name__=='__main__':
 if len(sys.argv)==2 and sys.argv[1]=='--selftest':
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);p=root/'README.md';sample='## 1. Industrial use case and current state of the art\nE_next Ppv eta_ch STEP_FEASIBILITY 69 / 69\n'
   p.write_text(sample+'![x](missing.png)\n'+'\n'.join(f'[local]({i}.png)' for i in range(9)),encoding='utf8')
   try:check(p)
   except ValueError:pass
   else:raise AssertionError('Broken target negative test failed')
   for i in range(9):(root/f'{i}.png').write_bytes(b'a')
   p.write_text(sample+'![x](0.png)\n'+'\n'.join(f'[local]({i}.png)' for i in range(9))+'\n```broken',encoding='utf8')
   try:check(p)
   except ValueError:pass
   else:raise AssertionError('Unclosed code negative test failed')
  print('README checker negative tests PASS')
 elif len(sys.argv)==2:
  print('README CommonMark and local link PASS:',check(sys.argv[1]),'valid local targets')
 else:raise SystemExit('Usage: check_readme_math.py README.md | --selftest')
