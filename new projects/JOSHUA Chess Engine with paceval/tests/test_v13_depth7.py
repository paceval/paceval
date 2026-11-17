#!/usr/bin/env python3
"""Reproducible genuine-paceval depth-7 and graph-fusion regression.
These are functional checks, not a claim of improved chess playing strength.
"""
import argparse,csv,json,os,subprocess,tempfile
from pathlib import Path

FEN='8/7k/8/8/8/6K1/7P/8 w - - 0 1'

def play(binary, graph, out, extra, fen=FEN):
    command=[str(binary),'--mode','alphabeta','--model','4','--depth','7',
       '--quiescence','2','--search-ms','22000','--search-nodes','1000000',
       '--plies','1','--graph-file',str(graph),'--fen',fen,
       '--no-board','--output',str(out)]+extra
    r=subprocess.run(command,capture_output=True,text=True,timeout=42)
    if r.returncode:raise AssertionError(str(command)+'\n'+r.stdout[-1300:]+'\n'+r.stderr[-500:])
    with (out/'selfplay_timeline.csv').open() as f:row=list(csv.DictReader(f))
    assert len(row)==1
    with (out/'root_move_rankings.csv').open() as f:rank=list(csv.DictReader(f))
    with (out/'run_evidence.json').open() as f:evidence=json.load(f)
    return row[0],rank,evidence,r.stdout

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--joshua',type=Path,required=True);ap.add_argument('--graph',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    # No evidence inferred from a preexisting file. Use a nonzero approved term.
    text=a.graph.read_text();text=text.replace('version\t0','version\t103')
    text+='\nfeature.king_tactics\t0.5000\n'
    graph=a.output/'depth7_test_graph.tsv';graph.write_text(text)
    first,rank1,e1,log1=play(a.joshua,graph,a.output/'fused',[])
    second,rank2,e2,log2=play(a.joshua,graph,a.output/'unfused',['--no-fused-adaptive'])
    assert first['search_depth_actual']=='7' and second['search_depth_actual']=='7'
    assert first['search_requested_depth']=='7' and first['search_budget_stop']=='none'
    assert first['chosen_uci']==second['chosen_uci']
    assert [v['uci'] for v in rank1]==[v['uci'] for v in rank2]
    assert max(abs(float(x['white_score_cp'])-float(y['white_score_cp'])) for x,y in zip(rank1,rank2)) < 1e-6
    assert e1['v13_fused_adaptive_graph'] is True and e2['v13_fused_adaptive_graph'] is False
    assert e1['adaptive_graph_evaluations']>0
    assert (a.output/'fused'/'paceval_v13_fused_score.txt').is_file()
    with (a.output/'fused'/'paceval_all_graphs.csv').open() as f:
        catalog=list(csv.DictReader(f))
    fused_graphs=[r for r in catalog if 'h0' in r['variables'] and 'kingDanger' in r['variables']]
    assert fused_graphs and any(int(r['evaluated_points'])>0 for r in fused_graphs)
    fallback,_,ev,log=play(a.joshua,graph,a.output/'budget',
      ['--search-nodes','4500'],fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    assert 1<=int(fallback['search_depth_actual'])<7 and fallback['search_budget_stop']=='nodes'
    assert 'SEARCH_BUDGET_STOP' in log
    assert ev['v13_search_requested_depth']==7
    report={'status':'PASS','sdk':'original external paceval library','requested_depth':7,
      'actual_depth_test':int(first['search_depth_actual']),
      'quiescence_depth':2,'fused_unfused_root_values':'AGREE',
      'fused_graph_registered_executed':True,
      'fused_graphs_total':len(fused_graphs),
      'budget_case_completed_depth':int(fallback['search_depth_actual']),
      'budget_stop_reason':fallback['search_budget_stop'],
      'playing_strength_improvement':'NOT_ESTABLISHED'}
    (a.output/'V13_TEST_EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n')
    print('JOSHUA_V13_DEPTH7_REAL_PACEVAL_PASS',json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
