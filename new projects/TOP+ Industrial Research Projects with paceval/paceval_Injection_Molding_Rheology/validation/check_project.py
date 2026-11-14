#!/usr/bin/env python3
"""Archive-wide Markdown/math/link preflight plus structural checks and negative tests.
Uses markdown-it-py as an actual Markdown parser; does not claim GitHub.com UI preview.
"""
from pathlib import Path
import re,json,csv,sys,hashlib
from markdown_it import MarkdownIt
import fitz
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
parser=MarkdownIt('commonmark',{'html':False,'linkify':True})
errors=[]
def inspect_math(source):
    e=[];inside_fence=False;fencetype='';inside_display=False
    for idx,line in enumerate(source.splitlines(),1):
        t=line.strip()
        match=re.match(r'^(```+|~~~+)(.*)$',t)
        if match:
            if not inside_fence:inside_fence=True;fencetype=match.group(1)[0]
            elif fencetype==match.group(1)[0]:inside_fence=False
            continue
        if inside_fence:continue
        if r'\(' in line or r'\)' in line or r'\[' in line or r'\]' in line:e.append(f'{idx}: unsupported escaped LaTex math delimiter')
        if r'\operatorname' in line:e.append(f'{idx}: unsupported operatorname macro')
        # Separate $$ line required for block display math.
        if '$$' in line:
            if t!='$$':e.append(f'{idx}: display formula delimiters must have dedicated line')
            else:inside_display=not inside_display
            continue
        if inside_display:
            if '$' in line:e.append(f'{idx}: nested math delimiter inside display math')
            continue
        # Strip ordinary inline code, so command strings and test paths are not math.
        text=re.sub(r'`[^`]*`','',line)
        text=text.replace(r'\$','')
        if text.count('$')%2:e.append(f'{idx}: unpaired inline $ math delimiter')
        if '$$$' in text:e.append(f'{idx}: nested math fence')
    if inside_display:e.append('unterminated $$ display math fence')
    if inside_fence:e.append('unterminated Markdown code fence')
    return e
mds=list(R.rglob('*.md'))
for f in mds:
    content=f.read_text(encoding='utf8'); rel=f.relative_to(R)
    try:tokens=parser.parse(content)
    except Exception as ex:errors.append(f'{rel}: parser exception {ex}');continue
    errors.extend(f'{rel}:{e}' for e in inspect_math(content))
    # Paths extracted from actual Markdown link/image token stream.
    def walk(tokens):
        for t in tokens:
            if t.type in ('link_open','image'):
                dest=t.attrGet('href' if t.type=='link_open' else 'src')
                if dest and not (dest.startswith(('http://','https://','mailto:','#','data:'))):
                    p=(f.parent/dest.split('#')[0].split('?')[0])
                    if not p.exists():errors.append(f'{rel}: missing relative link {dest}')
            if t.children:walk(t.children)
    walk(tokens)
negative={
 'legacy_inline':r'The value is \(x+1\).',
 'legacy_display':r'\[x+y\]',
 'forbidden_macro':r'$p=\operatorname{sig}(z)$',
 'unbalanced_inline':r'Here $x+1 is unclosed',
 'nested_display':r'$$\nx$y$\n$$'.replace(r'\n','\n'),
 'unclosed_display':r'$$\nx+y'.replace(r'\n','\n')
}
negative_results={k:bool(inspect_math(s)) for k,s in negative.items()}
if not all(negative_results.values()):errors.append('Negative regression test failed to detect bad syntax: '+str(negative_results))
manifest=json.loads((R/'src/formula_manifest.json').read_text())
evidence=json.loads((R/'results/execution_evidence.json').read_text())
expected=manifest['graphs'];assert len(expected)==31
actualids=set(x['function_id'] for x in csv.DictReader((R/'results/math_execution_inventory.csv').open()))
if {z['id'] for z in expected}!=actualids:errors.append('Formula inventory mismatch')
if len(list(csv.DictReader((R/'results/mcp_grid_observed.csv').open())))!=49:errors.append('Grid row mismatch')
if len(list(csv.DictReader((R/'results/mcp_edge_observed.csv').open())))!=12:errors.append('Edge row mismatch')
if evidence['main_graph_point_evaluations']!=1891:errors.append('Evidence counter mismatch')
ref=json.loads((R/'results/high_precision_validation.json').read_text())
if ref['status']!='PASS':errors.append('Independent reference failed')
pdf=fitz.open(R/'paceval_Injection_Molding_Rheology_Whitepaper_EN.pdf')
if len(pdf)!=15:errors.append('PDF does not have expected 15 pages')
# Check nonempty page text and no truly clipped text blocks outside page rectangles.
for i,page in enumerate(pdf):
    if len(page.get_text().strip())<180:errors.append(f'PDF page {i+1} lacks body text')
    for block in page.get_text('blocks'):
        x0,y0,x1,y1,*_=block
        if x0 < -1 or y0 < -1 or x1 >page.rect.width+1 or y1>page.rect.height+1:
            errors.append(f'PDF page {i+1} has text block outside page bounds')
status={'status':'PASS' if not errors else 'FAIL','markdown_files_checked':len(mds),'real_parser':'markdown-it-py CommonMark','negative_tests':negative_results,'negative_tests_passed':sum(negative_results.values()),'local_link_check':'PASS' if not errors else 'review','pdf_pages_checked_for_structure':len(pdf),'original_pdf_visually_rendered_separately':True,'github_com_ui_preview_performed':False,'errors':errors}
(R/'results/markdown_preflight.json').write_text(json.dumps(status,indent=2),encoding='utf8')
print('ARCHIVE PROJECT/PREFLIGHT:',status['status'],'markdown',len(mds),'negative',status['negative_tests_passed'],'PDF pages',len(pdf))
for e in errors[:30]:print('ERROR',e)
if errors:sys.exit(1)
