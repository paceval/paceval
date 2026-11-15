#!/usr/bin/env python3
"""On-demand bundle of retained JOSHUA per-game ZIPs for later review.

The always-on C++ program does not use Python for ZIP compression; this
optional convenience command only assembles existing, already-compressed ZIPs.
"""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

p=argparse.ArgumentParser()
p.add_argument('--session',type=Path,default=Path('sessions'))
p.add_argument('--output',type=Path,default=Path('JOSHUA_Logs_For_Analysis.zip'))
a=p.parse_args()
source=a.session.resolve()
target=a.output.resolve()
archives=sorted((source/'archives').glob('game_*.zip'))
if not archives:
    raise SystemExit('There are no retained game ZIPs to export.')
if target.exists():
    raise SystemExit(f'Refusing to overwrite existing export: {target}')
if target.is_relative_to(source):
    raise SystemExit('Write the export outside the session folder to avoid quota confusion.')
with ZipFile(target,'w',allowZip64=True) as output:
    for f in archives:
        output.write(f,'archives/'+f.name,compress_type=ZIP_STORED)
    for name in ('learning_log.md','learning_events.jsonl','games_index.csv',
                 'analysis_queue.csv','retention_status.json','next_game_id.txt'):
        f=source/name
        if f.is_file(): output.write(f,name,compress_type=ZIP_DEFLATED)
print(f'Exported {len(archives)} retained game ZIPs to {target} ({target.stat().st_size} bytes)')
