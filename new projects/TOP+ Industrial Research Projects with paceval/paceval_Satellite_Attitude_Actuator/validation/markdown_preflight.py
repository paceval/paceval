#!/usr/bin/env python3
"""Archive-wide GitHub math/relative-link preflight using real mistune math parsing.
Includes negative regression cases for the known raw-TeX defects.
"""
from pathlib import Path
import json,re,sys
import mistune
BASE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
renderer=mistune.create_markdown(renderer='ast',plugins=['math'])
LINK=re.compile(r'!?\[[^\]\n]*\]\(([^)]+)\)')

def check(text,folder,virtual=False):
 problems=[];in_fence=False;math_block=False;inline_count=0;block_count=0
 for lineno,line in enumerate(text.splitlines(),1):
  s=line.strip()
  if s.startswith('```') or s.startswith('~~~'):
   if not math_block:in_fence=not in_fence
   continue
  if in_fence:continue
  if s=='$$':math_block=not math_block;block_count+=1;continue
  if math_block:
   if '$' in line and not s.startswith('\\$'):problems.append(f'{lineno}: nested dollar delim inside display math')
   continue
  if '\\(' in line or '\\)' in line or '\\[' in line or '\\]' in line:problems.append(f'{lineno}: forbidden raw TeX math delimiters')
  if '\\operatorname' in line:problems.append(f'{lineno}: forbidden operatorname macro')
  if '$$' in line:problems.append(f'{lineno}: display math must have separate $$ lines')
  if line.count('$')%2:problems.append(f'{lineno}: unbalanced inline $')
  inline_count+=line.count('$')//2
 if in_fence:problems.append('unclosed Markdown code fence')
 if math_block:problems.append('unclosed display math $$ fence')
 try:
  ast=renderer(text)
  def count_math(x):
   if isinstance(x,list):return sum(count_math(z) for z in x)
   if isinstance(x,dict):return int(x.get('type') in {'inline_math','block_math'})+sum(count_math(v) for v in x.values())
   return 0
  recognized=count_math(ast)
  if (inline_count or block_count) and recognized==0:problems.append('real Markdown math parser recognized no math nodes')
 except Exception as exc:problems.append(f'Markdown parsing failed: {exc}')
 if not virtual:
  for raw in LINK.findall(text):
   link=raw.strip().split(' ',1)[0].strip('<>')
   if link.startswith(('http://','https://','mailto:','#','data:')):continue
   p=(folder/link.split('#',1)[0].split('?',1)[0]).resolve()
   if not p.is_file():problems.append('broken relative Markdown resource: '+raw)
 return problems,inline_count,block_count

files=list(sorted(BASE.rglob('*.md')));fail=[];stats=[]
for path in files:
 errors,ins,blocks=check(path.read_text(encoding='utf-8'),path.parent)
 stats.append({'file':str(path.relative_to(BASE)),'inline_pairs':ins,'display_delimiter_lines':blocks,'errors':errors})
 if errors:fail.extend(f'{path.relative_to(BASE)}: {e}' for e in errors)
# The deliberate negative cases MUST be rejected, proving that this preflight does not pass everything.
negatives=[
 'Use \\(x+1\\) in prose',
 'Use \\[x^2\\] in prose',
 'Here is $\\operatorname{sig}(x)$',
 'The variable $x is unmatched.',
 '$$\na+b\n',
 '$$x = $y$$',
 '![image](does_not_exist_wp32.png)',
 '```math\ny = x^2\n',
]
neg_rejected=0
for test in negatives:
 if check(test,BASE)[0]:neg_rejected+=1
 else:fail.append('negative regression example incorrectly accepted: '+repr(test))
report={'folder':str(BASE),'file_count':len(files),'files':stats,'negative_cases':len(negatives),'negative_rejected':neg_rejected,'failures':fail,'github_com_visual_render_verified':False,'parser':'mistune AST with math plugin'}
if BASE.name=='WP32_Satellite_Attitude_Paceval_Research':
 (BASE/'results'/'markdown_preflight.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'inline_math_pairs':sum(x['inline_pairs'] for x in stats),'negative_rejected':neg_rejected,'negative_total':len(negatives),'failures':fail},indent=2))
if fail:sys.exit(1)
