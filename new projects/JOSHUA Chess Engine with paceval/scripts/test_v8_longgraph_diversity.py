#!/usr/bin/env python3
"""Recorded V5 graph evidence replay to test host-side near-best selection.

No paceval calls are claimed: the original graph results are static, and the
selection across fixed root alternatives is being tested, not model fidelity.
"""
import csv
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
manager=Path(sys.argv[1]).resolve();fixture=Path(sys.argv[2]).resolve()
first=fixture/'ply_01'
assert first.exists(),first
with tempfile.TemporaryDirectory(prefix='joshua_v8_longgraph_') as temp:
 root=Path(temp);fake=root/'mock_longgraph.py'
 fake.write_text('#!/usr/bin/env python3\n'
   'from pathlib import Path\nimport sys,shutil,json\n'
   f'source=Path({str(first)!r})\n'
   'a=sys.argv; fen=a[a.index("--fen")+1]\n'
   'ref=json.loads((source/"run_evidence.json").read_text())\n'
   'assert fen==ref["fen_before"], (fen,ref["fen_before"])\n'
   'out=Path(a[a.index("--output")+1]);out.mkdir(parents=True,exist_ok=True)\n'
   'shutil.copyfile(source/"run_evidence.json",out/"run_evidence.json")\n'
   'shutil.copyfile(source/"root_moves.csv",out/"root_moves.csv")\n')
 fake.chmod(0o755)
 cmd=[str(manager),'--engine',str(fake),'--output',str(root/'sessions'),
      '--mode','longgraph','--quiescence','0','--depth','3','--model','4',
      '--opening','engine','--plies','1','--max-games','4',
      '--explore-cp','100','--explore-plies','14','--seed','20261115',
      '--progress-seconds','0']
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=35)
 assert p.returncode==0,(p.stdout,p.stderr)
 chosen=[];best=[]
 for i in range(1,5):
  zip_path=root/'sessions'/'archives'/f'game_{i:06d}.zip'
  assert zip_path.exists(),(zip_path,p.stdout)
  with zipfile.ZipFile(zip_path) as z:
   assert z.testzip() is None
   rows=list(csv.DictReader(io.StringIO(z.read('selfplay_timeline.csv').decode())))
   rankings=list(csv.DictReader(io.StringIO(z.read('root_move_rankings.csv').decode())))
   assert len(rows)==1
   selected=[r for r in rankings if r.get('selected')=='1']
   assert len(selected)==1 and selected[0]['uci']==rows[0]['chosen_uci']
   chosen.append(rows[0]['chosen_uci']);best.append(rankings[0]['uci'])
 assert len(set(chosen))>1,(chosen,best,p.stdout)
 assert len(set(best))==1,(chosen,best)
 assert any(c!=b for c,b in zip(chosen,best)),(chosen,best)
 print('V8_LONGGRAPH_DIVERSITY_MOCK_PASS 4_root_replays alternatives_selected legal_FEN_chain')
