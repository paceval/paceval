"""Fail-closed GitHub Markdown math and local-link linter with regression tests.
This is structural validation, not browser/GitHub visual rendering.
"""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
def verify(text,links=True):
    problems=[]
    if r'\operatorname' in text:problems.append('unsupported operatorname macro')
    if any(x in text for x in [r'\[',r'\]',r'\(',r'\)']):problems.append('legacy math delimiters')
    blocks=re.findall(r'(?m)^```math\s*\n([\s\S]*?)^```\s*$',text)
    open_count=len(re.findall(r'(?m)^```math\s*$',text))
    if open_count!=len(blocks):problems.append('unclosed math blocks')
    for b in blocks:
        if '$$' in b or '```' in b:problems.append('nested math delimiter')
        if b.count('{')!=b.count('}'):problems.append('imbalanced LaTeX braces')
        if r'\begin{' in b and b.count(r'\begin{')!=b.count(r'\end{'):problems.append('unbalanced LaTeX environment')
    if links:
        for dest in re.findall(r'\]\(([^)]+)\)',text):
            dest=dest.split('#')[0].replace('%20',' ')
            if dest and not re.match(r'^[a-zA-Z]+://',dest) and not (ROOT/dest).exists():problems.append('missing local link '+dest)
    return problems,len(blocks),len(re.findall(r'\]\(([^)]+)\)',text))
def test_cases():
    assert not verify('```math\nx=\\frac{1}{2}\n```',False)[0]
    for bad in [r'```math'+'\n'+r'\operatorname{route}(x)'+'\n```','```math\n$$x=1$$\n```','```math\nx=\\frac{1}{2}\n']:
        assert verify(bad,False)[0],bad
    assert verify('[missing](figures/nothing_here.png)',True)[0]
if __name__=='__main__':
    test_cases();text=(ROOT/'README.md').read_text()
    errors,n,links=verify(text)
    if errors:
        for err in errors:print('FAIL',err)
        sys.exit(1)
    print(f'PASS GitHub math and links; {n} checked math blocks; {links} URL references; regression tests passed')
