#!/usr/bin/env python3
"""Static GitHub Markdown math/link checks with positive and negative regressions."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent.parent
text=(ROOT/'README.md').read_text()
def validate(s,check_links=True):
    math_start=len(re.findall(r'(?m)^```math\s*$',s))
    math_end=len(re.findall(r'(?m)^```\s*$',s))
    other_starts=len(re.findall(r'(?m)^```(?!math\s*$)[a-zA-Z0-9_-]+\s*$',s))
    assert math_start>=3,'Missing mathematical equations'
    assert math_start+other_starts==math_end,'Unbalanced code/math blocks'
    assert r'\operatorname' not in s, 'Unsupported GitHub math macro'
    assert '$$' not in s,'Use supported math fences instead of nested delimiter blocks'
    assert (chr(92)+'nabla') in s,'Expected Lie derivative not found'
    if check_links:
        for a,b in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)',s):
            link=a or b
            if link.startswith(('https://','http://','mailto:','#')):continue
            assert (ROOT/link).exists(),f'Broken local Markdown link: {link}'
validate(text,check_links=True)
for marker in (r'\operatorname{foo}', '$$ x $$', '```math\n1+2\n'):
    try:validate(text+'\n'+marker,check_links=False)
    except AssertionError:pass
    else:raise RuntimeError('negative regression unexpectedly accepted')
print('GitHub README math and local link checks passed (+3 negative tests)')
