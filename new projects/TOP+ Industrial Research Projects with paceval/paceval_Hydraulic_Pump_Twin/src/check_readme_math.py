#!/usr/bin/env python3
"""Regression guard for GitHub math and local linked repository artifacts."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'README.md').read_text()
assert len(re.findall(r'^```math\s*$',text,flags=re.M))==len(re.findall(r'^```\s*$',text,flags=re.M)) - len(re.findall(r'^```(?:bash|sh|python|cpp).*$',text,flags=re.M)), 'Math/code fences unbalanced'
assert text.count('```')%2==0,'Odd number of fenced delimiters'
assert '\\operatorname' not in text,'GitHub KaTeX prohibited macro'
assert not re.search(r'\$\$\s*```math|```math\s*\$\$',text),'Nested math boundaries'
links=re.findall(r'\]\(([^)]+)\)',text);local=[]
for url in links:
 if url.startswith(('http://','https://','#','mailto:')):continue
 path=(ROOT/url.split('#',1)[0]);assert path.exists(),f'Broken local reference: {url}';local.append(url)
assert len(local)>25,local
(ROOT/'results/readme_validation.txt').write_text(f'GitHub Markdown static regression: PASS; local links checked: {len(local)}; math blocks: {text.count("```math")}\n')
print('README validation pass, local refs:',len(local))
