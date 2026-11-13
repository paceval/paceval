"""README math and links preflight with positive/negative regression checks.
This is not a GitHub rendering engine.
"""
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]
def verify(s,links=True):
    errs=[];in_fence=False;math=False;body=[];outside=[]
    for line in s.splitlines():
        if line.startswith('```'):
            if not in_fence:in_fence=True;math=line[3:].strip()=='math';body=[]
            else:
                if math:
                    inside='\n'.join(body)
                    if '$$' in inside or '\\[' in inside or '\\]' in inside:errs.append('nested math delimiters')
                    if re.search(r'\\(?:operatorname|newcommand|def)\b',inside):errs.append('forbidden math macro')
                    starts=re.findall(r'\\begin\{([^}]+)\}',inside);ends=re.findall(r'\\end\{([^}]+)\}',inside)
                    if starts!=ends[::-1] and starts!=ends:errs.append('unbalanced math environments')
                    if inside.count('{')!=inside.count('}'):errs.append('unbalanced braces')
                in_fence=False;math=False
            continue
        if in_fence:
            if math:body.append(line)
        else:outside.append(line)
    if in_fence:errs.append('unclosed code fence')
    outer='\n'.join(outside)
    if any(t in outer for t in ('\\[','\\]','\\(','\\)')):errs.append('legacy math delimiters')
    if re.search(r'\\(?:operatorname|newcommand|def)\b',outer):errs.append('forbidden inline macro')
    if links:
        for dest in re.findall(r'!?(?:\[[^\]]*\])\(([^)]+)\)',outer):
            dest=dest.split('#')[0].strip()
            if dest and not (dest.startswith(('http://','https://','mailto:','#')) or (root/dest).exists()):errs.append('missing local target '+dest)
    return errs
assert verify('```math\n\\mathrm{route}(x)=x\n```',False)==[]
assert verify('```math\n\\operatorname{route}(x)=x\n```',False)
assert verify('```math\n$$x$$\n```',False)
issues=verify((root/'README.md').read_text())
if issues:
 print('FAIL:',issues);sys.exit(1)
print('PASS README math structural preflight + positive/negative regression tests + local links')
