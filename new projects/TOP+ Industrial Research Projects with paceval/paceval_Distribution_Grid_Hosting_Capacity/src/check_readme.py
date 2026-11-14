#!/usr/bin/env python3
"""Check WP11 GitHub Markdown code fences, LaTex fences, exact links and negative controls."""
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]
def check(text):
 assert text.startswith('# ')
 assert text.count('$$')%2==0 and text.count('```')%2==0
 refs=re.findall(r'!?(?:\[[^\]]*\])\(([^)]*)\)',text)
 assert len(refs)>=19
 for r in refs:
  if r.startswith(('https:','http:','mailto:','#')):continue
  q=r.split('#',1)[0]
  assert (root/q).is_file(),'Broken relative link: '+r
 for term in ['Industrial use case and current state of the art','paceval_dConvertFloatToString','paceval_dConvertStringToFloat','independent','reactive','hosting','network_branches.csv']:
  assert term.lower() in text.lower(),term
 for x in ['sandbox:/','file://','<br>']:
  assert x not in text,x
 return len(refs)
readme=(root/'README.md').read_text()
if '--self-test' in sys.argv:
 try:check(readme+'\n![bad](figures/this_does_not_exist.png)')
 except AssertionError as exc:assert 'Broken relative link' in str(exc)
 else:raise AssertionError('Negative link regression failed')
 print('BROKEN_LINK_NEGATIVE_TEST_PASS')
else:print('README_MATH_AND_LINKS_PASS',check(readme))
