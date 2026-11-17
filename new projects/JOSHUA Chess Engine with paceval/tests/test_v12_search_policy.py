#!/usr/bin/env python3
"""V12 authentic paceval search-policy regression. No Stockfish strength claim."""
import argparse,csv,json,os,subprocess,tempfile
from pathlib import Path

POSITIONS = [
 ('game1_ply6', 'rnbqkb1r/pppppppp/8/4P3/4n3/3P4/PPP2PPP/RNBQKBNR b KQkq - 0 3', 'd7d6'),
 ('game2_ply9', 'r1bqkbnr/ppp2ppp/2n5/4p3/3pP3/5N2/PPPPNPPP/R1BQKB1R w KQkq - 2 5', 'c2c4'),
 ('game2_ply15','r2qkbnr/pppb1ppp/8/4p3/QnP1P3/3p1NN1/PP1P1PPP/R1B1KB1R w KQkq - 4 8', 'a4d7'),
]

def cli():
 p=argparse.ArgumentParser()
 p.add_argument('--joshua',required=True,type=Path)
 p.add_argument('--referee',required=True,type=Path)
 p.add_argument('--graph',required=True,type=Path)
 p.add_argument('--results',required=True,type=Path)
 p.add_argument('--all',action='store_true')
 return p.parse_args()

def run(args,label,fen,depth,verify,folder):
 command=[str(args.joshua),'--model','4','--mode','alphabeta','--depth',str(depth),
  '--quiescence','2','--plies','1','--fen',fen,'--graph-file',str(args.graph),
  '--verify-margin-cp',str(25 if verify else 0),
  '--verify-extra-depth',str(1 if verify else 0),
  '--no-board','--output',str(folder)]
 p=subprocess.run(command,capture_output=True,text=True,timeout=80)
 if p.returncode:raise AssertionError((label,p.returncode,p.stdout[-700:],p.stderr[-400:]))
 with (folder/'selfplay_timeline.csv').open(newline='') as handle:
  rows=list(csv.DictReader(handle))
 assert len(rows)==1,(label,rows)
 row=rows[0]
 evidence=json.loads((folder/'run_evidence.json').read_text())
 assert evidence['adaptive_graph_evaluations']>0
 assert evidence['paceval_graph_point_evaluations']>0
 ref=subprocess.run([str(args.referee),'--fen',fen,'--move',row['chosen_uci']],
   capture_output=True,text=True,timeout=15)
 assert ref.returncode==0,(label,ref.stderr)
 return row,evidence

def test():
 args=cli();cases=POSITIONS if args.all else POSITIONS[:1]
 args.results.mkdir(parents=True,exist_ok=True)
 report=[]
 for name,fen,old in cases:
  shallow, ev0=run(args,name+'_depth2',fen,2,False,args.results/(name+'_depth2'))
  verified, ev1=run(args,name+'_verify',fen,2,True,args.results/(name+'_verify'))
  deep, ev2=run(args,name+'_depth3',fen,3,False,args.results/(name+'_depth3'))
  assert shallow['chosen_uci']==old,(name,shallow['chosen_uci'],old)
  assert verified['chosen_uci']==deep['chosen_uci'],name
  assert verified['verify_triggered']=='1'
  assert verified['search_depth_actual']=='3'
  assert verified['preverify_best_uci']==shallow['chosen_uci']
  assert ev1['v12_verified_moves']==1
  assert ev1['v12_verified_decisions_changed']==int(verified['chosen_uci'] != old)
  report.append({'case':name,'source':'uploaded real Stockfish match log, independently replayed',
    'recorded_V11_move':old,'shallow_V12_move':shallow['chosen_uci'],
    'V12_verified_move':verified['chosen_uci'],'independent_V12_depth3_move':deep['chosen_uci'],
    'changed':verified['chosen_uci']!=old,'verified_graph_points':ev1['paceval_graph_point_evaluations'],
    'verified_adaptive_evaluations':ev1['adaptive_graph_evaluations']})
 (args.results/'v12_regression.json').write_text(json.dumps(report,indent=2)+'\n')
 print('V12_REAL_PACEVAL_REGRESSION_PASS',json.dumps(report))

if __name__=='__main__':test()
