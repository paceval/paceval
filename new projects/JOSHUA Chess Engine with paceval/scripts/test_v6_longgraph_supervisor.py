#!/usr/bin/env python3
"""Recorded-fixture replay of V5 long-graph process supervision; no fresh SDK work."""
from pathlib import Path
import tempfile,subprocess,sys,json,csv,shutil
manager=Path(sys.argv[1]).resolve();fixtures=Path(sys.argv[2]).resolve()
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);fake=p/'mock_longgraph.py';fake.write_text('#!/usr/bin/env python3\n'
  'from pathlib import Path\nimport sys,json,shutil\n'
  f'root=Path({str(fixtures)!r})\n'
  'argv=sys.argv\nfen=argv[argv.index("--fen")+1]\n'
  'folder=Path(argv[argv.index("--output")+1]);folder.mkdir(parents=True,exist_ok=True)\n'
  'for source in sorted(root.glob("ply_*/run_evidence.json")):\n'
  '  if json.loads(source.read_text())["fen_before"]==fen:\n'
  '    shutil.copy(source,folder/"run_evidence.json")\n'
  '    shutil.copy(source.parent/"root_moves.csv",folder/"root_moves.csv")\n'
  '    break\n'
  'else: raise SystemExit("Unknown FEN in prerecorded fixture: "+fen)\n');fake.chmod(0o755)
 cmd=[str(manager),'--engine',str(fake),'--mode','longgraph','--opening','fixed','--quiescence','0','--depth','3','--model','4','--plies','8','--max-games','1','--output',str(p/'run')]
 res=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 assert res.returncode==0,(res.stdout,res.stderr)
 game=p/'run'/'game_000001';rows=list(csv.DictReader((game/'selfplay_timeline.csv').open()))
 assert len(rows)==8,(len(rows),res.stdout)
 summary=json.loads((game/'run_evidence.json').read_text());end=json.loads((game/'end_state.json').read_text())
 assert summary['full_tree_paceval_graphs_built']==8 and summary['independently_checked_graphs']==8
 assert end['termination']=='max_halfmoves' and end['result']=='*'
 for i,r in enumerate(rows):
  source=json.loads((fixtures/f'ply_{i+1:02d}'/'run_evidence.json').read_text())
  assert r['chosen_uci']==source['selected_move'] and r['fen_after']==source['fen_after']
 assert (game/'learning_report.md').exists()
 assert len((p/'run'/'learning_events.jsonl').read_text().splitlines())==1
 print('V6_LONGGRAPH_OFFLINE_REPLAY_PASS eight_prior_real_graph_evidence_records no_new_runtime_execution')
