#!/usr/bin/env python3
"""Conservative GitHub Markdown/math sanity test with positive and negative regression cases."""
import re,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
def validate(text):
    fences=re.findall(r'^```(\w*)\s*$',text,re.M)
    assert len(fences)%2==0,'Unpaired fences'
    blocks=re.findall(r'^```math\s*\n(.*?)^```\s*$',text,re.M|re.S)
    for b in blocks:
        assert not re.search(r'\$\$|\\\[|\\\]|\\operatorname|\\newcommand|\\def',b),'Disallowed nested math or macro'
        pairs=re.findall(r'\\(begin|end)\{([^{}]+)\}',b)
        stack=[]
        for what,name in pairs:
            if what=='begin':stack.append(name)
            else:
                assert stack and stack.pop()==name,'Unmatched LaTeX environment'
        assert not stack,'Unclosed LaTeX environment'
        assert b.count('{')==b.count('}'),'Unbalanced math braces'
    assert '\\operatorname' not in text,'Unsupported GitHub macro'
    assert not re.search(r'^\$\$\s*$',text,re.M),'Use single math fence'
    return True
text=(root/'README.md').read_text()
validate(text)
for m in re.finditer(r'!?\[[^]]*\]\(([^)]+)\)',text):
    dest=m.group(1).split('#')[0].strip().split(' ')[0]
    if not dest or re.match(r'^(https?://|mailto:)',dest):continue
    assert (root/dest).exists(),f'Broken local link {dest}'
for bad in ('```math\n\\operatorname{route}(x)\n```','```math\n$$ x^2 $$\n```'):
    try:validate(bad);raise AssertionError('Negative regression incorrectly accepted')
    except AssertionError as e:
        if 'incorrectly accepted' in str(e):raise
assert validate('```math\n\\mathrm{route}(x)=x^2\n```')
print('PASS README formulas, relative links and positive/negative regressions')
