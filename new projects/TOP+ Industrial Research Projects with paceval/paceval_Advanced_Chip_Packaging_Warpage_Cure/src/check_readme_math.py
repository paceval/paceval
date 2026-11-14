#!/usr/bin/env python3
"""GitHub-oriented Markdown/math/relative-link structural QA with negative tests.
No claim of real GitHub rendering is made by this static checker.
"""
import re,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
RE_LINK=re.compile(r'!?\[[^\]]*\]\(([^)]+)\)')
RE_BEGIN=re.compile(r'\\(begin|end)\{([A-Za-z*]+)\}')
BANNED=('\\operatorname','\\newcommand','\\def','\\require')

def mathcheck(expr,issues):
    for bad in BANNED:
        if bad in expr:issues.append(f'Disallowed GitHub math command: {bad}')
    depth=0;esc=False
    for ch in expr:
        if esc:esc=False;continue
        if ch=='\\':esc=True;continue
        if ch=='{':depth+=1
        if ch=='}':depth-=1
        if depth<0:issues.append('Unmatched closing brace');break
    if depth:issues.append('Unbalanced math braces')
    stack=[]
    for how,env in RE_BEGIN.findall(expr):
        if how=='begin':stack.append(env)
        elif not stack or stack.pop()!=env:issues.append('Mismatched math environment: '+env)
    if stack:issues.append('Unclosed math environment: '+str(stack))

def check(md,root=BASE,check_links=True):
    problems=[];code=False;lang='';inline='';math=[]
    lines=md.splitlines()
    for no,line in enumerate(lines,1):
        marker=re.match(r'^\s*(`{3,}|~{3,})([^`]*)$',line)
        if marker:
            fence=marker.group(1);rest=marker.group(2).strip()
            if not code:
                code=True;lang=rest.lower();math=[];inline=fence[0]
            else:
                if lang=='math':
                    content='\n'.join(math)
                    if '$' in content or '\\[' in content or '\\]' in content or '\\(' in content or '\\)' in content:problems.append(f'line {no}: nested math delimiters')
                    mathcheck(content,problems)
                code=False;lang='';math=[];inline=''
            continue
        if code:
            if lang=='math':math.append(line)
            continue
        # Inline code segments are text, never inline math.
        plain=re.sub(r'`[^`]*`','',line)
        if '\\[' in plain or '\\]' in plain or '\\(' in plain or '\\)' in plain:
            problems.append(f'line {no}: old LaTex delimiters outside code fences')
        plain=re.sub(r'\\\$','',plain)
        if plain.count('$')%2:problems.append(f'line {no}: unmatched inline dollar')
        for match in re.finditer(r'(?<!\$)\$([^$]+)\$(?!\$)',plain):mathcheck(match.group(1),problems)
        if check_links:
            for link in RE_LINK.findall(line):
                link=link.split('#')[0].strip().replace('%20',' ')
                if not link or link.startswith(('https://','http://','mailto:','data:','#')):continue
                if not (root/link).exists():problems.append(f'line {no}: missing local linked path: {link}')
    if code:problems.append('Unclosed code fence')
    return problems

def selftest():
    passed='''# Example\n\n```math\n\\mathrm{route}(x)=\\begin{cases}1,&x>0,\\\\0,&x\\leq0\\end{cases}\n```\n\n$C=2$.\n'''
    for title,data in [
       ('macro','```math\n\\operatorname{route}(x)\n```'),
       ('nested delimiter','```math\n$$ x+1 $$\n```'),
       ('unbalanced math','```math\n\\begin{cases} a \\end{matrix}\n```'),
       ('unmatched inline','A single $E=mc^2 end.'),
       ('unclosed fence','```math\nx+1'),
       ('missing link','[missing](figures/do_not_create.png)')]:
        assert check(data),f'Negative case wrongly accepted: {title}'
    assert not check(passed),f'Valid math rejected: {check(passed)}'
    print('README CHECKER REGRESSION PASS: five math negatives, missing-link negative, valid math positive')

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--selftest':selftest();return 0
    file=Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'README.md'
    problems=check(file.read_text('utf-8'),file.parent)
    if problems:
        print('README VALIDATION FAILED:')
        for p in problems:print('  '+p)
        return 1
    print('README VALIDATION PASS: code fences, math structure, excluded macros and local links')
    return 0
if __name__=='__main__':raise SystemExit(main())
