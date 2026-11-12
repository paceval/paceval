"""Reject known GitHub LaTex failures and verify relative link targets."""
import re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def validate(body):
    if re.search(r'\\(?:operatorname|begin\{(?:align|cases)\}|\[|\]|\(|\))',body):raise ValueError('unsupported/restricted inline or macro')
    blocks=re.findall(r'(?ms)^```math\s*\n(.*?)^```\s*$',body)
    if body.count('```math')!=len(blocks):raise ValueError('unclosed math fence')
    for block in blocks:
        if '$$' in block or '\\[' in block or '\\]' in block:raise ValueError('nested math delimiters')
        if block.count('{')!=block.count('}'):raise ValueError('unbalanced braces')
    for target in re.findall(r'\]\(([^)]+)\)',body):
        if target.startswith(('https:','http:','#','mailto:')):continue
        target=target.split('#',1)[0]
        if not (root/target).exists():raise ValueError('broken local link: '+target)
    return len(blocks)
if __name__=='__main__':
    for invalid in ['```math\n\\operatorname{x}\n```','```math\n$$ x $$\n```','```math\nx']:
        try:validate(invalid);raise AssertionError('negative test not rejected')
        except ValueError:pass
    assert validate('```math\nx=1\n```')==1
    n=validate((root/'README.md').read_text())
    print(f'PASS: {n} math blocks; math-regression and local link tests')
