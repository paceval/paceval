#!/usr/bin/env python3
"""Check GitHub math fences and local README links (not a visual renderer)."""
import re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
t=(root/'README.md').read_text()
assert t.count('```math')==t.count('```math\n')
assert not any(d in t for d in (r'\[',r'\]',r'\(',r'\)'))
assert t.count('```')%2==0
missing=[]
for dest in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)|!\[[^]]*\]\(([^)]+)\)',t):
    x=dest[0] or dest[1]
    if x.startswith(('http://','https://','#','mailto:')):continue
    if not (root/x.split('#')[0]).exists():missing.append(x)
assert not missing,missing
print(f'PASS: {t.count("```math")} GitHub math blocks; local links exist')
