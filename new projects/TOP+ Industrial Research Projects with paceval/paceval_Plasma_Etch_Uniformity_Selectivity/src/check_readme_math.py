#!/usr/bin/env python3
"""Fail-closed lightweight GitHub README link/math check with a negative regression."""
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]
def validate(doc):
 if not doc.startswith('# '):raise AssertionError('Main heading missing')
 if doc.count('$$')%2:raise AssertionError('Unbalanced display math')
 if '```' in doc and doc.count('```')%2:raise AssertionError('Unbalanced fences')
 paths=re.findall(r'!?(?:\[[^\]]*\])\(([^\)]*)\)',doc)
 for p in paths:
  if p.startswith(('http://','https://','mailto:','#')):continue
  if not (root/p.split('#')[0]).is_file():raise AssertionError('Broken relative link: '+p)
 if len(paths)<10:raise AssertionError('Too few actual links')
 for forbidden in ('sandbox:/','file:///','<br>'):assert forbidden not in doc
 for term in ('Industrial use case and current state of the art','paceval_dConvertFloatToString','paceval_dConvertStringToFloat','Original','independent'):assert term in doc,term
 return len(paths)
doc=(root/'README.md').read_text()
if '--self-test' in sys.argv:
 try:validate(doc+'\n![broken](figures/__missing__.png)')
 except AssertionError as e:
  if 'Broken relative' not in str(e):raise
 else:raise AssertionError('Intentional missing link passed')
 print('NEGATIVE_LINK_REGRESSION_PASS')
else:print('README_LINKS_MATH_PASS',validate(doc))
