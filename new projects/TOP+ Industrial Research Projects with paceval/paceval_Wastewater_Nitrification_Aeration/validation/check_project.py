#!/usr/bin/env python3
"""Archive-wide markdown math and relative-link preflight with negative regressions."""
from pathlib import Path
import re,sys,json
from markdown_it import MarkdownIt
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
parser=MarkdownIt('commonmark',{'html':False}).enable('table')

def validate_markdown(content,path):
    issues=[]
    # Removing code fences prevents the shell and programming examples from
    # being mistaken for publication math. Incorrect math outside fences fails.
    clean=re.sub(r'(?ms)^\s*```[^\n]*\n.*?^\s*```\s*$', '',content)
    clean=re.sub(r'`[^`\n]*`','',clean)
    for symbol in ('\\(', '\\)', '\\[', '\\]', '\\operatorname'):
        if symbol in clean:issues.append('unsupported/raw math token '+symbol)
    # A display math block uses a $$ delimiter on its own line.
    display=[i for i,line in enumerate(clean.splitlines(),1) if line.strip()=='$$']
    if len(display)%2:issues.append('unpaired display $$ delimiters')
    # Inline dollar delimiters must be paired per non-display line.
    within=False
    for lineno,line in enumerate(clean.splitlines(),1):
        if line.strip()=='$$':within=not within;continue
        if within:continue
        # Literal prices should be written as \$ or in code spans.
        singles=len(re.findall(r'(?<!\\)(?<!\$)\$(?!\$)',line))
        if singles%2:issues.append(f'unpaired inline $ at line {lineno}')
    try:tokens=parser.parse(content)
    except Exception as e:issues.append('CommonMark parsing error '+str(e));tokens=[]
    if not tokens:issues.append('No CommonMark tokens')
    # Use both real parser tokens and a separate syntax-aware link check.
    for match in re.finditer(r'(?<!!)\[[^\]\n]+\]\(([^)]+)\)|!\[[^\]\n]*\]\(([^)]+)\)',content):
        dest=match.group(1) or match.group(2)
        if not dest or dest.startswith(('https://','http://','#','mailto:','data:')):continue
        dest=dest.split('#',1)[0]
        if not (path.parent/dest).exists():issues.append(f'missing relative asset {dest}')
    return issues

files=sorted(ROOT.rglob('*.md'));errors={}
for f in files:
    report=validate_markdown(f.read_text(encoding='utf-8'),f)
    if report:errors[str(f.relative_to(ROOT))]=report
# Required negative tests: parser must FAIL known broken math and broken links.
neg=[('bad_inline',r'Bad \\(x+1\\) formula'),('bad_display',r'Bad \\[ x^2 \\]'),('bad_macro',r'$\\operatorname{sig}(x)$'),('bad_dollar','This is $unbalanced.'),('bad_link','[missing](does_not_exist_local_test_asset.svg)')]
negative={}
for name,broken in neg:
    negative[name]=bool(validate_markdown(broken,ROOT/'NEGATIVE_TEST.md'))
    if not negative[name]:errors['negative_test_'+name]=['failed to reject known broken markdown']
json_report={'markdown_files_checked':len(files),'negative_regression_cases':negative,'issues':errors,'parser':'markdown-it-py commonmark with table plugin','github_visual_preview_checked':False}
(ROOT/'results'/'markdown_preflight.json').write_text(json.dumps(json_report,indent=2)+'\n')
if errors:
    print(json.dumps(json_report,indent=2));sys.exit(1)
print(f'PASS: {len(files)} markdown files, {len(negative)} rejected negative cases, local asset links checked; GitHub UI not inspected.')
