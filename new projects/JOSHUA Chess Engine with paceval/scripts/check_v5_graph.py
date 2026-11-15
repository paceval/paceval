#!/usr/bin/env python3
"""Audit graph expression, root rankings and independent/reuse comparison evidence."""
from pathlib import Path
import json,re,sys,csv,math
root=Path(sys.argv[1]);d=json.loads((root/'run_evidence.json').read_text())
expr=(root/'paceval_minimax_expression.txt').read_text().strip()
assert len(expr)==d['graph_characters']
assert d['nodes']>d['root_legal_moves']>1
assert d['graph_result_verified'] and d['reused_graph_result_verified']
assert not d['mcp_used']
assert math.isclose(d['paceval_value_cp'],d['independent_cpp_minimax_cp'],abs_tol=1e-8)
assert math.isclose(d['reused_graph_value_cp'],d['reused_graph_independent_cpp_cp'],abs_tol=1e-8)
assert ' min ' in expr and ' max ' in expr
used={int(s) for s in re.findall(r'\bv(\d+)\b',expr)}
assert len(used)>0 and max(used)<d['unique_feature_vectors']
r=list(csv.DictReader((root/'root_moves.csv').open()))
assert len(r)==d['root_legal_moves']
assert d['selected_move'] in {x['move'] for x in r}
print('JOSHUA V5 GRAPH AUDIT PASS',d['nodes'],'nodes',len(expr),'characters',d['unique_feature_vectors'],'distinct inputs')
