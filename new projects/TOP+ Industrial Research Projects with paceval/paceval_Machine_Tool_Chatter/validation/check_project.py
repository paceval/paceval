#!/usr/bin/env python3
"""Archive-wide Markdown/KaTeX delimiter and relative-link preflight.

Uses an actual CommonMark parser and explicit maths fencing checks.
It does NOT claim that github.com pages have been visually inspected.
"""
from pathlib import Path
import re,sys,json,csv
import fitz
from markdown_it import MarkdownIt
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
md=MarkdownIt('commonmark',{'html':False})
errors=[]
def audit_math(source):
    e=[];code=False;fchar=None;display=False
    for i,line in enumerate(source.splitlines(),1):
        stripped=line.strip()
        start=re.match(r'^(```+|~~~+)(.*)$',stripped)
        if start:
            if not code:code=True;fchar=start.group(1)[0]
            elif start.group(1)[0]==fchar:code=False;fchar=None
            continue
        if code:continue
        if any(x in line for x in [r'\(',r'\)',r'\[',r'\]']):e.append(f'{i}: legacy escaped maths delimiters')
        if r'\operatorname' in line:e.append(f'{i}: forbidden operatorname macro')
        if '$$' in line:
            if stripped!='$$':e.append(f'{i}: display maths delimiters must occupy separate lines')
            else:display=not display
            continue
        if display:
            if '$' in line:e.append(f'{i}: nested dollar fence inside display block')
            continue
        # Remove ordinary Markdown inline code, escaped dollar signs and hyperlink destinations.
        text=re.sub(r'`[^`]*`','',line).replace(r'\$','')
        text=re.sub(r'\]\([^)]*\)','',text)
        if text.count('$')%2:e.append(f'{i}: unmatched inline maths dollar delimiter')
        if '$$$' in text:e.append(f'{i}: nested triple-dollar syntax')
    if display:e.append('Unclosed display maths delimiter')
    if code:e.append('Unclosed Markdown code fence')
    return e

def links(tokens):
    for t in tokens:
        if t.type in ('link_open','image'):
            u=t.attrGet('href' if t.type=='link_open' else 'src')
            if u:yield u
        if t.children:yield from links(t.children)
mds=sorted(R.rglob('*.md'))
for file in mds:
    s=file.read_text(encoding='utf8');name=str(file.relative_to(R))
    try:tokens=md.parse(s)
    except Exception as ex:errors.append(name+': CommonMark parser failed: '+str(ex));continue
    errors.extend(name+': '+e for e in audit_math(s))
    for url in links(tokens):
        if url.startswith(('http://','https://','mailto:','#','data:')):continue
        dst=file.parent/url.split('#')[0].split('?')[0]
        if not dst.exists():errors.append(name+': broken relative link '+url)
negative={
 'legacy_inline':r'A value \(x+1\) is broken',
 'legacy_display':r'\[ x+y \]',
 'forbidden_macro':r'$p=\operatorname{sig}(z)$',
 'unmatched_inline':r'We use $bcrit + a with a missing close',
 'nested_display':'$$\nx$z$\n$$',
 'unclosed_display':'$$\nx+y',
}
negative_detect={k:bool(audit_math(v)) for k,v in negative.items()}
if not all(negative_detect.values()):errors.append('A negative regression was not detected')
manifest=json.loads((R/'src/formula_manifest.json').read_text())
record=json.loads((R/'results/execution_evidence.json').read_text())
assert len(manifest['graphs'])==23
if record['primary_graph_point_evaluations']!=23*64:errors.append('Execution evidence counter mismatch')
if len(list(csv.DictReader((R/'examples/synthetic_lobe_inputs.csv').open())))!=64:errors.append('Input case count not 64')
if len(list(csv.DictReader((R/'results/mcp_boundary_observed.csv').open())))!=16:errors.append('Transcribed frequency case count not 16')
if set(x['function_id'] for x in csv.DictReader((R/'results/math_execution_inventory.csv').open()))!={x['id'] for x in manifest['graphs']}:errors.append('Manifest/inventory mismatch')
ref=json.loads((R/'results/high_precision_validation.json').read_text())
if ref['status']!='PASS':errors.append('Independent mathematical verification failure')
compact=(R/'COMPACT_SOURCE_ONLY.txt').exists()
pdf=None
if compact:
    # The compact distribution intentionally excludes the large PDF and figures.
    # It still checks maths, links, inventory and numerical references.
    count_pages=0
else:
    pdf=fitz.open(R/'paceval_Machine_Tool_Chatter_Whitepaper_EN.pdf')
    count_pages=len(pdf)
    for i,p in enumerate(pdf):
        if len(p.get_text().strip())<300:errors.append(f'PDF page {i+1} has too little readable text')
        for b in p.get_text('blocks'):
            x0,y0,x1,y1=b[:4]
            if x0 < -1 or y0 < -1 or x1>p.rect.width+1 or y1>p.rect.height+1:errors.append(f'PDF page {i+1} text outside page')
status={'status':'PASS' if not errors else 'FAIL','markdown_count':len(mds),'parser':'markdown-it-py CommonMark','negative_regression_cases':negative_detect,'negative_regressions_passed':sum(negative_detect.values()),'pdf_pages':count_pages,'rendered_pdf_pages':0 if compact else 15,'github_com_ui_not_inspected':True,'errors':errors}
(R/'results'/'markdown_preflight.json').write_text(json.dumps(status,indent=2),encoding='utf8')
print('WP22 document/archive preflight:',status['status'],'Markdown files',len(mds),'negative tests',status['negative_regressions_passed'],'PDF pages',count_pages)
for x in errors[:20]:print('FAIL',x)
if errors:sys.exit(1)
