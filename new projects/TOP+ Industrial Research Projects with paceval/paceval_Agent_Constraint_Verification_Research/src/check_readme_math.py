#!/usr/bin/env python3
"""Check GitHub math blocks and local Markdown links without claiming visual rendering."""
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]; md=(root/'README.md').read_text(encoding='utf8')
errors=[]
if md.count('```math') != md.count('```math\n'):errors.append('Malformed opening math fence')
if md.count('```')%2:errors.append('Unbalanced code fences')
for forbidden in (r'\operatorname',):
 if forbidden in md:errors.append('Math macro not permitted in target GitHub renderer: '+forbidden)
for old in ('\\[','\\]','\\(','\\)'):
 if old in md:errors.append('Unsupported math delimiter '+old)
links=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md)
local=0
for url in links:
 path=url.split('#')[0].strip('<>')
 if not path or '://' in path or path.startswith('mailto:'):continue
 local+=1
 if not (root/path).exists():errors.append('Missing link '+path)
print('math blocks:',md.count('```math'),'local links:',local)
print('PASS' if not errors else 'FAIL: '+'; '.join(errors))
sys.exit(bool(errors))
