#!/usr/bin/env python3
"""Verify all 4-ply challenger opening lines with the genuine referee."""
import argparse,importlib.util,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--referee',required=True);p.add_argument('--scripts',required=True)
a=p.parse_args()
sys.path.insert(0,a.scripts)
import v11_champion_gate as gate
from stockfish_match import START
seen=set()
for name,line in gate.CHALLENGE_LINES.items():
 assert len(line)==4
 fen=START
 for uci in line:
  r=subprocess.run([a.referee,'--fen',fen,'--move',uci],capture_output=True,text=True)
  assert r.returncode==0,(name,uci,r.stderr)
  fen=r.stdout.splitlines()[0]
 assert ' w ' in fen,(name,fen)
 assert fen not in seen,name
 seen.add(fen)
 print('V12_VERIFIED_OPENING',name,fen)
assert len(seen)==6
print('V12_SIX_BALANCED_LINES_PASS')
