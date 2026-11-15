#!/usr/bin/env python3
"""V10 evidence-gated, bounded tactical graph tests; optional AUTHENTIC SDK use."""
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('v10', ROOT/'scripts/stockfish_match.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FakeTeacher:
    def __init__(self,*scores):self.scores=list(scores)
    def go(self,*a,**kw):return {'score':self.scores.pop(0),'depth':8}


def test_grade():
    x=mod.stockfish_loss(FakeTeacher(('cp',0),('cp',0)), 'before','after',50)
    assert x['loss_pp']==0 and not x['mate_alert'],x
    x=mod.stockfish_loss(FakeTeacher(('cp',200),('cp',200)),'before','after',50)
    assert 40 < x['loss_pp'] < 60, x
    x=mod.stockfish_loss(FakeTeacher(('mate',3),('mate',2)),'before','after',50)
    assert x['loss_pp']==100 and x['mate_alert'],x
    x=mod.stockfish_loss(FakeTeacher(('mate',-3),('mate',2)),'before','after',50)
    assert x['loss_pp']==0 and not x['mate_alert'],x
    print('HEURISTIC_GRADE_PASS: bounded 0..100, mate alert independently recorded')


def test_graph_structure():
    with tempfile.TemporaryDirectory() as tmp:
        root=pathlib.Path(tmp)
        graph=root/'g.tsv'
        graph.write_text((ROOT/'config/active_graph.tsv').read_text()+
            'feature.king_tactics\t0.5000\nfeature.hanging_pressure\t-0.2500\n')
        got=mod.parse_model(graph)
        assert set(got['extra'])=={'king_tactics','hanging_pressure'}
        assert mod.parse_model(graph)==mod.parse_model(graph)
        assert 'feature.king_tactics\t0.5000' in mod.model_text(got)
        for injection in ('feature.evil\t1.0000\n','feature.king_tactics\tsqrt(-1)\n',
                          'feature.hanging_pressure\t500000.0000\n'):
            graph.write_text((ROOT/'config/active_graph.tsv').read_text()+injection)
            try:mod.parse_model(graph)
            except ValueError:pass
            else:raise AssertionError('Unsafe graph input accepted: '+injection)
        print('STRUCTURAL_SCHEMA_PASS: whitelisted features, bounded numeric literals')


def test_structural_promotion_policy():
    with tempfile.TemporaryDirectory() as tmp:
        root=pathlib.Path(tmp); active=root/'active.tsv'
        active.write_text((ROOT/'config/active_graph.tsv').read_text())
        class Args:
            adapt=True;training_loss_pp=7;train_positions=1;holdout_positions=1
            max_holdout_regression=2;min_improvement=1;step=.5;structural_step=.5
            referee=ROOT/'bin/joshua_referee'
        originals=mod.evaluate_model_on_fens
        def simulated(fens, model, graph_file, args, teacher, directory, logger, label):
            # Test harness deliberately substitutes deterministic reference results.
            # It tests controller gates only, never authentic chess improvement.
            out=[]
            for i,_ in enumerate(fens):
                folder=directory/f'{label}_{i}';folder.mkdir(parents=True,exist_ok=True)
                (folder/'paceval_graph.txt').write_text(f'version={model["version"]}\nexpression=MOCK_TEST_ONLY\n')
                (folder/'paceval_graph_terms.csv').write_text('version,category,term,coefficient,paceval_expression\n')
                value=model.get('extra',{}).get('king_tactics',0)
                loss=60+20*value if i==0 else 10.
                out.append({'loss_pp':loss,'chosen_uci':'a2a4' if value<0 else 'e2e4','graph_folder':str(folder)})
            return out
        mod.evaluate_model_on_fens=simulated
        logger=mod.Logger(root/'debug.log',1)
        try:
            report=mod.adjust_graph(2,[{'fen_before':mod.START,'loss_pp':60,'mate_alert':True}],
                                    active,None,Args(),root,logger)
            assert report['status']=='promoted_provisional',report
            changed=mod.parse_model(active)
            assert changed['version']==1 and changed['extra']['king_tactics']==-.5,changed
            assert (root/'active_graph_expression.txt').is_file()
            print('STRUCTURAL_PROMOTION_GATE_PASS: MOCK candidate accepted; real chess strength not asserted')
        finally:
            logger.close();mod.evaluate_model_on_fens=originals


def test_strength_comparison():
    data=[]
    for v in (0,1):
        for i,opening in enumerate(mod.OPENINGS[:8]):
            for color in (0,1):
                gid = i*2 + color + 1 + (0 if v==0 else 28)
                # The sign test exercises paired opening comparison only.
                # Simulated points are NOT authentic chess results.
                data.append({'game':gid, 'graph_version':v,'opening_book':opening,
                             'white':'Stockfish' if not color else 'JOSHUA',
                             'joshua_points':0. if v==0 else 1.,
                             'result':'0-1' if v==0 and color else ('1-0' if v==0 else ('0-1' if color else '1-0')),
                             'stockfish_id':'FIXED_MOCK','stockfish_nodes':1000,
                             'stockfish_skill':20,'joshua_depth':2,'quiescence':2})
    report=mod.summary_metrics(data)
    assert report['version_comparisons'][-1]['status']=='BETTER_ON_COMPARED_OPENINGS_PROVISIONAL',report
    assert report['version_comparisons'][-1]['matched_distinct_openings']==8
    for row in data:
        if row['graph_version']==1:
            row['joshua_points']=0.
    report=mod.summary_metrics(data)
    assert report['version_comparisons'][-1]['status']=='NOT_ESTABLISHED', report
    print('STRENGTH_COMPARISON_PASS: color-paired distinct openings; mock data only')

def test_real_paceval_optional():
    lib=os.environ.get('PACEVAL_RUNTIME')
    binary=ROOT/'bin/joshua'
    if not lib or not pathlib.Path(lib).is_file() or not binary.exists():
        print('REAL_PACEVAL_TEST_SKIPPED: set PACEVAL_RUNTIME for authentic integration')
        return
    with tempfile.TemporaryDirectory() as tmp:
        root=pathlib.Path(tmp)
        graph=root/'candidate.tsv'
        graph.write_text((ROOT/'config/active_graph.tsv').read_text()+
                         'feature.king_tactics\t0.5000\nfeature.hanging_pressure\t-0.2500\n')
        p=subprocess.run([str(binary),'--graph-file',str(graph),'--model','4',
                          '--depth','1','--plies','1','--no-board','--output',str(root/'run')],
                          capture_output=True,text=True,timeout=60)
        assert p.returncode==0,(p.stderr,p.stdout)
        evidence=json.loads((root/'run/run_evidence.json').read_text())
        assert evidence['adaptive_graph_evaluations']>0,evidence
        assert 'bkingDanger' in (root/'run/paceval_graph.txt').read_text()
        import csv
        with (root/'run/paceval_all_graphs.csv').open() as f:all_graphs=list(csv.DictReader(f))
        assert any(int(g['evaluated_points'])>0 and 'bkingDanger*' in g['paceval_expression']
                   for g in all_graphs), 'Nonlinear mathematical graph not evaluated'
        assert sum(int(g['evaluated_points']) for g in all_graphs) == evidence['paceval_graph_point_evaluations']
        print('AUTHENTIC_PACEVAL_GRAPH_PASS: nonlinears executed; full graph registry reconciles')


if __name__ == '__main__':
    test_grade()
    test_graph_structure()
    test_structural_promotion_policy()
    test_strength_comparison()
    test_real_paceval_optional()
