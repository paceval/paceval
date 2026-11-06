#!/usr/bin/env python3
"""Validate local Markdown images/links, PNG integrity and key package inputs."""
from pathlib import Path
from urllib.parse import unquote
import re, sys, zipfile
ROOT=Path(__file__).resolve().parents[1]
MARKDOWN=sorted(ROOT.rglob('*.md'))
fail=[]; local=0
for p in MARKDOWN:
    src=p.read_text('utf-8')
    for hit in re.finditer(r'!?\[[^\]]*\]\(([^)]*)\)',src):
        url=hit.group(1).strip('<>')
        if url.startswith(('https://','http://','mailto:','#')) or not url:continue
        target=(p.parent/unquote(url.split('#')[0])).resolve()
        local+=1
        if not target.exists():fail.append(f'Missing link in {p.relative_to(ROOT)} -> {url}')
for f in (ROOT/'figures').glob('*.png'):
    if f.stat().st_size<500:fail.append(f'Too small image: {f.name}')
for path in ['README.md','CMakeLists.txt','sdk/paceval_main.h',
             'report/Braneworld_Shortcuts_Complete_Research_Report_EN.md',
             'report/Braneworld_Shortcuts_Complete_Research_Report_EN.pdf']:
    if not (ROOT/path).is_file():fail.append(f'Missing required file: {path}')
print(f'Markdown files: {len(MARKDOWN)}; local references checked: {local}; PNG images: {len(list((ROOT/"figures").glob("*.png")))}')
if fail:
    print('\n'.join(fail),file=sys.stderr)
    raise SystemExit(1)
print('PASS: publication link and file checks')
