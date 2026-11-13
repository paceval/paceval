"""Basic publication preflight for local links and GitHub math-fence regression."""
import re,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
def validate(s,links=True):
 if '\\operatorname' in s or '\\newcommand' in s:raise ValueError('disallowed command')
 if s.count('```')%2:raise ValueError('unclosed fence')
 for part in re.findall(r'```math\n(.*?)\n```',s,re.S):
  if '$$' in part or '\\[' in part or '\\]' in part:raise ValueError('nested math delimiters')
  if part.count('\\begin{')!=part.count('\\end{'):raise ValueError('unpaired LaTeX environments')
 if links:
  for path in re.findall(r'!?\[[^]]*\]\(([^)]+)\)',s):
   if '://' in path or path.startswith('#') or path.startswith('mailto:'):continue
   if not (root/path.split('#',1)[0].split(' ',1)[0]).exists():raise ValueError('missing local link: '+path)
validate((root/'README.md').read_text())
for bad in ['```math\n$$ x $$\n```','```math\n\\operatorname{route}(x)\n```']:
 try:validate(bad,False);raise AssertionError('negative regression was accepted')
 except ValueError:pass
validate('```math\n\\mathrm{route}(x)=x\n```',False)
print('PASS README links, math fences and positive/negative syntax tests')
