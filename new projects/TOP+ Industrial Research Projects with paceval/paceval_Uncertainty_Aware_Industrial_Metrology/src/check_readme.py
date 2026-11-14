#!/usr/bin/env python3
"""Markdown equation-fence and local asset/link checker, with a failing-link regression."""
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]
def check(s):
 assert s.startswith('# ')
 assert s.count('$$')%2==0 and s.count('```')%2==0
 refs=re.findall(r'!?\[[^\]]*\]\(([^)]*)\)',s)
 assert len(refs)>11,len(refs)
 for r in refs:
  if r.startswith(('http:','https:','mailto:','#')):continue
  assert (root/r.split('#',1)[0]).is_file(),'Broken relative link: '+r
 for term in ['Industrial use case and current state of the art','Original','paceval_dConvertFloatToString',
              'paceval_dConvertStringToFloat','independent','Covariance','measurement uncertainty']:
  assert term.lower() in s.lower(),term
 for token in ['sandbox:/','file://','<br>']:
  assert token not in s
 return len(refs)
s=(root/'README.md').read_text()
if '--self-test' in sys.argv:
 try:check(s+'\n![bad](figures/__nonexistent_hero.png)')
 except AssertionError as e:
  assert 'Broken relative link' in str(e),e
 else:raise AssertionError('Broken README link incorrectly accepted')
 print('READMELINK_NEGATIVE_REGRESSION_PASS')
else:print('README_LINKS_AND_MATH_PASS',check(s))
