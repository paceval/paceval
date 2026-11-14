#!/usr/bin/env python3
"""Conservative structural GitHub math and link checks with negative regression tests."""
import re,sys
from pathlib import Path

def check_text(txt):
    for bad in ['\\operatorname','\\newcommand','\\def','\\[','\\]','\\(','\\)']:
        if bad in txt:raise ValueError('Unsupported math command or delimiter: '+bad)
    lines=txt.splitlines();in_fence=False;fence_math=False;math=[]
    for ln in lines:
        s=ln.strip()
        if s.startswith('```'):
            if not in_fence:in_fence=True;fence_math=s=='```math';math=[]
            else:
                if fence_math:
                    contents='\n'.join(math)
                    if '$' in contents:raise ValueError('Nested dollar delimiter inside math fence')
                    if contents.count('\\begin{')!=contents.count('\\end{'):raise ValueError('Unbalanced math environments')
                    stack=[]
                    for typ,name in re.findall(r'\\(begin|end)\{([^{}]+)\}',contents):
                        if typ=='begin':stack.append(name)
                        elif not stack or stack.pop()!=name:raise ValueError('Improper math environment nesting')
                    if stack:raise ValueError('Missing math end delimiter')
                in_fence=False;fence_math=False
            continue
        if in_fence:
            if fence_math:math.append(ln)
            continue
        # Code spans are excluded from inline delimiter checks.
        ln=re.sub(r'`[^`]*`','',ln)
        ln=re.sub(r'\\\$','',ln)
        if ln.count('$')%2:raise ValueError('Unbalanced inline math delimiter: '+ln)
    if in_fence:raise ValueError('Unclosed markdown code fence')

def check_links(text,root):
    for path in re.findall(r'!?(?:\[[^\]]*\])\(([^)]+)\)',text):
        if path.startswith(('http://','https://','mailto:','#')):continue
        path=path.split('#',1)[0].replace('%20',' ')
        if path and not (root/path).is_file():raise ValueError('Missing linked project file: '+path)

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--self-test':
        for bad in ['```math\n$$x$$\n```','```math\n\\operatorname{route}(x)\n```',
                    '```math\n\\begin{cases}a\\end{aligned}\n```']:
            try:check_text(bad);raise AssertionError('Negative case incorrectly accepted')
            except ValueError:pass
        check_text('```math\n\\mathrm{route}(x)=x+1\n```')
        print('PASS: negative / positive GitHub math regression cases');return
    src=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent.parent/'README.md')
    text=src.read_text(encoding='utf8');check_text(text);check_links(text,src.parent)
    print('PASS: GitHub math fences, conservative LaTeX syntax and all local paths')
if __name__=='__main__':main()
