#!/usr/bin/env python3
"""Strict GitHub Markdown math and local-link preflight (including regressions)."""
import re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def check(s):
    assert s.count('```math')>=5,'Too few mathematical blocks'
    blocks=re.findall(r'```math\n(.*?)\n```',s,re.S)
    assert len(blocks)==s.count('```math'),'Malformed Markdown math fence'
    for b in blocks:
        assert '$$' not in b and '\\operatorname' not in b and '\\begin{cases}' not in b,'Unsupported GitHub MathJax notation'
        assert b.count('{')==b.count('}'),'Unbalanced math braces'
        assert len(b.strip())>15,'Empty math expression'
    assert s.count('```') == 2*(s.count('```math')+s.count('```bash')),'Unmatched fenced code block'
    for m in re.finditer(r'!?\[[^\]]+\]\(([^)]+)\)',s):
        url=m.group(1).split('#')[0].strip()
        if not url or url.startswith(('https://','http://','mailto:')):continue
        assert not url.startswith('/'),'Link must be repository relative'
        assert (R/url).exists(),f'Missing link {url}'
    return len(blocks),len(list(re.finditer(r'!?\[[^\]]+\]\(([^)]+)\)',s)))
s=(R/'README.md').read_text(encoding='utf-8');a,b=check(s)
for faulty in ('\\operatorname{route}','$$','\\begin{cases}'):
    altered=s.replace('```math\n','```math\n'+faulty,1)
    try:check(altered)
    except AssertionError:pass
    else:raise AssertionError('Regression checker failed to reject '+faulty)
print(f'PASS {a} GitHub mathematical blocks and {b} Markdown links; negative regression tests passed')
