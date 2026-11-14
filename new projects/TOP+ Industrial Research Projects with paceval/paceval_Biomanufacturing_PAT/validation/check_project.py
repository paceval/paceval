#!/usr/bin/env python3
"""Repeatable artifact structural checks, relative markdown links, negative probes."""
from pathlib import Path
import json,re,sys,csv
from markdown_it import MarkdownIt
from PIL import Image
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
assert (root/'src'/'CMakeLists.txt').is_file()
assert (root/'src'/'paceval_main.h').is_file()
assert (root/'src'/'paceval_main.cpp').is_file()
manifest=json.loads((root/'src'/'formula_manifest.json').read_text());assert len(manifest['graphs'])==24
head=(root/'src'/'generated_formulas.h').read_text();assert head.count('FormulaItem{')==24
im=Image.open(root/'figures'/'00_biomanufacturing_pat_hero.png');assert im.size==(2400,1200) and im.mode=='RGB'
for f,n in [('synthetic_sensor_snapshots.csv',16),('synthetic_state_grid.csv',81)]:
 rows=list(csv.DictReader((root/'data'/f).open()));assert len(rows)==n

def lint_readme(s,linkroot):
 # Parse CommonMark with a real Markdown parser. Inspect its AST rather than
 # assuming every bracket pair is a link. Incomplete fences are separately
 # rejected because CommonMark normally treats them as legal to end-of-file.
 assert s.count('```')%2==0,'Unclosed fenced code block'
 assert s.count('$')%2==0,'Unbalanced inline mathematical delimiters'
 tokens=MarkdownIt('commonmark').parse(s)
 targets=[]
 for token in tokens:
  for part in (token.children or []):
   if part.type=='link_open':targets.append(part.attrGet('href'))
   elif part.type=='image':targets.append(part.attrGet('src'))
 for path in targets:
  assert path is not None
  path=path.split('#')[0]
  if path.startswith(('http://','https://','mailto:')) or not path:continue
  assert (linkroot/path).is_file(),'Missing relative Markdown target: '+path
 return len(targets)
readme=(root/'README.md').read_text();links=lint_readme(readme,root)
# Negative tests prove both fence and relative-link checker are active.
for bad,reason in [(readme+'\n```','unclosed fence'),(readme+'\n[bad](figures/does_not_exist.png)','broken link')]:
 try:lint_readme(bad,root)
 except AssertionError:continue
 else:raise AssertionError('Negative checker failed for '+reason)
print('PASS: exact hero, 24 formulas, SDK source, two input data sets, README markdown links:',links,'negative probes: 2')
