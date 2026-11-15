#!/usr/bin/env python3
"""Independent result/trajectory coherence audit. No paceval SDK imported."""
import csv,json,sys,math
from pathlib import Path

def board_from_fen(fen):
 p=fen.split();assert len(p)==6
 rows=p[0].split('/');assert len(rows)==8
 b=[]
 for row in rows:
  x=''.join('.'*int(c) if c.isdigit() else c for c in row)
  assert len(x)==8
  b.append(x)
 assert sum(z.count('K') for z in b)==1 and sum(z.count('k') for z in b)==1
 return b,p

def simple_move_coherence(before,after,uci):
 aa,fa=board_from_fen(before);bb,fb=board_from_fen(after)
 assert fa[1] != fb[1]
 assert len(uci) in (4,5) and all(x in 'abcdefgh' for x in (uci[0],uci[2]))
 f1,r1=ord(uci[0])-97,8-int(uci[1]);f2,r2=ord(uci[2])-97,8-int(uci[3]); assert 0<=min(f1,f2,r1,r2) and max(f1,f2,r1,r2)<8
 src=aa[r1][f1];assert src!='.' and src.isupper()==(fa[1]=='w');assert aa[r2][f2].isupper()!=src.isupper() or aa[r2][f2]=='.'
 if len(uci)==4:
  assert bb[r2][f2]==src
 else:assert bb[r2][f2].lower()==uci[4]
 assert bb[r1][f1]=='.'
 # Normal moves in a short opening self-play must not mutate other pieces.
 for r in range(8):
  for f in range(8):
   if (r,f) not in ((r1,f1),(r2,f2)):
    assert aa[r][f]==bb[r][f], f'Unexpected side change: {uci}, square {(r,f)}'

def audit(path):
 folder=Path(path);rows=list(csv.DictReader(open(folder/'selfplay_timeline.csv')));moves=list(csv.DictReader(open(folder/'root_move_rankings.csv')));ev=json.load(open(folder/'run_evidence.json'))
 assert rows and len(rows)<=ev['max_halfmoves'];assert ev['mcp_used'] is False and ev['search_mode'] in ('research','alphabeta')
 is_full = ev['search_mode']=='research'
 assert ev['all_minmax_reductions_via_paceval'] is is_full and ev['leaf_multi_graph_count']==20
 last=-1;total_features=0;lastwhite=None
 for ix,r in enumerate(rows):
  assert int(r['halfmove'])==int(rows[0]['halfmove'])+ix
  assert r['side'] == ('white' if r['fen_before'].split()[1]=='w' else 'black')
  assert last <= float(r['start_s']) <= float(r['tree_ready_s']) <= float(r['leaf_values_ready_s']) <= float(r['decision_s'])
  assert int(r['tree_nodes']) >= int(r['leaf_nodes']) >= int(r['unique_feature_vectors'])>0
  assert int(r['legal_root_moves'])>0 and (int(r['score_batches'])>0 if is_full else int(r['score_batches'])==0) and int(r['reduction_batches'])>0
  assert int(r['new_paceval_reduction_graphs'])>=0
  assert math.isclose(float(r['tree_generation_s']),float(r['tree_ready_s'])-float(r['start_s']),abs_tol=0.015)
  assert math.isclose(float(r['score_batch_s']),float(r['leaf_values_ready_s'])-float(r['tree_ready_s']),abs_tol=0.015)
  assert math.isclose(float(r['reduction_s']),float(r['decision_s'])-float(r['leaf_values_ready_s']),abs_tol=0.015)
  simple_move_coherence(r['fen_before'],r['fen_after'],r['chosen_uci'])
  if 'chosen_piece' in r:
   pieces={'P':'Bauer','N':'Springer (Pferd)','B':'Läufer','R':'Turm','Q':'Dame','K':'König'}
   before,_=board_from_fen(r['fen_before'])
   uci=r['chosen_uci'];assert r['from_square']==uci[:2] and r['to_square']==uci[2:4]
   mover=before[8-int(uci[1])][ord(uci[0])-97].upper()
   assert r['chosen_piece']==pieces[mover],f'wrong piece label: {r}'
   assert r['chosen_san'] and (r['chosen_san'].startswith('O-O') if mover=='K' and abs(ord(uci[2])-ord(uci[0]))==2 else True)
   assert r['is_capture'] in ('0','1')
   assert r['promotion']==('' if len(uci)==4 else pieces[uci[-1].upper()])
  if ix:assert lastwhite==r['fen_before'], 'FEN chain broken'
  lastwhite=r['fen_after'];last=float(r['decision_s']);total_features+=int(r['unique_feature_vectors'])
  options=[o for o in moves if int(o['halfmove'])==int(r['halfmove'])]
  assert len(options)==int(r['legal_root_moves']) and [int(x['rank']) for x in options]==list(range(1,len(options)+1))
  assert options[0]['uci']==r['chosen_uci'] and float(options[0]['white_score_cp'])==float(r['white_score_cp'])
  values=[float(x['white_score_cp']) for x in options]
  if r['side']=='white':assert values==sorted(values,reverse=True)
  else:assert values==sorted(values)
 assert int(ev['paceval_graph_point_evaluations']) >= (20*total_features if is_full else len(rows))
 assert int(ev['played_halfmoves'])>=len(rows)
 print(f'AUTOPLAY_AUDIT_PASS mode={ev["search_mode"]} rows={len(rows)} unique_feature_vectors={total_features} graphs={ev["paceval_graphs_created"]} graph_points={ev["paceval_graph_point_evaluations"]}')

if __name__=='__main__':audit(sys.argv[1])
