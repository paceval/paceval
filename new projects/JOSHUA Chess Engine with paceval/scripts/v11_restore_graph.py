#!/usr/bin/env python3
"""Manually restore a frozen model version. Does not prove increased strength.
Requires --apply and no active game; creates a byte-for-byte backup first.
No source recompilation is needed. If a historical version is restored,
the next new version ID remains strictly higher than all retained snapshots.
"""
import argparse
import os
from pathlib import Path
from datetime import datetime,timezone


def restore(sessions:Path,version:int,apply:bool):
    sessions=sessions.resolve(); active=sessions/'active_graph.tsv'
    if (sessions/'current_game').exists():
        raise RuntimeError('Refusing restoration while current_game exists. Stop match safely first.')
    source=sessions/'model_versions'/f'version_{version:07d}.tsv'
    if not source.is_file():raise FileNotFoundError(f'Model revision missing: {source}')
    if not active.is_file():raise FileNotFoundError(f'Active model missing: {active}')
    # The same schema parser used for every real Joshua evaluation.
    from stockfish_match import parse_model,atomic_text,utc
    before=parse_model(active);after=parse_model(source)
    if after['version'] != version:raise RuntimeError('Snapshot version and filename differ')
    label=f'{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{os.getpid()}'
    audit={'previous_version':before['version'],'restored_version':version,'time_utc':utc(),
           'backup':str(sessions/'model_versions'/f'pre_rollback_{label}.tsv'),'applied':bool(apply)}
    if apply:
        backup=Path(audit['backup']);backup.write_bytes(active.read_bytes())
        atomic_text(active, source.read_text(encoding='utf-8'))
        atomic_text(sessions/'last_model_restore.json', __import__('json').dumps(audit,indent=2)+'\n')
    return audit

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--sessions',type=Path,default=Path('stockfish_sessions'))
    p.add_argument('--version',type=int,required=True)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    try:print(restore(a.sessions,a.version,a.apply))
    except Exception as e:p.error(str(e))
