#!/usr/bin/env python3
"""Actual markdown parser/link/math audit with intentional negative tests."""
from pathlib import Path
import re,sys,json
from markdown_it import MarkdownIt
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
md=MarkdownIt('commonmark')

def check(source):
    tokens=md.parse(source)
    failures=[]
    for token in tokens:
        seq=[token]
        if token.children:seq+=token.children
        for item in seq:
            if item.type in ('link_open','image'):
                dest=item.attrGet('href' if item.type=='link_open' else 'src')
                if not dest:failures.append('Missing destination')
                elif not re.match(r'^(https?:|mailto:|#)',dest) and not (root/dest.split('#')[0]).is_file():failures.append('Broken relative link: '+dest)
    # Strip code fences (rather than interpreting code examples as mathematics).
    prose=re.sub(r'```[\s\S]*?```','',source)
    if prose.count('$$')%2:failures.append('Unbalanced display math')
    if re.search(r'!\[[^]]+\]\(\)',prose):failures.append('Empty image link')
    if re.search(r'\\(?:begin|end)\{(?!aligned|array|cases)',prose):failures.append('Unsupported raw LaTeX environment')
    return failures

content=(root/'README.md').read_text(encoding='utf8')
errors=check(content)
assert not errors,errors
assert check('[broken](no_such_target_1234.md)')
assert check('$$\na=b')
assert check('![broken]()')
assert (root/'src/paceval_main.h').is_file() and (root/'src/paceval_main.cpp').is_file()
assert (root/'figures/00_additive_thermal_window_hero.png').is_file()
assert (root/'results/mcp_tinc_raw_record.csv').is_file()
for name in ['README.md','results/execution_evidence.json','src/formula_manifest.json']:
 assert (root/name).stat().st_size>100
report={'markdown_parser':'markdown-it-py commonmark','readme_relative_links':'PASS','display_math_pairs':'PASS','negative_tests':['broken_local_link_rejected','unbalanced_display_math_rejected','empty_image_link_rejected'],'original_sdk_sources_present':True}
(root/'results/readme_link_math_audit.json').write_text(json.dumps(report,indent=2))
print('Project README/link/math checks passed with 3 deliberate negative tests.')
