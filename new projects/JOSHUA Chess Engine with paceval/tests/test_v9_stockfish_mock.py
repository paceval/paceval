#!/usr/bin/env python3
"""OFFLINE protocol mock. It does NOT test authentic Stockfish or paceval.

The actual Joshua binary is never replaced in production. The two explicitly
marked fake executables exercise orchestration, referee, logs, color rotation,
ZIP retention and adaptive model policy without a proprietary SDK installation.
"""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'scripts/stockfish_match.py'
REFEREE = ROOT / 'bin/joshua_referee'
assert REFEREE.exists(), 'Build joshua_referee before offline tests'

MOCK_MOVES = '''e7e5 e2e4 d7d5 d2d4 g8f6 g1f3 b8c6 b1c3 c7c5 c2c4 f8c5 f1c4
d8e7 d1e2 a7a6 a2a3 h7h6 h2h3 e5e4 e4e5 c5d4 d4c5 f6e4 f3e5 g7g6 g2g3
b7b6 b2b3 a8a7 a1a2 h8h7 h1h2 c8b7 c1b2 e8e7 e1e2 b7a6'''.split()

UCI_MOCK = r'''#!/usr/bin/env python3
import os,sys,subprocess
ref=os.environ['MOCK_REFEREE']
fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
moves=os.environ['MOCK_MOVES'].split()
def choose():
 for move in moves:
  r=subprocess.run([ref,'--fen',fen,'--move',move],capture_output=True,text=True)
  if r.returncode==0:return move
 return '(none)'
for line in sys.stdin:
 command=line.strip()
 if command=='uci':print('id name OFFLINE MOCK STOCKFISH NOT AUTHENTIC',flush=True);print('uciok',flush=True)
 elif command=='isready':print('readyok',flush=True)
 elif command.startswith('position fen '):fen=command[13:]
 elif command.startswith('go '):
  print('info depth 2 score cp 0 nodes 50',flush=True)
  print('bestmove '+choose(),flush=True)
 elif command=='quit':break
'''
JOSHUA_MOCK = r'''#!/usr/bin/env python3
import os,sys,subprocess,json,csv,pathlib
args=sys.argv[1:]
def opt(x):return args[args.index(x)+1]
fen=opt('--fen');out=pathlib.Path(opt('--output'));out.mkdir(parents=True,exist_ok=True)
ref=os.environ['MOCK_REFEREE'];moves=os.environ['MOCK_MOVES'].split()
move=None;fena=None
for m in moves:
 p=subprocess.run([ref,'--fen',fen,'--move',m],capture_output=True,text=True)
 if p.returncode==0:move=m;fena=p.stdout.splitlines()[0];break
if move is None:sys.exit(9)
with (out/'selfplay_timeline.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['chosen_uci','white_score_cp']);w.writeheader();w.writerow({'chosen_uci':move,'white_score_cp':0})
(out/'run_evidence.json').write_text(json.dumps({'adaptive_graph_version':int(next(x.split('\t')[1] for x in pathlib.Path(opt('--graph-file')).read_text().splitlines() if x.startswith('version\t'))), 'adaptive_graph_evaluations':1,'paceval_graph_point_evaluations':1}))
print('MOCK_JOSHUA_MOVE',move,flush=True)
'''


def mkexec(path, code):
    path.write_text(code)
    path.chmod(0o755)


def test_match():
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        stockfish = tmp / 'mock_stockfish'
        joshua = tmp / 'mock_joshua'
        lib = tmp / 'MOCK_NOT_A_REAL_PACEVAL_LIBRARY.so'
        lib.write_text('NOT A LIBRARY; OFFLINE PROTOCOL TEST ONLY')
        mkexec(stockfish, UCI_MOCK)
        mkexec(joshua, JOSHUA_MOCK)
        env = dict(os.environ, MOCK_REFEREE=str(REFEREE), MOCK_MOVES=' '.join(MOCK_MOVES))
        proc = subprocess.run([sys.executable, str(SCRIPT), '--stockfish', str(stockfish), '--joshua', str(joshua),
                               '--referee', str(REFEREE), '--paceval-runtime', str(lib),
                               '--max-games', '2', '--max-plies', '5', '--output', str(tmp / 'sessions'),
                               '--stockfish-nodes', '50', '--teacher-nodes', '50',
                               '--progress-seconds', '1', '--move-timeout', '5', '--max-logs-mb', '0.2'],
                              capture_output=True, text=True, env=env, timeout=100)
        if proc.returncode:
            raise AssertionError(f'Mock V9 match failure: {proc.stderr}\n{proc.stdout}')
        assert 'delta_s=' in proc.stdout and 'elapsed_s=' in proc.stdout and 'move_s=' in proc.stdout, proc.stdout
        archives = sorted((tmp / 'sessions/archives').glob('game_*.zip'))
        assert len(archives) == 2, archives
        pairs = []
        for archive in archives:
            with zipfile.ZipFile(archive) as z:
                assert z.testzip() is None
                summary = json.loads(z.read('summary.json'))
                moves = json.loads(z.read('moves.json'))
                assert all(isinstance(m['move_s'], (int, float)) for m in moves)
                assert 'delta_s=' in z.read('debug_timeline.log').decode()
                assert 'move_s=' in z.read('debug_timeline.log').decode()
                assert summary['model_used'] == 0
                assert 'adaptation.json' in z.namelist()
                assert '1. ' in z.read('game.pgn').decode()
                assert 'e4e5' not in z.read('game.pgn').decode()
                assert summary['termination'] == 'max_plies_unfinished', summary
                pairs.append((summary['white'], summary['black']))
        assert pairs == [('Stockfish', 'JOSHUA'), ('JOSHUA', 'Stockfish')], pairs
        assert (tmp / 'sessions/next_game_id.txt').read_text().strip() == '3'
        # One-third of retention under forced small budget. Oldest-first deletion.
        from importlib.util import module_from_spec, spec_from_file_location
        spec = spec_from_file_location('joshua_match', SCRIPT)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger = mod.Logger(tmp/'rotate.log', 1)
        try:
            current = mod.file_footprint(archives[-1])
            retained = mod.rotate(tmp / 'sessions/archives', current+512, logger)
            assert retained <= current+512
            assert len(list((tmp / 'sessions/archives').glob('*.zip'))) == 1
        finally:
            logger.close()
        print('V9_OFFLINE_PROTOCOL_MOCK_PASS: 2 colors, real C++ legal referee, per-move delta_s/elapsed_s/move_s, ZIP CRC, oldest-first retention')


def test_model_validation():
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location('joshua_match_model', SCRIPT)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        active = tmp / 'active.tsv'
        active.write_text((ROOT/'config/active_graph.tsv').read_text())
        m = mod.parse_model(active)
        assert m['version'] == 0
        assert set(m['weights']) == set(mod.TERMS)
        # Mutation of formulas is disallowed; only predefined bounded coefficients.
        active.write_text(active.read_text() + 'unsafe_formula\tsqrt(-1)\n')
        try:
            mod.parse_model(active)
        except ValueError:
            pass
        else:
            raise AssertionError('Free-form expression injection accepted')
        active.write_text((ROOT/'config/active_graph.tsv').read_text())
        # These are fake trials, not Stockfish measurements, verifying the gate itself.
        class Args:
            adapt=True
            training_loss_cp=35
            train_positions=1
            holdout_positions=1
            max_holdout_regression=5
            min_improvement=1
            step=.5
            referee=REFEREE
        args = Args()
        originals = mod.evaluate_model_on_fens
        def fake_trials(fens, model, graphfile, args, teacher, folder, logger, label):
            # Baseline losses: train 100, holdout 10. Negative direction helps train;
            # positive direction hurts it. Heldout loss is unchanged, so the
            # selection policy should permit only the negative candidate.
            value = model['weights']['mobility']
            return [{'cp_loss': (100+20*value if i==0 else 10.0),
                     'chosen_uci': 'e2e4' if value==0 else 'd2d4'} for i,_ in enumerate(fens)]
        mod.evaluate_model_on_fens = fake_trials
        logger = mod.Logger(tmp/'log.txt', 1)
        try:
            report = mod.adjust_graph(1, [{'fen_before':mod.START, 'cp_loss':100}], active,
                                      None, args, tmp, logger)
            assert report['status'] == 'promoted', report
            assert mod.parse_model(active)['version'] == 1
            assert mod.parse_model(active)['weights']['mobility'] == -.5
        finally:
            logger.close()
            mod.evaluate_model_on_fens = originals
        print('V9_OFFLINE_ADAPTIVE_POLICY_MOCK_PASS: bounded coefficients, promoted only after independent heldout check')


if __name__ == '__main__':
    test_match()
    test_model_validation()
