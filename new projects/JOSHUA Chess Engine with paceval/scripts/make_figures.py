#!/usr/bin/env python3
from pathlib import Path
import csv, math
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
BASE=ROOT/'results'/'selfplay_depth3_8plies'
R=list(csv.DictReader(open(BASE/'selfplay_timeline.csv')))
rank=list(csv.DictReader(open(BASE/'root_move_rankings.csv')))
BG='#f9f8f3';INK='#152939';BLUE='#247c8a';GOLD='#bc7e2c';RED='#b75644'
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fontfile_bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def chunks(fen):
 raw=fen.split()[0].split('/');rows=[]
 for x in raw:
  v=[]
  for p in x:
   if p.isdigit():v+=['.']*int(p)
   else:v.append(p)
  assert len(v)==8;rows.append(v)
 assert len(rows)==8 and sum('K' in row for row in rows)==1
 return rows

def board(fen,name,highlight=None,desc=''):
 rows=chunks(fen); sz=86;left=68;top=75;W=2*left+8*sz;H=top+8*sz+85
 im=Image.new('RGB',(W,H),'#ffffff');d=ImageDraw.Draw(im)
 fbase=ImageFont.truetype(fontfile,20);fsmall=ImageFont.truetype(fontfile_bold,18);fhead=ImageFont.truetype(fontfile_bold,22);fch=ImageFont.truetype(fontfile,62)
 d.text((left,20),name,fill=INK,font=fhead)
 syms={'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙','k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟'}
 for r in range(8):
  for c in range(8):
   x=left+c*sz;y=top+r*sz
   shade='#e4eadf' if (r+c)%2==0 else '#77998e'
   d.rectangle((x,y,x+sz,y+sz),fill=shade)
   if highlight and chr(97+c)+str(8-r) in highlight:
    d.rectangle((x+4,y+4,x+sz-4,y+sz-4),outline='#e6a326',width=6)
   p=rows[r][c]
   if p!='.':
    symbol=syms[p];bb=d.textbbox((0,0),symbol,font=fch);pw=bb[2]-bb[0];ph=bb[3]-bb[1]
    d.text((x+(sz-pw)/2-bb[0],y+(sz-ph)/2-bb[1]-2),symbol,fill='#1b2730' if p.islower() else '#fffefa',stroke_width=2,stroke_fill='#07151c' if p.isupper() else '#e1dccc',font=fch)
  d.text((25,top+r*sz+30),str(8-r),font=fsmall,fill=INK)
 for c in range(8):d.text((left+c*sz+32,top+8*sz+12),chr(97+c),font=fsmall,fill=INK)
 if desc:d.text((left,H-26),desc,fill=INK,font=fbase)
 im.save(FIG/(name.lower().replace(' ','_').replace(':','')+'.png'))

board(R[0]['fen_before'],'01 Initial position',None,'Starting position; White to move')
board(R[0]['fen_after'],'02 White b1c3',['b1','c3'],'After 1. Nc3; Black to move')
board(R[1]['fen_after'],'03 Black b8c6',['b8','c6'],'After 1... Nc6; White to move')
forced=ROOT/'results'/'selfplay_forced_e4_depth3_6plies'/'selfplay_timeline.csv'
F=list(csv.DictReader(open(forced)))
board(F[0]['fen_before'],'04 Forced e2e4',['e2','e4'],'After an explicitly forced 1. e4; Black to move')
board(F[0]['fen_after'],'05 Black g8f6',['g8','f6'],'After 1. e4 Nf6; White to move')
# Measured time stages
ply=[int(r['halfmove']) for r in R]
fig,ax=plt.subplots(figsize=(9.5,4.5));ax.bar(ply,[float(r['tree_generation_s']) for r in R],label='Complete tree construction',color=BLUE)
ax.bar(ply,[float(r['score_batch_s']) for r in R],bottom=[float(r['tree_generation_s']) for r in R],label='paceval multi-graph leaf evaluation',color=GOLD)
ax.bar(ply,[float(r['reduction_s']) for r in R],bottom=[float(r['tree_generation_s'])+float(r['score_batch_s']) for r in R],label='paceval min/max reduction',color=RED)
ax.set(xlabel='Half-move',ylabel='Measured stage seconds',title='Observed per-turn stages, Linux, depth 3');ax.set_xticks(ply);ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(FIG/'06_measured_stage_durations.png',dpi=180);fig.savefig(FIG/'06_measured_stage_durations.pdf');plt.close(fig)
# Unique leaf features vs leaves
fig,ax=plt.subplots(figsize=(9.5,4.5));ax.bar([x-.19 for x in ply],[int(r['leaf_nodes']) for r in R],width=.38,color=BLUE,label='Full search leaves');ax.bar([x+.19 for x in ply],[int(r['unique_feature_vectors']) for r in R],width=.38,color=GOLD,label='Unique input feature vectors');ax.set_yscale('log');ax.set(xlabel='Half-move',ylabel='Count (log scale)',title='Separate search leaves from mathematical feature reuse');ax.set_xticks(ply);ax.legend(fontsize=9);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(FIG/'07_feature_reuse.png',dpi=180);fig.savefig(FIG/'07_feature_reuse.pdf');plt.close(fig)
# Ranked root-move scores actual (first move from run)
top=[x for x in rank if x['halfmove']=='1'][:10]
fig,ax=plt.subplots(figsize=(9.5,5));v=[float(x['white_score_cp']) for x in top];ax.barh([x['uci'] for x in reversed(top)],list(reversed(v)),color=[BLUE if x==max(v) else '#9fbcc0' for x in reversed(v)]);ax.set(xlabel='Model V2 score in centipawns, from White perspective',title='Exact paceval-backed depth-3 root ranking (first turn)');ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(FIG/'08_first_turn_rankings.png',dpi=180);fig.savefig(FIG/'08_first_turn_rankings.pdf');plt.close(fig)
# Count chart of exact perft sizes
fig,ax=plt.subplots(figsize=(9.5,4.5));counts=[1,20,400,8902,197281];ax.bar(range(5),counts,color=BLUE);ax.set(yscale='log',xlabel='Exact full-width ply depth',ylabel='Positions at horizon (log scale)',title='Legal move sequence expansion from standard initial position');ax.set_xticks(range(5));ax.set_xticklabels(['0','1','2','3','4']);
for i,n in enumerate(counts):ax.text(i,n*1.1,f'{n:,}',ha='center',fontsize=9)
fig.tight_layout();fig.savefig(FIG/'09_perft_depths.png',dpi=180);fig.savefig(FIG/'09_perft_depths.pdf');plt.close(fig)
# Architecture diagram (uses measured pipeline labels and explicitly owns stage)
fig,ax=plt.subplots(figsize=(10,5));ax.axis('off');nodes=[(.08,.54,'FEN + legal\nchess rules',BLUE),(.35,.54,'Complete legal\nmove tree',BLUE),(.62,.73,'Feature vectors\n19 variables',GOLD),(.88,.73,'paceval persistent\n20 formula graphs',GOLD),(.62,.35,'Grouped by\nbranching degree',RED),(.88,.35,'paceval min/max\nreduction graphs',RED)];
for x,y,t,c in nodes:ax.text(x,y,t,ha='center',va='center',fontsize=10,color='white',bbox=dict(boxstyle='round,pad=.7',fc=c,ec=c))
for x1,y1,x2,y2 in [(0.17,.54,.25,.54),(.47,.60,.52,.70),(.72,.73,.75,.73),(.47,.48,.52,.35),(.75,.35,.78,.35)]:ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='-|>',lw=2,color=INK))
ax.text(.88,.10,'C++ selects argmax / argmin at root',ha='center',fontsize=10,color=INK)
ax.annotate('',xy=(.88,.17),xytext=(.88,.25),arrowprops=dict(arrowstyle='<|-',lw=2,color=INK))
ax.set_title('Research architecture: chess rules in C++, numerical graphs in paceval',fontsize=14,pad=15);fig.tight_layout();fig.savefig(FIG/'10_architecture.png',dpi=180);fig.savefig(FIG/'10_architecture.pdf');plt.close(fig)
# Detailed min max illustrative graph using correct numbers from real observed root rankings
fig,ax=plt.subplots(figsize=(9.5,4.5));ax.axis('off')
# Demonstration is structure, not data: child values chosen from observed root move scores
samples=[('b1c3',float(top[0]['white_score_cp'])),('g1f3',float(top[1]['white_score_cp'])),('d2d4',float(top[2]['white_score_cp']))]
ax.text(.5,.88,'ROOT: White chooses maximum of evaluated legal moves',ha='center',fontsize=13,fontweight='bold',color=INK)
ax.text(.5,.72,'max(' + ', '.join(str(int(q[1])) for q in samples) + ') = '+str(int(max(q[1] for q in samples))),ha='center',fontsize=12,color=BLUE)
for i,(name,score) in enumerate(samples):
 x=.2+i*.3;ax.annotate('',xy=(x,.32),xytext=(.5,.65),arrowprops=dict(arrowstyle='->',lw=2,color='#9ba7ae'))
 ax.text(x,.25,f'{name}\n{score:.0f} cp',ha='center',fontsize=12,bbox=dict(boxstyle='round,pad=.6',fc='#e7eeec',ec='#7f9999'))
ax.text(.5,.07,'Three examples from the full legal root-move list; each child already includes an opponent response.',ha='center',fontsize=9,color=INK)
fig.tight_layout();fig.savefig(FIG/'11_minmax_example.png',dpi=180);fig.savefig(FIG/'11_minmax_example.pdf');plt.close(fig)
print('FIGURES_READY',len(list(FIG.glob('*.png'))),'png')
