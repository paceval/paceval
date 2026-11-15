#!/usr/bin/env python3
"""Independent ZIP32, CRC, restart, rollover and active-size tests.

All engines used here are marked mock fixture generators, not paceval.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

manager=Path(sys.argv[1]).resolve()
fixture=Path(sys.argv[2]).resolve()
assert manager.is_file() and fixture.is_dir()
with tempfile.TemporaryDirectory(prefix='joshua_v7_test_') as d:
    base=Path(d)
    fake=base/'offline_fixture_engine.py'
    fake.write_text('#!/usr/bin/env python3\n'
        'from pathlib import Path\nimport sys,shutil,os,time,json\n'
        f'fixture=Path({str(fixture)!r})\n'
        'args=sys.argv; out=Path(args[args.index("--output")+1]); out.mkdir(parents=True,exist_ok=True)\n'
        'for name in ("selfplay_timeline.csv","root_move_rankings.csv","run_evidence.json","game_uci.txt"):\n'
        '  shutil.copyfile(fixture/name,out/name)\n'
        'data=json.loads((out/"run_evidence.json").read_text())\n'
        '(out/"end_state.json").write_text(json.dumps(dict(result="*",termination="max_halfmoves",played_halfmoves=data["played_halfmoves"],final_fen=data["final_fen"])))\n'
        '(out/"extra_random_trace.bin").write_bytes(os.urandom(int(os.environ.get("JOSHUA_TEST_TRACE_BYTES","5600"))))\n')
    fake.chmod(0o755)
    root=base/'sessions'
    common=[str(manager),'--engine',str(fake),'--output',str(root),
            '--log-limit-bytes','65000','--max-active-bytes','500000']
    def invoke(*extra, expect=0):
        p=subprocess.run([*common,*extra],capture_output=True,text=True,timeout=30)
        assert p.returncode==expect,(p.returncode,p.stdout,p.stderr)
        return p
    r=invoke('--max-games','5')
    zips=sorted((root/'archives').glob('game_*.zip'))
    assert zips and len(zips)<5, [z.name for z in zips]
    assert zips[-1].name=='game_000005.zip', [z.name for z in zips]
    assert zips[0].name!='game_000001.zip', [z.name for z in zips]
    for z in zips:
        with zipfile.ZipFile(z) as archive:
            assert archive.testzip() is None, z.name
            names=set(archive.namelist())
            assert {'learning_report.md','learning_event.jsonl','analysis_queue.csv',
                    'root_move_rankings.csv','selfplay_timeline.csv','extra_random_trace.bin','end_state.json'}<=names
            events=json.loads(archive.read('learning_event.jsonl'))
            assert events['game']==int(z.stem[5:]),z.name
            assert events['termination']=='max_halfmoves'
    assert not list(root.glob('game_*/'))
    total=sum(p.stat().st_size for p in (root/'archives').glob('game_*.zip'))
    snapshot_names=['learning_log.md','learning_events.jsonl','games_index.csv','analysis_queue.csv',
                    'manager_errors.log','next_game_id.txt','retention_status.json']
    total+=sum((root/p).stat().st_size for p in snapshot_names if (root/p).exists())
    assert total<=65000,total
    assert json.loads((root/'learning_events.jsonl').read_text())['game']==5
    assert len(list(csv.DictReader((root/'games_index.csv').open())))==1
    # Archived sequence numbers never repeat even after older ZIP files disappear.
    invoke('--max-games','2')
    assert (root/'next_game_id.txt').read_text().strip()=='8'
    assert (root/'archives'/'game_000007.zip').exists()
    assert not (root/'archives'/'game_000001.zip').exists()
    # An archive that cannot fit by itself is safely discarded after the raw
    # game has been released; a bounded latest-game summary remains.
    oversize=base/'too_small'
    q=subprocess.run([str(manager),'--engine',str(fake),'--output',str(oversize),
                       '--log-limit-bytes','50000','--max-games','1'],capture_output=True,text=True,timeout=30,env={**os.environ,'JOSHUA_TEST_TRACE_BYTES':'100000'})
    assert q.returncode==0,(q.stdout,q.stderr)
    assert not list((oversize/'archives').glob('game_*.zip'))
    assert 'latest_retained=no' in q.stdout
    assert (oversize/'learning_log.md').exists()
    assert not (oversize/'game_000001').exists()
    # A runaway child cannot build unlimited raw logs while the supervisor waits.
    huge=base/'huge_engine.py';huge.write_text('#!/usr/bin/env python3\n'
        'import sys,time,os\nfrom pathlib import Path\n'
        'a=sys.argv;out=Path(a[a.index("--output")+1]);out.mkdir(parents=True,exist_ok=True)\n'
        '(out/"huge_file.bin").write_bytes(os.urandom(1300000))\n'
        'time.sleep(4)\n');huge.chmod(0o755)
    limited=base/'active_limit'
    p=subprocess.run([str(manager),'--engine',str(huge),'--output',str(limited),
                      '--max-active-bytes','500000','--max-games','1'],capture_output=True,text=True,timeout=10)
    assert p.returncode==98,(p.returncode,p.stdout,p.stderr)
    assert (limited/'archives'/'game_000001.zip').exists()
    assert not (limited/'game_000001').exists()
    with zipfile.ZipFile(limited/'archives'/'game_000001.zip') as z:
        assert z.testzip() is None
        assert 'incomplete_game.txt' in z.namelist()
    print('V7_ZIP_RETENTION_PASS CRC32 7games oldest_pruned 65000byte_budget monotonic_ids 50000byte_oversize active_limit failure_archive')
