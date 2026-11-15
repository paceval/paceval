#!/usr/bin/env python3
"""Independent full-width versus exact fixed-depth alpha-beta equivalence.
All legal root moves, exact white-centric scores and resulting chess positions must match.
"""
import csv, json, sys
from pathlib import Path

def read(d):
 d=Path(d)
 return (list(csv.DictReader((d/'selfplay_timeline.csv').open())),
         list(csv.DictReader((d/'root_move_rankings.csv').open())),
         json.load((d/'run_evidence.json').open()))

a,ra,ea=read(sys.argv[1]);b,rb,eb=read(sys.argv[2]);assert ea['search_mode']=='research';assert eb['search_mode']=='alphabeta'
assert len(a)==len(b)>0
for i,(x,y) in enumerate(zip(a,b),1):
 for field in ('side','chosen_uci','chosen_san','chosen_piece','white_score_cp','fen_before','fen_after','legal_root_moves'):
  assert x[field]==y[field],f'Ply {i} differs in {field}: {x[field]} vs {y[field]}'
assert len(ra)==len(rb)>0
for x,y in zip(ra,rb):
 for f in ('halfmove','depth','side','rank','uci','white_score_cp'):
  assert x[f]==y[f],f'Root move score differs at halfmove {x["halfmove"]}, {f}'
assert ea['mcp_used'] is False and eb['mcp_used'] is False
assert ea['all_minmax_reductions_via_paceval'] is True and eb['all_minmax_reductions_via_paceval'] is False
print(f'MODE_EQUIVALENCE_PASS plies={len(a)} exact_root_scores={len(ra)} white_and_black_moves=IDENTICAL')
