#!/usr/bin/env python3
"""Export currently retained game ZIPs and the latest match/model summaries.

The export is a manual point-in-time snapshot. Keep the output outside the
session directory; it is not part of the managed 25 MB archive rotation.
"""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

p = argparse.ArgumentParser()
p.add_argument('--session', type=Path, default=Path('stockfish_sessions'))
p.add_argument('--output', type=Path, default=Path('JOSHUA_V9_Stockfish_Logs_For_Analysis.zip'))
a = p.parse_args()
a.session = a.session.resolve()
a.output = a.output.resolve()
if not a.session.is_dir():
    p.error('Session folder not found')
if a.output.is_relative_to(a.session):
    p.error('Export must be outside the rotating session folder')
files = sorted((a.session/'archives').glob('game_*.zip'))
files += [a.session / name for name in ('strength_summary.json','match_index.json','active_graph.tsv',
                                        'next_game_id.txt','latest_game.txt','last_archive_debug.log')
          if (a.session/name).is_file()]
with ZipFile(a.output, 'w', compression=ZIP_DEFLATED, compresslevel=6) as z:
    for f in files:
        z.write(f, f.relative_to(a.session))
with ZipFile(a.output) as z:
    if z.testzip() is not None:
        raise SystemExit('Export archive failed CRC verification')
print(f'Exported {len(files)} files into {a.output}')
