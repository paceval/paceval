#!/usr/bin/env python3
"""Scientific illustrations based on actual V4/FEN/graph files, never synthetic move art."""
from pathlib import Path
import csv,json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch,FancyArrowPatch
from matplotlib import patheffects
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
form=list(csv.DictReader(open(ROOT/'formulas/v4_graph_manifest.csv')))
training=json.loads((ROOT/'formulas/training_metrics.json').read_text())
moves=list(csv.DictReader(open(ROOT/'results/v4_alphabeta_10ply/selfplay_timeline.csv')))
root=list(csv.DictReader(open(ROOT/'results/v4_research/root_move_rankings.csv')))
assert len(moves)==10 and moves[0]['chosen_uci']=='b1c3'
B='♟'; glyph={'k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟','K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙'}
def board(fen,ax,label,move=None):
 rows=fen.split()[0].split('/');cells=[]
 for r in rows:
  line=[]
  for c in r:
   if c.isdigit():line.extend(['']*int(c))
   else:line.append(c)
  assert len(line)==8;cells.append(line)
 assert len(cells)==8
 for r in range(8):
  for c in range(8):
   ax.add_patch(Rectangle((c,r),1,1,color=('#f1e7d3' if (r+c)%2==0 else '#ac8967')))
   piece=cells[r][c]
   if piece:
    text=ax.text(c+.5,r+.56,glyph[piece],fontsize=24,ha='center',va='center',color='#171b23' if piece.islower() else '#fffdf7',fontfamily='DejaVu Sans',zorder=4)
    text.set_path_effects([patheffects.withStroke(linewidth=1.6,foreground='#fffdf7' if piece.islower() else '#282f36')])
 if move:
  x1=ord(move[0])-97+.5;y1=8-int(move[1])+.5
  x2=ord(move[2])-97+.5;y2=8-int(move[3])+.5
  ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=20,color='#c54431',linewidth=2.9,zorder=5))
 ax.set(xlim=(0,8),ylim=(8,0),aspect='equal');ax.set_xticks(np.arange(8)+.5,list('abcdefgh'),fontsize=9);ax.xaxis.tick_bottom();ax.set_yticks(np.arange(8)+.5,[str(i) for i in range(8,0,-1)],fontsize=9);ax.tick_params(length=0);ax.set_title(label,fontsize=12,fontweight='bold',pad=10)
 for spine in ax.spines.values():spine.set_visible(False)
fig,axs=plt.subplots(1,3,figsize=(14,5),layout='constrained')
for ax,rec,name in [(axs[0],moves[0],'Before 1.Nc3'),(axs[1],moves[0],'After 1.Nc3'),(axs[2],moves[1],'After 1...Na6')]:
 fen=rec['fen_before'] if ax is axs[0] else rec['fen_after']
 board(fen,ax,name,rec['chosen_uci'] if ax is not axs[0] else None)
fig.savefig(OUT/'v4_01_legal_board_sequence.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/'v4_01_legal_board_sequence.pdf',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(14,5.1));ax.axis('off');ax.set(xlim=(0,14),ylim=(0,5))
items=[(.12,2.0,2.0,1.12,'FEN chess position','Legal board + history','#f7ede3'),(2.63,2.,2.0,1.12,'C++ legal search','All candidates, Alpha-Beta','#e1eff4'),(5.15,2.,2.0,1.12,'V3 paceval SCORE','32 classical features','#dbefe7'),(7.66,2.,2.0,1.12,'12 paceval NN graphs','48 inputs + trained weights','#f5dfdc'),(10.17,2.,2.0,1.12,'paceval fused SCORE','V3 + clipped residual','#ecedef'),(12.68,2.,1.2,1.12,'Best move','Minimax','#e7eaf0')]
for x,y,w,h,title,sub,c in items:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',fc=c,ec='#657789',lw=1.1))
 ax.text(x+w/2,y+.71,title,fontsize=10.5,weight='bold',ha='center');ax.text(x+w/2,y+.34,sub,fontsize=8.7,ha='center')
for i in range(len(items)-1):
 x=items[i][0]+items[i][2];xx=items[i+1][0]
 ax.annotate('',xy=(xx-.06,2.57),xytext=(x+.06,2.57),arrowprops=dict(arrowstyle='->',lw=2,color='#30445a'))
ax.text(7,4.3,'Trained neural residual supplements a transparent mathematical evaluation, not chess rules',ha='center',fontsize=14,weight='bold')
ax.text(7,.9,'Two supported execution modes: full-width graph batches and alpha-beta on-demand leaf evaluations',ha='center',fontsize=11,color='#4d6170')
fig.savefig(OUT/'v4_02_architecture.png',dpi=200,bbox_inches='tight');fig.savefig(OUT/'v4_02_architecture.pdf',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(11,5.5));ax.bar(['V3 (zero residual)','V4 trained residual'],[training['test_zero_residual_mae_cp'],training['test_mae_residual_cp']],color=['#8fa0ab','#227c83'],width=.55)
for i,val in enumerate([training['test_zero_residual_mae_cp'],training['test_mae_residual_cp']]):ax.text(i,val+2,f'{val:.2f} cp',ha='center',fontsize=12,fontweight='bold')
ax.set_ylim(0,152);ax.set_ylabel('MAE to synthetic depth-2 V3 teacher, centipawns');ax.set_title('Holdout by complete games: imitation error, not chess playing strength',fontsize=14)
ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);fig.savefig(OUT/'v4_03_holdout_error.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/'v4_03_holdout_error.pdf',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(12,5.1));names=[r['graph'] for r in form];lengths=[int(r['formula_characters']) for r in form]
ax.barh(names[::-1],lengths[::-1],color=['#c97d63' if n=='V4_FUSED_SCORE' else '#347f8a' for n in names[::-1]])
ax.set_xlabel('Exact exported expression length (characters)');ax.set_title('Actual compiled paceval V4 formula strings');ax.grid(axis='x',alpha=.22);ax.set_axisbelow(True)
fig.savefig(OUT/'v4_04_graph_lengths.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/'v4_04_graph_lengths.pdf',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(11,5));x=np.arange(len(moves));vals=[float(r['white_score_cp']) for r in moves];labels=[r['chosen_san'] for r in moves]
ax.plot(x+1,vals,'o-',color='#18798a',lw=2)
for i,(v,l) in enumerate(zip(vals,labels)):
 ax.annotate(l,(i+1,v),xytext=(0,9 if i%2==0 else -18),textcoords='offset points',ha='center',fontsize=9)
ax.axhline(0,color='#67717a',lw=.8);ax.set_xticks(x+1);ax.set(xlabel='Halfmove in actual depth-2 self-play',ylabel='Heuristic White score (cp)')
ax.set_title('JOSHUA V4 self-play: decisions recorded from the real local-paceval run',fontsize=13)
ax.grid(alpha=.19);fig.savefig(OUT/'v4_05_real_selfplay.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/'v4_05_real_selfplay.pdf',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(13,6));ax.axis('off');ax.set(xlim=(0,13),ylim=(0,6))
for x,y,t,c in [(1,4.5,'Position feature vectors\n48 input scalars','#e5edf5'),(5.0,4.5,'Persistent hidden graphs\nH0 ... H11','#d9ebe4'),(9,4.5,'Fused output graph\nV3 + bounded residual','#f5e5d8')]:
 ax.add_patch(FancyBboxPatch((x,y),3.1,1.05,boxstyle='round,pad=.06',fc=c,ec='#748a98'));ax.text(x+1.55,y+.55,t,ha='center',va='center',fontsize=11,weight='bold')
for xx in (4.1,8.1):ax.annotate('',(xx+.85,5.02),(xx+.08,5.02),arrowprops=dict(arrowstyle='->',lw=2))
for i in range(5):
 y=3.9-.65*i;ax.add_patch(Rectangle((1.3,y),10.4,.45,fc='#f7f8f9',ec='#d6dce3'))
 ax.text(2.3,y+.22,f'Board / FEN {i+1}',ha='center',va='center',fontsize=10)
 ax.text(6.5,y+.22,'12 hidden-neuron results in one batch',ha='center',va='center',fontsize=10)
 ax.text(10.2,y+.22,'1 final score',ha='center',va='center',fontsize=10)
ax.text(6.5,.15,'Graph structure is created once; variables change for each evaluated position',ha='center',fontsize=11,color='#426174')
fig.savefig(OUT/'v4_06_batch_graph_reuse.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/'v4_06_batch_graph_reuse.pdf',bbox_inches='tight');plt.close(fig)

# Decision tree is generated directly from root score CSV, not arbitrary example values.
current=[r for r in root if int(r['halfmove'])==1]
assert current
fig,ax=plt.subplots(figsize=(12,5));ax.axis('off');ax.set(xlim=(0,12),ylim=(0,5))
ax.add_patch(FancyBboxPatch((4.35,3.95),3.4,.68,boxstyle='round,pad=.08',fc='#e4f1ed',ec='#297c7c'))
ax.text(6.05,4.3,'White: MAX (paceval)',ha='center',va='center',fontsize=13,weight='bold')
for i,r in enumerate(current[:6]):
 xx=1.1+i*1.95
 ax.annotate('',xy=(xx+.55,3.1),xytext=(6.05,3.95),arrowprops=dict(arrowstyle='->',color='#899eac',lw=1.4))
 ax.add_patch(FancyBboxPatch((xx,2.4),1.1,.7,boxstyle='round,pad=.03',fc='#f5ece2',ec='#a8876b'))
 ax.text(xx+.55,2.83,r['uci'],ha='center',fontsize=9.7,fontweight='bold')
 ax.text(xx+.55,2.55,f'{float(r["white_score_cp"]):+.1f} cp',ha='center',fontsize=9)
ax.text(6.05,1.35,'Leaf scores are calculated from actual V3 + trained NN graph outputs.\nChess search and the root decision are separately verified.',ha='center',fontsize=11)
fig.savefig(OUT/'v4_07_actual_minimax_root.png',dpi=180,bbox_inches='tight');fig.savefig(OUT/'v4_07_actual_minimax_root.pdf',bbox_inches='tight');plt.close(fig)
print('Created 7 new scientific figures from V4 data')
