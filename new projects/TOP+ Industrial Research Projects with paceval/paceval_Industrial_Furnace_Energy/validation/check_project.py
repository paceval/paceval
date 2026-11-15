#!/usr/bin/env python3
"""Archive-wide Markdown math and link preflight, with negative regression tests."""
from pathlib import Path
import csv,json,re,sys
from markdown_it import MarkdownIt
import fitz
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
md=MarkdownIt('commonmark',{'html':False});errors=[]
def math_check(s):
 out=[];fence=False;display=False;fencechar=''
 for i,line in enumerate(s.splitlines(),1):
  strip=line.strip();m=re.match(r'^(```+|~~~+)',strip)
  if m:
   if not fence:fence=True;fencechar=m.group(1)[0]
   elif m.group(1)[0]==fencechar:fence=False
   continue
  if fence:continue
  if any(x in line for x in (r'\(',r'\)',r'\[',r'\]')):out.append(f'{i}: legacy math delimiter')
  if r'\operatorname' in line:out.append(f'{i}: unsupported operatorname')
  if '$$' in line:
   if strip!='$$':out.append(f'{i}: inline display math delimiter')
   else:display=not display
   continue
  if display:
   if '$' in line:out.append(f'{i}: nested dollar in block math')
   continue
  clean=re.sub(r'`[^`]*`','',line).replace(r'\$','')
  clean=re.sub(r'\]\([^)]*\)','',clean)
  if clean.count('$')%2:out.append(f'{i}: unclosed inline math')
 if display:out.append('unclosed display math')
 if fence:out.append('unclosed code fence')
 return out

def links(tokens):
 for t in tokens:
  if t.type in ('link_open','image'):
   k='href' if t.type=='link_open' else 'src'
   s=t.attrGet(k)
   if s:yield s
  if t.children:yield from links(t.children)
files=sorted(R.rglob('*.md'))
for p in files:
 s=p.read_text(encoding='utf8')
 try:t=md.parse(s)
 except Exception as e:errors.append(str(p)+': parser '+str(e));continue
 errors.extend(str(p.relative_to(R))+': '+v for v in math_check(s))
 for url in links(t):
  if url.startswith(('http://','https://','#','mailto:','data:')):continue
  link=p.parent/url.split('#')[0].split('?')[0]
  if not link.exists():errors.append(str(p.relative_to(R))+': missing '+url)
negative={
 'legacy_inline':r'bad \(x+1\)',
 'legacy_display':r'\[x^2\]',
 'operatorname':r'$p=\operatorname{sig}(z)$',
 'unclosed_inline':'bad $x',
 'nested_display':'$$\nx + $y$\n$$',
 'unclosed_display':'$$\nx+y',
 'inline_display':'text $$x^2$$ text'
}
negative_results={k:bool(math_check(v)) for k,v in negative.items()}
if not all(negative_results.values()):errors.append('Negative markdown regression suite failed')
manifest=json.loads((R/'src/formula_manifest.json').read_text())
inv=list(csv.DictReader((R/'results/math_execution_inventory.csv').open()))
e=json.loads((R/'results/execution_evidence.json').read_text())
obs=list(csv.DictReader((R/'results/mcp_observed_grid_transcription.csv').open()))
snap=list(csv.DictReader((R/'results/mcp_observed_snapshots.csv').open()))
inputs=list(csv.DictReader((R/'examples/synthetic_operating_points.csv').open()))
validation=json.loads((R/'results/high_precision_validation.json').read_text())
if len(manifest['graphs'])!=32 or len(inv)!=32:errors.append('Expected 32 mathematical graphs')
if [x['id'] for x in manifest['graphs']]!=[x['function_id'] for x in inv]:errors.append('Graph inventory IDs disagree')
if len(obs)!=49 or len(snap)!=12 or len(inputs)!=61:errors.append('Input or observed result count is wrong')
if e['primary_graph_point_evaluations']!=1952:errors.append('MCP execution count inconsistent')
if validation['status']!='PASS' or validation['checked_numeric_boolean_cells']!=329 or validation['tinc_passed']!=12:errors.append('Independent precision audit failed/missing')
ops=json.loads((R/'results/operator_mcp_selftest.json').read_text())
if [r[0] for r in ops['actual_results_by_graph']]!=[-1,9,4,5,1,0,1]:errors.append('Operator results invalid')
compact=(R/'COMPACT_SOURCE_ONLY.txt').exists()
pages=0
if not compact:
 p=R/'paceval_Industrial_Furnace_Energy_Whitepaper_EN.pdf'
 if not p.is_file():errors.append('Missing whitepaper')
 else:
  d=fitz.open(p);pages=len(d)
  if pages<12:errors.append('PDF too few pages')
  for n,page in enumerate(d,1):
   if len(page.get_text().strip())<350:errors.append(f'PDF page {n}: insufficient text')
   for b in page.get_text('blocks'):
    x0,y0,x1,y1=b[:4]
    if x0<-.5 or y0<-.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:errors.append(f'PDF page {n}: off-page text')
status={'status':'PASS' if not errors else 'FAIL','markdown_files_checked':len(files),'negative_tests_passed':sum(negative_results.values()),'negative_tests':negative_results,'pdf_pages':pages,'github_com_ui_not_tested':True,'errors':errors}
(R/'results/markdown_preflight.json').write_text(json.dumps(status,indent=2)+'\n')
print('WP30 markdown/archive preflight',status['status'],'md',len(files),'negative tests',sum(negative_results.values()),'PDF pages',pages)
for x in errors[:20]:print('ERROR',x)
sys.exit(bool(errors))
