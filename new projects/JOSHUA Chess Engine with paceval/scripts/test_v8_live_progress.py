#!/usr/bin/env python3
"""Live progress integration against a clearly labeled MOCK, not original paceval."""
from pathlib import Path
import tempfile,subprocess,sys,zipfile,json,shutil
manager=Path(sys.argv[1]).resolve();fixture=Path(sys.argv[2]).resolve()
with tempfile.TemporaryDirectory(prefix='joshua_v8_status_') as d:
    root=Path(d); fake=root/'mock_progress_engine.py'
    fake.write_text('#!/usr/bin/env python3\n'
      'import sys,time,shutil,json\nfrom pathlib import Path\n'
      f'fixture=Path({str(fixture)!r})\n'
      'out=Path(sys.argv[sys.argv.index("--output")+1]);out.mkdir(parents=True,exist_ok=True)\n'
      'print("JOSHUA | MOCK PACEVAL-FREE PROGRESS TEST",flush=True)\n'
      'print("[+0.010s] JOSHUA scenario: user-forced opening move e2e4 | SAN=e4 (not engine-selected)",flush=True)\n'
      'print("[+0.020s] ply=2 BLACK legal=20; SEARCH legal moves",flush=True)\n'
      'time.sleep(1.45)\n'
      'print("[+1.475s] EXPLORE ply=2 candidates=3 policy_best=e7e5 played=c7c5 loss_cp=11 seed=22",flush=True)\n'
      'print("[+1.476s] JOSHUA PLAYED BLACK c7c5 | Piece=Pawn c7 -> c5 | SAN=c5 | score_white=17cp | FEN x",flush=True)\n'
      'for name in ("selfplay_timeline.csv","root_move_rankings.csv","run_evidence.json","game_uci.txt"):\n'
      '    shutil.copyfile(fixture/name,out/name)\n'
      'ev=json.loads((out/"run_evidence.json").read_text())\n'
      '(out/"end_state.json").write_text(json.dumps({"result":"*","termination":"max_halfmoves","played_halfmoves":ev["played_halfmoves"],"final_fen":ev["final_fen"]}))\n'
      'print("[+1.480s] JOSHUA SELF-PLAY END plies=10",flush=True)\n')
    fake.chmod(0o755)
    cmd=[str(manager),'--engine',str(fake),'--output',str(root/'sessions'),
         '--max-games','1','--progress-seconds','1','--opening','fixed',
         '--first-move','e2e4']
    res=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
    assert res.returncode==0,(res.stdout,res.stderr)
    for token in ('GAME_START 1','OPENING game=1','SEARCH game=1 ply=2',
                  'HEARTBEAT game=1','DIVERSITY game=1','MOVE game=1 ply=2',
                  'ENGINE_END game=1','GAME_END 1','ARCHIVE_COMMITTED'):
        assert token in res.stdout,(token,res.stdout)
    with zipfile.ZipFile(root/'sessions'/'archives'/'game_000001.zip') as z:
        assert z.testzip() is None
        assert 'game_console.log' in z.namelist()
        assert 'JOSHUA PLAYED BLACK' in z.read('game_console.log').decode()
    print('V8_PROGRESS_MOCK_TEST_PASS heartbeat search move diversity zip_archive')
