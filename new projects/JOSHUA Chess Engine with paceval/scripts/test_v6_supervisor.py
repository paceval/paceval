#!/usr/bin/env python3
"""Offline process-management regression, NOT a paceval game execution test."""
from pathlib import Path
import tempfile, shutil, subprocess, json, csv, sys, textwrap, time, signal
supervisor=Path(sys.argv[1]).resolve()
fixture=Path(sys.argv[2]).resolve()
assert supervisor.exists() and fixture.exists()
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    fake=root/'fake_engine.py'
    fake.write_text('#!/usr/bin/env python3\n'
                    'import sys, shutil, json\n'
                    'from pathlib import Path\n'
                    f'fixture=Path({str(fixture)!r})\n'
                    'args=sys.argv\n'
                    'out=Path(args[args.index("--output")+1]); out.mkdir(exist_ok=True,parents=True)\n'
                    'for name in ("selfplay_timeline.csv","root_move_rankings.csv","run_evidence.json","game_uci.txt"):\n'
                    '    shutil.copyfile(fixture/name,out/name)\n'
                    'data=json.loads((out/"run_evidence.json").read_text())\n'
                    'state={"result":"*","termination":"max_halfmoves","played_halfmoves":data["played_halfmoves"],"final_fen":data["final_fen"]}\n'
                    '(out/"end_state.json").write_text(json.dumps(state))\n')
    fake.chmod(0o755)
    output=root/'log'
    cmd=[str(supervisor),'--engine',str(fake),'--output',str(output),'--max-games','2','--depth','2','--model','4','--seed','5']
    first=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    assert first.returncode==0,(first.stdout,first.stderr)
    assert (output/'archives'/'game_000001.zip').exists()
    assert (output/'archives'/'game_000002.zip').exists()
    import zipfile
    with zipfile.ZipFile(output/'archives'/'game_000001.zip') as archive:
        assert archive.testzip() is None
        events=[json.loads(archive.read('learning_event.jsonl').decode())]
    with zipfile.ZipFile(output/'archives'/'game_000002.zip') as archive:
        assert archive.testzip() is None
        events.append(json.loads(archive.read('learning_event.jsonl').decode()))
    assert len(events)==2 and [x['game'] for x in events]==[1,2]
    assert events[0]['opening']!=events[1]['opening']
    assert events[0]['termination']=='max_halfmoves' and events[1]['result']=='*'
    second=subprocess.run([str(supervisor),'--engine',str(fake),'--output',str(output),'--max-games','1','--seed','5'],capture_output=True,text=True,timeout=30)
    assert second.returncode==0,(second.stdout,second.stderr)
    events=[json.loads(z) for z in (output/'learning_events.jsonl').read_text().splitlines()]
    assert len(events)==1 and events[-1]['game']==3
    assert sorted(p.name for p in (output/'archives').glob('game_*.zip'))==['game_000001.zip','game_000002.zip','game_000003.zip']
    assert (output/'archives'/'game_000001.zip').exists()
    # Negative test: engine error must stop the supervisor instead of spinning forever.
    broken=root/'broken_engine.sh';broken.write_text('#!/bin/sh\nexit 17\n');broken.chmod(0o755)
    failure=subprocess.run([str(supervisor),'--engine',str(broken),'--output',str(root/'bad'),'--max-games','0'],capture_output=True,text=True,timeout=10)
    assert failure.returncode==17,(failure.stdout,failure.stderr)
    assert 'exited with code 17' in (root/'bad'/'manager_errors.log').read_text()
    slow=root/'slow_engine.sh';slow.write_text('#!/bin/sh\nsleep 8\n');slow.chmod(0o755)
    interrupted=root/'interrupted'
    running=subprocess.Popen([str(supervisor),'--engine',str(slow),'--output',str(interrupted),'--max-games','0'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    time.sleep(0.15)
    running.send_signal(signal.SIGINT)
    stdout,stderr=running.communicate(timeout=10)
    assert running.returncode==0,(running.returncode,stdout,stderr)
    assert (interrupted/'archives'/'game_000001.zip').exists()
    with zipfile.ZipFile(interrupted/'archives'/'game_000001.zip') as archive:
        assert 'interrupted.txt' in archive.namelist()
    assert not (interrupted/'learning_events.jsonl').exists()
    print('V7_MANAGER_OFFLINE_TEST_PASS three_cycles resumed distinct_openings error_stops signal_graceful jsonl_no_overwrite')
