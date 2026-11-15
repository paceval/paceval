#!/usr/bin/env python3
"""Independent exact replay comparison across saved original/optimized 20-ply runs."""
from pathlib import Path
import csv, json
root=Path(__file__).resolve().parents[1]/'results'
paths=('baseline_original','optimized_research','optimized_alphabeta')
sets=[]
for name in paths:
 p=root/name
 tl=list(csv.DictReader((p/'selfplay_timeline.csv').open()))
 rk=list(csv.DictReader((p/'root_move_rankings.csv').open()))
 ev=json.loads((p/'run_evidence.json').read_text())
 assert len(tl)==20 and ev['played_halfmoves']==20 and ev['mcp_used'] is False
 sets.append((tl,rk,ev))
baseT,baseR,_=sets[0]
for name,(tl,rk,ev) in zip(paths[1:],sets[1:]):
 assert len(rk)==len(baseR)==478
 for ix,(x,y) in enumerate(zip(baseT,tl),1):
  for field in ('halfmove','side','chosen_uci','chosen_san','chosen_piece','white_score_cp','fen_before','fen_after'):
   assert x[field]==y[field],f'{name} ply {ix}: {field} changed'
 for ix,(x,y) in enumerate(zip(baseR,rk),1):
  for field in ('halfmove','side','uci','rank','white_score_cp'):
   assert x[field]==y[field],f'{name} root candidate {ix}: {field} changed'
print('JOSHUA_RELEASE_EQUIVALENCE_PASS 20/20 halfmoves and 478/478 ranked scores in both optimized modes')
