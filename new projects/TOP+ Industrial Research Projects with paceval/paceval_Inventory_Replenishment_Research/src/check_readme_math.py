#!/usr/bin/env python3
"""Validate common GitHub MathJax delimiter mistakes and local Markdown links.

This is a structural check, not a complete LaTeX renderer or Markdown parser.
"""
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]
content=(root/'README.md').read_text(encoding='utf-8')
errors=[]
for label,pat in [('non-GitHub display delimiter',r'\\\[|\\\]'),('non-GitHub inline delimiter',r'\\\(|\\\)')]:
 if re.search(pat,content):errors.append(label)
blocks=re.findall(r'^```math\s*\n(.*?)^```\s*$',content,re.S|re.M)
for i,b in enumerate(blocks,1):
 if b.count('{')!=b.count('}'):errors.append(f'math block {i}: unbalanced braces')
# Avoid matching inline LaTeX commands as link syntax.
links=re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)',content)
local=[]
for a,b in links:
 url=(a or b).split('#',1)[0]
 if url and not re.match(r'(?i)^[a-z]+://',url) and not url.startswith('#'):
  local.append(url)
  if not (root/url).is_file():errors.append(f'missing local link: {url}')
print(f'GitHub math blocks: {len(blocks)}; local file references: {len(local)}')
if errors:
 print('FAIL:',*errors,sep='\n - ');sys.exit(1)
print('PASS: structural math delimiters and local file links')
