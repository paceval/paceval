#!/usr/bin/env python3
"""Create source-derived figures only; all boards come from recorded legal FENs."""
from pathlib import Path
import csv,json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch,FancyBboxPatch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams['font.family']='DejaVu Sans'
plt.rcParams['font.size']=10
G={"K":"♔","Q":"♕","R":"♖","B":"♗","N":"♘","P":"♙","k":"♚","q":"♛","r":"♜","b":"♝","n":"♞","p":"♟"}

def board(fen,ax,highlight=None,title=''):
 fields=fen.split();ranks=fields[0].split('/')
 cells=[]
 for row in ranks:
  z=[]
  for ch in row:
   if ch.isdigit():z+=['.']*int(ch)
   else:z.append(ch)
  assert len(z)==8;cells.append(z)
 assert len(cells)==8
 for r in range(8):
  for c in range(8):
   ax.add_patch(Rectangle((c,7-r),1,1,facecolor='#e9e2d5' if (r+c)%2==0 else '#8b9c91',edgecolor='none'))
   p=cells[r][c]
   if p!='.':ax.text(c+.5,7-r+.50,G[p],ha='center',va='center',fontsize=30,color='#121820' if p.islower() else '#f9f5eb',path_effects=[])
 if highlight:
  f,t=highlight
  for s in (f,t):
   ff=ord(s[0])-ord('a');rr=int(s[1])-1
   ax.add_patch(Rectangle((ff,rr),1,1,facecolor='none',edgecolor='#e18438',linewidth=3))
  ax.add_patch(FancyArrowPatch((ord(f[0])-96.5,int(f[1])-.5),(ord(t[0])-96.5,int(t[1])-.5),arrowstyle='->',mutation_scale=18,color='#c84e25',linewidth=2))
 ax.set_xlim(0,8);ax.set_ylim(0,8);ax.set_aspect('equal');ax.set_xticks([i+.5 for i in range(8)],list('abcdefgh'));ax.set_yticks([i+.5 for i in range(8)],[str(i+1) for i in range(8)]);ax.tick_params(length=0);ax.set_title(title,fontsize=14,fontweight='bold',pad=12)
 for spine in ax.spines.values():spine.set_visible(False)

def rows(folder):return list(csv.DictReader(open(ROOT/'results'/folder/'selfplay_timeline.csv')))
trace=rows('v3_ab_depth3_3ply')
fig,ax=plt.subplots(1,3,figsize=(15,5.8))
board(trace[0]['fen_before'],ax[0],None,'Initial position | White to move')
board(trace[0]['fen_after'],ax[1],('b1','c3'),'After 1. Nc3 | Black to move')
board(trace[1]['fen_after'],ax[2],('b8','c6'),'After 1... Nc6 | White to move')
fig.suptitle('Actual JOSHUA self-play: board states derived from recorded FEN',fontsize=17,fontweight='bold')
fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(FIG/'01_real_chess_positions.png',dpi=170);plt.close(fig)

root=list(csv.DictReader(open(ROOT/'results'/'v3_ab_depth5_q2_2ply'/'root_move_rankings.csv')))
root=[r for r in root if r['halfmove']=='1'][:12]
fig,ax=plt.subplots(figsize=(11,6));root=root[::-1]
labels=[r['uci'] for r in root];values=[float(r['white_score_cp']) for r in root]
ax.barh(labels,values,color=['#d18a35' if r['rank']=='1' else '#497d8b' for r in root]);ax.axvline(0,color='black',linewidth=.7)
ax.set_xlabel('White-centric heuristic centipawns (cp)');ax.set_title('Root alternatives from actual depth-5, V3, q2 opening search',fontweight='bold')
ax.grid(axis='x',alpha=.18);fig.tight_layout();fig.savefig(FIG/'02_actual_root_scores.png',dpi=175);plt.close(fig)

# Architecture: this diagram reflects actual implementation API boundaries.
fig,ax=plt.subplots(figsize=(14,6));ax.set_xlim(0,14);ax.set_ylim(0,6);ax.axis('off')
blocks=[(0.4,3.55,2.2,1.2,'Legal board states\nC++ make/unmake','#edf2ed'),(3.0,3.55,2.15,1.2,'32 V3 features\nC++ extraction','#edf2ed'),(5.6,3.55,3.0,1.2,'paceval V3 SCORE\npersistent graph','#d8edec'),(9.05,3.55,2.1,1.2,'Alpha-Beta\nC++ recursion','#edf2ed'),(11.65,3.55,2.0,1.2,'Root MAX/MIN\npaceval graph','#d8edec'),(5.6,1.45,3.0,1.15,'paceval V1/V2\nreference graph set','#d8edec'),(9.05,1.45,2.1,1.15,'Exact research\nfull-width graph','#edf2ed')]
for x,y,w,h,txt,fc in blocks:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.12',linewidth=1.4,edgecolor='#557279',facecolor=fc))
 ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=11,fontweight='bold')
for x1,x2,y in [(2.6,3.0,4.15),(5.15,5.6,4.15),(8.6,9.05,4.15),(11.15,11.65,4.15)]:
 ax.add_patch(FancyArrowPatch((x1,y),(x2,y),arrowstyle='-|>',mutation_scale=16,linewidth=2,color='#b57b40'))
ax.text(7,5.55,'JOSHUA: local paceval numerical graphs, C++ search and board rules',ha='center',fontsize=16,fontweight='bold')
ax.text(7,0.55,'Research mode batches all distinct leaf feature rows; Alpha-Beta mode evaluates required leaves on demand.',ha='center',fontsize=11)
fig.tight_layout();fig.savefig(FIG/'03_actual_architecture.png',dpi=175);plt.close(fig)

runs=['v3_ab_depth3_3ply','v3_ab_depth4_4ply','v3_ab_depth5_q2_2ply','v3_ab_depth6_initial','v3_ab_depth8_q1_endgame','v3_ab_depth10_endgame','v3_ab_depth4_q1_10ply']
metrics=[]
for name in runs:
 ev=json.load(open(ROOT/'results'/name/'run_evidence.json'))
 metrics.append((name.replace('v3_ab_','').replace('_',' '),ev['depth_each_move'],ev['played_halfmoves'],float(ev['elapsed_seconds']),int(ev['paceval_graph_point_evaluations'])))
fig,ax=plt.subplots(figsize=(11,6));labels=[m[0] for m in metrics];secs=[m[3] for m in metrics]
ax.barh(labels[::-1],secs[::-1],color=['#416d79']*len(secs));ax.set_xlabel('Observed total wall time (s)');ax.grid(axis='x',alpha=.2);ax.set_title('Actual recorded runs (different FEN and ply budgets; not a speed benchmark)',fontweight='bold');fig.tight_layout();fig.savefig(FIG/'04_observed_runs.png',dpi=175);plt.close(fig)

fig,ax=plt.subplots(figsize=(12,6));ax.axis('off');ax.set_xlim(0,12);ax.set_ylim(0,6)
# Mathematical expressions are exact semantics; diagram uses recorded first ply top 4 values.
rs=list(csv.DictReader(open(ROOT/'results'/'v3_ab_depth5_q2_2ply'/'root_move_rankings.csv')))
rs=[r for r in rs if r['halfmove']=='1'][:4]
ax.add_patch(FancyBboxPatch((4.7,4.8),2.6,.8,boxstyle='round,pad=.12',facecolor='#d6e6e3',edgecolor='#4c7780',linewidth=1.3))
ax.text(6,5.2,'MAX for White\npaceval root graph',ha='center',va='center',fontsize=13,fontweight='bold')
for i,r in enumerate(rs):
 x=.35+i*2.87
 ax.add_patch(FancyBboxPatch((x,2.1),2.5,1.35,boxstyle='round,pad=.1',facecolor='#f3eee3',edgecolor='#b58a5a',linewidth=1.2))
 ax.text(x+1.25,2.85,r['uci'],ha='center',fontsize=14,fontweight='bold')
 ax.text(x+1.25,2.42,str(r['white_score_cp'])+' cp',ha='center',fontsize=12)
 ax.add_patch(FancyArrowPatch((6,4.78),(x+1.25,3.6),arrowstyle='<-',mutation_scale=14,color='#67818b',linewidth=1.4))
ax.text(6,.9,'Each displayed score is a recorded root-search result, not an invented leaf value.',ha='center',fontsize=11)
ax.text(6,.45,'Individual internal alpha-beta decisions remain in C++; final root reduction is a real paceval graph.',ha='center',fontsize=10)
ax.set_title('Actual V3 root decision: search alternatives and paceval MAX',fontsize=17,fontweight='bold',pad=15)
fig.tight_layout();fig.savefig(FIG/'05_actual_root_reduction.png',dpi=170);plt.close(fig)
print('FIGURES_CREATED',len(list(FIG.glob('0*_*.png'))))
