#!/usr/bin/env python3
"""Complete release preflight; returns nonzero for missing data, math, PDF or SDK source deviations."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
import fitz
P=Path(__file__).resolve().parents[1]
OLD=Path('/mnt/data/WP30_Industrial_Furnace_Paceval_Research/src')
log=[];errors=[]
def require(ok,label):
 log.append({'test':label,'passed':bool(ok)})
 if not ok:errors.append(label)

for f in ['paceval_main.h','paceval_main.cpp']:
 a=P/'src'/f
 require(a.exists() and len(a.read_bytes())>1000,'Original SDK '+f+' exists and nonempty')
 if (OLD/f).exists():
  require(hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256((OLD/f).read_bytes()).digest(),'Original SDK '+f+' unchanged against prior supplied project')
manifest=json.loads((P/'src/formula_manifest.json').read_text())
require([len(x['graphs']) for x in manifest['graph_groups']]==[30,8,5],'All 43 main graphs in formula inventory')
require(len(list(csv.DictReader((P/'results/math_execution_inventory.csv').open())))==43,'43 inventory records')
for file,n in [('axis_snapshots.csv',147),('quaternion_snapshots.csv',12)]:
 require(len(list(csv.DictReader((P/'examples'/file).open())))==n,'Input dataset '+file)
for file,n in [('mcp_observed_joint_grid.csv',49),('mcp_observed_axis_x_examples.csv',8),('mcp_observed_quaternion.csv',12),('mcp_observed_desaturation.csv',12),('mcp_observed_tinc.csv',12)]:
 require(len(list(csv.DictReader((P/'results'/file).open())))==n,'Observed data '+file)
e=json.loads((P/'results/execution_evidence.json').read_text())
require(e['primary_total']==4922,'Correct main graph-point counts')
require(e['aggregate_results']=={'v1_eligible':20,'v2_eligible':15,'changed':5},'Aggregate decision counters')
hp=json.loads((P/'results/high_precision_validation.json').read_text())
require(hp['total_compared']==585 and not hp['failures'],'585 recorded independent comparisons')
require(hp['tinc']['confirmed']==7 and hp['tinc']['point_inclusion_not_demonstrable_from_rounded_text']==3 and hp['tinc']['paceval_error_144_unresolved']==2,'TINC failures and inconclusive cases retained')
md=json.loads((P/'results/markdown_preflight.json').read_text())
require(md['negative_rejected']==8 and not md['failures'] and md['file_count']>=6,'Markdown math parser with negative tests')
figs=list((P/'figures').glob('*.png'))
require(len(figs)>=12,'Research diagrams and conceptual title cover')
from PIL import Image
with Image.open(P/'figures/00_Satellite_Attitude_Cinematic_Cover.png') as im:
 require(im.size==(2400,1200),'Title image exact 2400x1200')
pdf=P/'paceval_Satellite_Attitude_Actuator_Whitepaper_EN.pdf'
require(pdf.exists(),'Scientific PDF exists')
if pdf.exists():
 doc=fitz.open(pdf)
 require(len(doc)==16,'PDF exactly 16 actual pages')
 for i,p in enumerate(doc):
  text=p.get_text('text')
  require(len(text)>250,f'PDF page {i+1}: meaningful selectable text')
  outside=[]
  for blk in p.get_text('blocks'):
   if blk[6]!=0:continue
   x0,y0,x1,y1=blk[:4]
   if x0<0 or y0<0 or x1>p.rect.width+.5 or y1>p.rect.height+.5:outside.append(blk[:4])
  require(not outside,f'PDF page {i+1}: text blocks inside page bounds')
# Compiler syntax only, definitely not link or execution.
cmd=['g++','-std=c++17','-Wall','-Wextra','-Wpedantic','-Werror','-fsyntax-only','satellite_attitude_paceval.cpp']
p=subprocess.run(cmd,cwd=P/'src',capture_output=True,text=True)
require(p.returncode==0,'C++17 host syntax with -Werror')
if p.returncode!=0:errors.append(p.stderr[:500])
p2=subprocess.run(['g++','-std=c++17','-w','-fsyntax-only','paceval_main.cpp'],cwd=P/'src',capture_output=True,text=True)
require(p2.returncode==0,'Original SDK bridge C++17 syntax')
status={'checked_files':len(list(P.rglob('*'))),'tests':len(log),'passed':sum(bool(x['passed']) for x in log),'errors':errors,'local_sdk_linked_or_executed':False,'github_com_renderer_exercised':False}
(P/'results/project_validation.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps({'checks':status['tests'],'passed':status['passed'],'failures':status['errors']},indent=2))
if errors:sys.exit(1)
