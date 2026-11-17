#!/usr/bin/env python3
"""V11 model commit/rollback policy tests. Fake Stockfish & fake duel, no strength claim."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import stockfish_match as m
import v11_champion_gate as gate
import v11_restore_graph as restore

class DummyTeacher:pass

def fake_eval(fens,model,graph_file,args,teacher,directory,logger,label):
    value=model['extra'].get('king_check_combo',0)
    results=[]
    for i,fen in enumerate(fens):
        fold=directory/f'{label}_{i}';fold.mkdir(parents=True,exist_ok=True)
        (fold/'paceval_graph.txt').write_text(f'version={model["version"]}\nexpression=MOCK_TEST_ONLY\n')
        (fold/'paceval_graph_terms.csv').write_text('version,term,coefficient\n')
        loss=(60+20*value if i==0 else 10.)
        results.append({'fen':fen,'chosen_uci':'a2a4' if value<0 else 'e2e4',
                        'loss_pp':loss,'mate_alert':False,'graph_folder':str(fold)})
    return results

def test_gateway():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);active=root/'active_graph.tsv';active.write_text((ROOT/'config/active_graph.tsv').read_text())
        options=SimpleNamespace(adapt=True,training_loss_pp=7,train_positions=1,holdout_positions=1,
            max_holdout_regression=2,min_improvement=1,step=.5,structural_step=.5,
            referee=ROOT/'bin/joshua_referee',champion_pairs=1,champion_max_plies=20,champion_min_score=.625)
        for x in ('reject','accept','after_restore'):(root/x).mkdir()
        old_eval=m.evaluate_model_on_fens;old_compare=gate.compare
        m.evaluate_model_on_fens=fake_eval
        log=m.Logger(root/'test.log',1)
        errors=[{'fen_before':m.START,'loss_pp':60.,'mate_alert':True}]
        try:
            gate.compare=lambda *a,**kw:{'accepted':False,'reason':'MOCK CHAMPION LOSS'}
            r=m.adjust_graph(2,errors,active,DummyTeacher(),options,root/'reject',log)
            assert r['status']=='rejected_after_champion_gate',r
            assert m.parse_model(active)['version']==0
            gate.compare=lambda *a,**kw:{'accepted':True,'reason':'MOCK CHAMPION VICTORY','score':.75}
            r=m.adjust_graph(2,errors,active,DummyTeacher(),options,root/'accept',log)
            assert r['status']=='promoted_provisional',r
            assert m.parse_model(active)['version']==1
            assert (root/'model_versions/version_0000000.tsv').exists()
            assert (root/'model_versions/version_0000001.tsv').exists()
            before=active.read_text()
            preview=restore.restore(root,0,False)
            assert not preview['applied'] and active.read_text()==before
            applied=restore.restore(root,0,True)
            assert applied['applied'] and m.parse_model(active)['version']==0
            assert Path(applied['backup']).read_text()==before
            gate.compare=lambda *a,**kw:{'accepted':True,'reason':'MOCK ACCEPT','score':.8}
            r=m.adjust_graph(2,errors,active,DummyTeacher(),options,root/'after_restore',log)
            assert m.parse_model(active)['version']==2, r  # No version ID reuse after rollback
            # Fail closed when an active game is in progress.
            (root/'current_game').mkdir()
            try:restore.restore(root,0,True)
            except RuntimeError:pass
            else:raise AssertionError('Restored a model while a game was active')
            print('V11_MOCK_POLICY_PASS: reject, accept, snapshot, rollback and monotonic IDs')
        finally:
            m.evaluate_model_on_fens=old_eval;gate.compare=old_compare;log.close()

if __name__=='__main__':test_gateway()
