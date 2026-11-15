#!/usr/bin/env python3
"""Recheck recorded reusable paceval mathematical graph expressions per move."""
from pathlib import Path
import csv,json,math,sys,re
p=Path(sys.argv[1]);s=json.loads((p/'summary.json').read_text())
rows=list(csv.DictReader((p/'selfplay_timeline.csv').open()))
assert s['played_plies']==len(rows)==8
assert s['depth']==3 and s['model']==4 and s['mcp_used'] is False
assert s['paceval_local_graphs_per_move']
assert s['independent_minimax_checks_passed']==8 and s['reused_graph_checks_passed']==8
assert sum(int(r['graph_characters']) for r in rows)==s['total_graph_characters_generated']
assert rows[-1]['fen_after']==s['final_fen']
for i,r in enumerate(rows,1):
 d=p/f'ply_{i:02d}';j=json.loads((d/'run_evidence.json').read_text());expr=(d/'paceval_minimax_expression.txt').read_text().rstrip('\n')
 assert int(r['ply'])==i and j['graph_characters']==len(expr)==int(r['graph_characters'])
 assert j['nodes']==int(r['search_nodes']) and j['unique_feature_vectors']==int(r['distinct_leaf_inputs'])
 assert j['selected_move']==r['move_uci'] and j['fen_before']==r['fen_before'] and j['fen_after']==r['fen_after']
 assert j['graph_result_verified'] and j['reused_graph_result_verified']
 assert math.isclose(j['paceval_value_cp'],j['independent_cpp_minimax_cp'],abs_tol=1e-8)
 assert math.isclose(j['reused_graph_value_cp'],j['reused_graph_independent_cpp_cp'],abs_tol=1e-8)
 assert ' min ' in expr and ' max ' in expr
 assert max(map(int,re.findall(r'\bv(\d+)\b',expr)))<j['unique_feature_vectors']
 assert int(r['model'])==4 and int(r['depth'])==3
 assert (p/f'ply_{i:02d}'/'leaf_values.csv').exists()
print('EIGHT-PLY V5 GRAPH EVIDENCE PASS',len(rows),'graph builds',s['total_graph_characters_generated'],'characters')
