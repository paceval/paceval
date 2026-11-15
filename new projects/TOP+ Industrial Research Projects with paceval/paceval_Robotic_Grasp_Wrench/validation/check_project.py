#!/usr/bin/env python3
"""Archive-wide Markdown math and link QA with six negative regression cases.
Not a live GitHub.com UI preview. All paths resolved relative to their Markdown file.
"""
from pathlib import Path
import csv,sys,json,re
from markdown_it import MarkdownIt
import fitz
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
md=MarkdownIt('commonmark',{'html':False});errors=[]
def math_check(s):
    out=[];fence=False;fencechar='';display=False
    for num,line in enumerate(s.splitlines(),1):
        stripped=line.strip()
        code_match=re.match(r'^(```+|~~~+)(.*)$',stripped)
        if code_match:
            if not fence:fence=True;fencechar=code_match.group(1)[0]
            elif code_match.group(1)[0]==fencechar:fence=False
            continue
        if fence:continue
        if any(x in line for x in (r'\(',r'\)',r'\[',r'\]')):out.append(f'{num}: unsupported legacy raw TeX delimiter')
        if r'\operatorname' in line:out.append(f'{num}: forbidden operatorname macro')
        if '$$' in line:
            if stripped!='$$':out.append(f'{num}: math fence not on its own line')
            else:display=not display
            continue
        if display:
            if '$' in line:out.append(f'{num}: nested math delimiter')
            continue
        cleaned=re.sub(r'`[^`]*`','',line).replace(r'\$','')
        cleaned=re.sub(r'\]\([^)]*\)','',cleaned)
        if cleaned.count('$')%2:out.append(f'{num}: unmatched inline math delimiter')
    if display:out.append('unclosed $$ display math')
    if fence:out.append('unclosed fenced code')
    return out
def get_urls(tokens):
    for t in tokens:
        if t.type in ('link_open','image'):
            val=t.attrGet('href' if t.type=='link_open' else 'src')
            if val:yield val
        if t.children:yield from get_urls(t.children)
md_files=sorted(R.rglob('*.md'))
for path in md_files:
    s=path.read_text(encoding='utf8');rel=str(path.relative_to(R))
    try:t=md.parse(s)
    except Exception as exc:errors.append(rel+': parser exception: '+str(exc));continue
    errors.extend(rel+': '+x for x in math_check(s))
    for url in get_urls(t):
        if url.startswith(('https://','http://','mailto:','#','data:')):continue
        dest=path.parent/url.split('#')[0].split('?')[0]
        if not dest.exists():errors.append(rel+': broken relative link '+url)
negative={
    'legacy_inline':r'This \(x+1\) is legacy',
    'legacy_display':r'\[ x^2 \]',
    'unsupported_macro':r'$p=\operatorname{sig}(z)$',
    'unmatched_inline':'The value $x is unbalanced',
    'nested_display':'$$\nx + $y$\n$$',
    'unclosed_display':'$$\nx+y',
    'inline_display_mixed':'Some text $$ x^2 $$ more text'
}
negative_results={k:bool(math_check(v)) for k,v in negative.items()}
if not all(negative_results.values()):errors.append('negative regression failed')
manifest=json.loads((R/'src/formula_manifest.json').read_text())
inv=list(csv.DictReader((R/'results/math_execution_inventory.csv').open()))
evidence=json.loads((R/'results/execution_evidence.json').read_text())
main=list(csv.DictReader((R/'results/mcp_observed_main_selected.csv').open()))
inp=list(csv.DictReader((R/'examples/synthetic_contact_candidates.csv').open()))
if len(manifest['graphs'])!=28 or len(inv)!=28:errors.append('graph inventory count mismatch')
if set(x['function_id'] for x in inv)!=set(x['id'] for x in manifest['graphs']):errors.append('graph inventory identifiers not equal')
if len(main)!=81 or len(inp)!=81:errors.append('main inputs/results not 81')
if evidence['primary_graph_point_evaluations']!=3888:errors.append('main MCP counting mismatch')
operator=json.loads((R/'results/operator_mcp_selftest.json').read_text())
if not (len(operator['actual_results_by_graph'])==7 and all(len(r)==3 for r in operator['actual_results_by_graph'])):errors.append('operator output dimensions mismatch')
for val in (operator['actual_results_by_graph'][0],operator['actual_results_by_graph'][1]):
    if val not in ([-1,-1,-1],[9,9,9]):errors.append('operator modulo semantics unexpected')
ref=json.loads((R/'results/high_precision_validation.json').read_text())
if ref['status']!='PASS' or ref['checked_numeric_and_boolean_cells']!=567 or ref['tinc_passed']!=8:errors.append('independent scientific reference missing/failing')
compact=(R/'COMPACT_SOURCE_ONLY.txt').exists()
pdfpages=0
if not compact:
    pdf=R/'paceval_Robotic_Grasp_Wrench_Whitepaper_EN.pdf'
    if not pdf.is_file():errors.append('English report PDF missing')
    else:
        f=fitz.open(pdf);pdfpages=len(f)
        if pdfpages<14:errors.append('PDF fewer than expected pages')
        for i,p in enumerate(f):
            if len(p.get_text().strip())<250:errors.append(f'PDF page {i+1} too little readable text')
            for b in p.get_text('blocks'):
                x0,y0,x1,y1=b[:4]
                if x0<-1 or y0<-1 or x1>p.rect.width+1 or y1>p.rect.height+1:errors.append(f'PDF page {i+1} content outside page')
status={'status':'PASS' if not errors else 'FAIL','markdown_files_checked':len(md_files),'markdown_parser':'markdown-it-py CommonMark','negative_regressions_passed':sum(negative_results.values()),'negative_regression_status':negative_results,'pdf_pages':pdfpages,'github_com_live_preview_not_inspected':True,'errors':errors}
(R/'results/markdown_preflight.json').write_text(json.dumps(status,indent=2)+'\n')
print('Archive markdown preflight',status['status'],'md files',len(md_files),'negative tests',status['negative_regressions_passed'],'pdf pages',pdfpages)
for x in errors[:30]:print('FAIL',x)
if errors:sys.exit(1)
