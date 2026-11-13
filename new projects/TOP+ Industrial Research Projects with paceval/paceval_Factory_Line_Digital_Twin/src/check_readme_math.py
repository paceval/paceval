#!/usr/bin/env python3
"""Static regression guard for GitHub Markdown math and relative local assets."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
s=(root/'README.md').read_text(encoding='utf-8')
assert s.count('```math')>=4
assert s.count('```math')==len(re.findall(r'(?m)^```$',s)) - len(re.findall(r'(?m)^```bash$',s)), 'Math fence imbalance'
assert r'\operatorname' not in s, 'GitHub unsupported operatorname macro'
assert '$$' not in s, 'Avoid double math delimiters mixed with fenced blocks'
for url in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)',s):
 link=next(v for v in url if v)
 if link.startswith(('http://','https://','mailto:','#')):continue
 assert (root/link).exists(), f'Broken local Markdown reference {link}'
print('README math and local links passed')
