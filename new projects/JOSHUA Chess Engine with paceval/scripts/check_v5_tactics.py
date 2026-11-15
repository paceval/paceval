#!/usr/bin/env python3
"""Regression on the historically recorded 15...Nxe5 material-loss episode.

This is a narrow deterministic diagnosis, not an independent engine-strength claim.
"""
import csv,json,sys
from pathlib import Path
base=Path(sys.argv[1]);a=base/'position_15_black_q0';b=base/'position_15_black_q2'
def chosen(path):
    rows=list(csv.DictReader((path/'selfplay_timeline.csv').open()))
    assert len(rows)==1
    row=rows[0]
    assert row['side']=='black'
    assert int(row['legal_root_moves'])>10
    assert row['fen_before']==list(csv.DictReader(Path(sys.argv[2]).open()))[29]['fen_before']
    return row['chosen_uci']
m0=chosen(a);m2=chosen(b)
assert m0=='c4e5',f'Historical shallow blunder changed: {m0}'
assert m2!='c4e5',f'Tactical extension failed to avoid recorded blunder: {m2}'
print(f'JOSHUA V5 TACTICAL REGRESSION PASS: no_extension={m0}, quiescence_two={m2}')
