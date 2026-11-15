#!/usr/bin/env python3
"""Rebuild the full legal decision graph before EACH move (local paceval only).

Launches the compiled C++ binary for every ply. The C++ engine returns its
actual selected legal move and resulting FEN; Python does not choose moves.
"""
from pathlib import Path
import argparse,csv,json,subprocess,time

def run(binary,output,depth,model,plies,max_nodes=25000,max_chars=2500000):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    board='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    start=time.monotonic();rows=[];uci=[];traces=[]
    for ply in range(plies):
        current=output/f'ply_{ply+1:02d}'
        args=[str(binary),'--depth',str(depth),'--model',str(model),
              '--fen',board,'--max-nodes',str(max_nodes),
              '--max-chars',str(max_chars),'--output',str(current)]
        begun=time.monotonic()-start
        result=subprocess.run(args,capture_output=True,text=True)
        traces.append(f'===== PLY {ply+1} BEGIN elapsed={begun:.6f}s =====\n'+result.stdout+result.stderr)
        if result.returncode:
            raise RuntimeError(f'Graph building failed at ply {ply+1}: {result.stderr[-800:]}')
        evidence=json.loads((current/'run_evidence.json').read_text())
        if not evidence['graph_result_verified'] or not evidence['reused_graph_result_verified']:
            raise RuntimeError('Mathematical graph validation missing')
        chosen=evidence['selected_move'];newboard=evidence['fen_after']
        uci.append(chosen)
        rows.append({'ply':ply+1,'side':'white' if ' w ' in board else 'black',
          'elapsed_seconds':round(time.monotonic()-start,6),
          'move_uci':chosen,'depth':depth,'model':model,
          'graph_characters':evidence['graph_characters'],
          'search_nodes':evidence['nodes'],
          'distinct_leaf_inputs':evidence['unique_feature_vectors'],
          'paceval_value_cp':evidence['paceval_value_cp'],
          'graph_creation_seconds':evidence['paceval_graph_creation_seconds'],
          'graph_evaluation_seconds':evidence['paceval_graph_evaluation_seconds'],
          'fen_before':board,'fen_after':newboard})
        board=newboard
    with (output/'selfplay_timeline.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    (output/'selfplay_console.txt').write_text('\n'.join(traces))
    (output/'game_uci.txt').write_text(' '.join(uci)+'\nfinal_fen '+board+'\n')
    summary={'played_plies':len(rows),'depth':depth,'model':model,'mcp_used':False,
      'paceval_local_graphs_per_move':True,
      'total_graph_characters_generated':sum(r['graph_characters'] for r in rows),
      'elapsed_seconds':time.monotonic()-start,'final_fen':board,
      'independent_minimax_checks_passed':len(rows),
      'reused_graph_checks_passed':len(rows)}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('JOSHUA V5 LONG-GRAPH SELFPLAY PASS:',json.dumps(summary))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--depth',type=int,default=3)
    p.add_argument('--model',type=int,default=4)
    p.add_argument('--plies',type=int,default=4)
    p.add_argument('--max-nodes',type=int,default=25000)
    p.add_argument('--max-chars',type=int,default=2500000)
    a=p.parse_args();run(a.binary,a.output,a.depth,a.model,a.plies,a.max_nodes,a.max_chars)
