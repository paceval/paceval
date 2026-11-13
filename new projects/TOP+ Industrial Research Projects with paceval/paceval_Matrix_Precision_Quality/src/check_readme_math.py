#!/usr/bin/env python3
"""README syntax, math and local-link checker, including negative regressions."""
import pathlib,re,sys,urllib.parse
BAD_MACROS=(r'\operatorname',r'\newcommand',r'\def')
TAG=re.compile(r'\\(begin|end)\{([^{}]+)\}')
LINK=re.compile(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)')
class ReadmeIssue(Exception): pass

def check_math(content):
    fence=None;math_lines=[];text_lines=[]
    for ln,line in enumerate(content.splitlines(),1):
        z=re.match(r'^\s*(`{3,}|~{3,})(\w*)',line)
        if z:
            if fence is None:
                fence=(z.group(1)[0],len(z.group(1)),z.group(2).lower());math_lines=[]
            else:
                if z.group(1)[0]!=fence[0] or len(z.group(1))<fence[1]:raise ReadmeIssue('Mismatched code fence')
                if fence[2]=='math':
                    block='\n'.join(math_lines)
                    if '$' in block or '\\[' in block or '\\]' in block:raise ReadmeIssue('Nested math delimiters')
                    validate_environment(block)
                fence=None
            continue
        if fence is not None:
            if fence[2]=='math':math_lines.append(line)
            continue
        text_lines.append(line)
    if fence is not None:raise ReadmeIssue('Unclosed fence')
    joined='\n'.join(text_lines)
    # Inline spans and simple $...$ blocks are checked without interpreting code spans.
    joined=re.sub(r'`[^`\n]*`','',joined)
    if joined.count('$$')%2:raise ReadmeIssue('Unbalanced display math')
    joined=joined.replace('$$','')
    if joined.count('\\(')!=joined.count('\\)'):raise ReadmeIssue('Unbalanced inline math')
    validate_environment(joined)
    return True

def validate_environment(source):
    for bad in BAD_MACROS:
        if bad in source:raise ReadmeIssue('Disallowed macro '+bad)
    stack=[]
    for m in TAG.finditer(source):
        if m.group(1)=='begin':stack.append(m.group(2))
        elif not stack or stack.pop()!=m.group(2):raise ReadmeIssue('Unbalanced TeX environment')
    if stack:raise ReadmeIssue('Unclosed TeX environment')
    braces=re.sub(r'\\[{}]','',source)
    if braces.count('{')!=braces.count('}'):raise ReadmeIssue('Unbalanced braces')

def check_links(content,root):
    errors=[]
    for hit in LINK.findall(content):
        path=urllib.parse.unquote(hit.split('#')[0])
        if not path or re.match(r'^(?:https?://|mailto:)',path):continue
        if path.startswith('/') or not (root/path).exists():errors.append(hit)
    if errors:raise ReadmeIssue('Broken local markdown links: '+', '.join(errors))

def regressions():
    for bad in ['```math\n\\operatorname{route}\n```','```math\n$$x+y$$\n```','```math\n\\begin{matrix} a \\end{cases}\n```','```math\na+b']:
        try: check_math(bad)
        except ReadmeIssue:continue
        raise AssertionError('Checker accepted prohibited regression '+repr(bad))
    check_math('```math\n\\mathrm{route} = x + y\n```')
    check_math('```math\n\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}\n```')

if __name__=='__main__':
    root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]);content=(root/'README.md').read_text()
    try:regressions();check_math(content);check_links(content,root)
    except (ReadmeIssue,AssertionError) as e:print('FAIL:',e);sys.exit(1)
    print('PASS: README structural math, local links and positive/negative regression checks')
