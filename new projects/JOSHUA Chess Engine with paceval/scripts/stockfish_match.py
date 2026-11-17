#!/usr/bin/env python3
"""Joshua V12: durable Stockfish-vs-paceval Joshua matches and bounded graph evolution.

Every move is adjudicated by the compiled Joshua C++ referee, not by a simulated
chess package. Stockfish speaks UCI. Joshua runs the authentic local paceval
binary with --fen, --plies 1 and --graph-file on each of its turns.

Time stamps use time.monotonic(); delta_s is time since the *previous emitted*
DEBUG line and move_s is the complete subprocess search wall time. All moves,
graph candidates, rejections, diagnostics and the final model live in game ZIPs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import v11_champion_gate as champion_gate

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR if (SCRIPT_DIR / "joshua").exists() else SCRIPT_DIR.parent
OPENINGS = ['e2e4', 'd2d4', 'c2c4', 'g1f3', 'b1c3', 'e2e3', 'd2d3',
            'g2g3', 'b2b3', 'f2f4', 'a2a3', 'h2h3', 'a2a4', 'h2h4']
START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
TERMS = ('mobility', 'captures', 'hanging', 'attacked', 'passed', 'kingdanger', 'queenthreat', 'rookthreat')
MEMORY_LIMIT = 25_000_000
# Exact same whitelisted templates as src/adaptive_score_graph.h.
# A TSV contains only names and bounded coefficients, never executable text.
EXTRA_FORMULAS = {
    'king_alarm': '((bkingDanger*bkingDanger)-(wkingDanger*wkingDanger))',
    'king_tactics': '((bkingDanger*(1+bqueenThreat+brookThreat))-(wkingDanger*(1+wqueenThreat+wrookThreat)))',
    'hanging_pressure': '((bhanging*bhanging)-(whanging*whanging))',
    'queen_exposure': '((bqueenThreat*battacked)-(wqueenThreat*wattacked))',
    'rook_exposure': '((brookThreat*battacked)-(wrookThreat*wattacked))',
    'check_pressure': '(bcheck-wcheck)',
    'pawn_race': '((wpassed*wpassed)-(bpassed*bpassed))',
    'active_captures': '((wmob*wcaps)-(bmob*bcaps))',
    'king_check_combo': '((bcheck*(1+bkingDanger+bqueenThreat))-(wcheck*(1+wkingDanger+wqueenThreat)))',
    'hanging_capture_combo': '((bhanging*wcaps)-(whanging*bcaps))',
}
# This approximate expected-score transform is a *heuristic* rather than
# an official Stockfish WDL calibration. A forced mate is treated separately.

STOP = False

class RuntimeAPI:
    """Live access to this controller, including asynchronous STOP updates."""
    def __getattr__(self, name):
        if name not in globals(): raise AttributeError(name)
        return globals()[name]



def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def stop_handler(signum, frame):
    global STOP
    STOP = True


def atomic_text(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(value, encoding='utf-8')
    os.replace(tmp, path)


def json_write(path, data):
    atomic_text(Path(path), json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def parse_model(path: Path):
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) != 2 or parts[0] in values:
            raise ValueError('Invalid adaptive model TSV')
        values[parts[0]] = parts[1]
    if not {'version', *TERMS}.issubset(values) or not re.fullmatch(r'[0-9]{1,7}', values['version']):
        raise ValueError('Model keys or version invalid')
    if int(values['version']) > 9_999_998:
        raise ValueError('Model version rollover')
    weights = {}
    for term in TERMS:
        v = values[term]
        if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]{1,4})?|\.[0-9]{1,4})', v):
            raise ValueError('Invalid coefficient ' + term)
        value = float(v)
        if not math.isfinite(value) or abs(value) > 32:
            raise ValueError('Coefficient out of range ' + term)
        weights[term] = value
    extras = {}
    for name, value in values.items():
        if name in ('version', *TERMS):
            continue
        if not name.startswith('feature.') or name[8:] not in EXTRA_FORMULAS:
            raise ValueError('Unrecognized nonlinear graph template: ' + name)
        if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]{1,4})?|\.[0-9]{1,4})', value):
            raise ValueError('Invalid nonlinear weight: ' + name)
        number = float(value)
        if not math.isfinite(number) or abs(number) > 8:
            raise ValueError('Nonlinear weight out of range: ' + name)
        if number != 0:
            extras[name[8:]] = number
    if len(extras) > 6:
        raise ValueError('Maximum six active nonlinear terms per graph')
    return {'version': int(values['version']), 'weights': weights, 'extra': extras}


def model_text(model):
    return '# Validated decimal paceval graph coefficients. Never inject formulas here.\n' + \
           'version\t' + str(model['version']) + '\n' + \
           ''.join(f'{term}\t{model["weights"][term]:.4f}\n' for term in TERMS) + \
           ''.join(f'feature.{name}\t{value:.4f}\n' for name, value in sorted(model.get('extra', {}).items()) if value != 0)


class Logger:
    def __init__(self, path: Path, progress: int):
        self.path = path
        self.progress = max(1, progress)
        self.origin = self.previous = time.monotonic()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = path.open('a', encoding='utf-8', buffering=1)

    def event(self, label, **fields):
        now = time.monotonic()
        values = {'delta_s': round(now - self.previous, 3),
                  'elapsed_s': round(now - self.origin, 3), **fields}
        self.previous = now
        line = f'{utc()} {label} ' + ' '.join(f'{k}={json.dumps(v, ensure_ascii=False)}' for k, v in values.items())
        print(line, flush=True)
        self.f.write(line + '\n')
        if self.f.tell() > MEMORY_LIMIT // 2:
            raise RuntimeError('Active debug output exceeded 12.5 MB; stopping safely')
        return values

    def close(self):
        self.f.close()


class UCI:
    def __init__(self, binary, threads, hash_mb, timeout=45, skill=20):
        self.path = str(binary)
        self.timeout = timeout
        self.p = subprocess.Popen([self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = queue.Queue(maxsize=20000)
        self.name = ''
        self.traces = []
        def reader():
            try:
                for line in self.p.stdout:
                    if len(line) > 16384:
                        continue
                    try:
                        self.lines.put(line.strip(), timeout=2)
                    except queue.Full:
                        break
            finally:
                try:
                    self.lines.put_nowait(None)
                except queue.Full:
                    pass
        threading.Thread(target=reader, daemon=True).start()
        self.send('uci')
        for line in self.read_until('uciok', timeout):
            if line.startswith('id name '):
                self.name = line[8:]
        self.send(f'setoption name Threads value {threads}')
        self.send(f'setoption name Hash value {hash_mb}')
        self.send(f'setoption name Skill Level value {skill}')
        self.send('isready')
        self.read_until('readyok', timeout)

    def send(self, command):
        if self.p.poll() is not None:
            raise RuntimeError(f'UCI process exited with code {self.p.returncode}')
        self.p.stdin.write(command + '\n')
        self.p.stdin.flush()

    def read_until(self, prefix, timeout, heartbeat=None, heartbeat_seconds=5):
        end = time.monotonic() + timeout
        messages = []
        last_heartbeat = time.monotonic()
        while True:
            remain = end - time.monotonic()
            if remain <= 0:
                raise TimeoutError('UCI timeout waiting for ' + prefix)
            try:
                line = self.lines.get(timeout=min(remain, max(.1, heartbeat_seconds)))
            except queue.Empty:
                if heartbeat and time.monotonic() - last_heartbeat >= heartbeat_seconds:
                    heartbeat(time.monotonic())
                    last_heartbeat = time.monotonic()
                continue
            if line is None:
                raise RuntimeError('UCI process terminated waiting for ' + prefix)
            messages.append(line)
            if line.startswith(prefix):
                return messages

    def go(self, fen, nodes, logger=None, progress_seconds=5, reset_hash=False):
        if reset_hash:
            self.send('ucinewgame')
            self.send('setoption name Clear Hash')
        self.send('isready')
        self.read_until('readyok', self.timeout)
        self.send('position fen ' + fen)
        self.send(f'go nodes {nodes}')
        begin = time.monotonic()
        messages = self.read_until('bestmove ', self.timeout,
             heartbeat=(lambda now: logger.event('HEARTBEAT', engine='Stockfish', search_s=round(now - begin,3))) if logger else None,
             heartbeat_seconds=progress_seconds)
        last_score = None
        depth = None
        for line in messages:
            if not line.startswith('info ') or ' multipv ' in line and ' multipv 1 ' not in line:
                continue
            score = re.search(r'\bscore (cp|mate) (-?[0-9]+)', line)
            d = re.search(r'\bdepth ([0-9]+)', line)
            if score:
                last_score = (score.group(1), int(score.group(2)))
                if d:
                    depth = int(d.group(1))
        candidate = messages[-1].split()
        if len(candidate) < 2 or not re.fullmatch('[a-h][1-8][a-h][1-8][qrbn]?', candidate[1]):
            raise RuntimeError('Invalid UCI bestmove: ' + messages[-1])
        return {'move': candidate[1], 'score': last_score, 'depth': depth,
                'move_s': round(time.monotonic()-begin, 3), 'uci_info': messages[-12:]}

    def close(self):
        try:
            if self.p.poll() is None:
                self.send('quit')
                self.p.wait(timeout=2)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.p.kill()
        finally:
            if self.p.poll() is None:
                self.p.kill()
                self.p.wait(timeout=2)


def referee(binary, fen, move=None):
    command = [str(binary), '--fen', fen]
    if move is not None:
        command += ['--move', move]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise RuntimeError('Referee rejected FEN/move: ' + result.stderr.strip()[:500])
    values = result.stdout.splitlines()
    if len(values) != 5:
        raise RuntimeError('Referee produced unexpected output')
    return {'fen': values[0], 'status': values[1], 'san': values[2], 'key': values[3], 'legal': int(values[4])}


def joshua_choice(binary, fen, model, graph_file, depth, quiescence, timeout,
                  folder: Path, logger: Logger, progress, explore_cp=0, explore_plies=0, seed=0,
                  verify_margin_cp=0.0, verify_extra_depth=0):
    folder.mkdir(parents=True, exist_ok=True)
    command = [str(binary), '--mode', 'alphabeta', '--model', '4', '--depth', str(depth),
               '--quiescence', str(quiescence), '--plies', '1', '--fen', fen,
               '--graph-file', str(graph_file), '--no-board', '--output', str(folder),
               '--explore-cp', str(explore_cp), '--explore-plies', str(explore_plies),
               '--game-seed', str(seed), '--verify-margin-cp', str(verify_margin_cp),
               '--verify-extra-depth', str(verify_extra_depth)]
    logfile = folder / 'engine_console.log'
    begin = time.monotonic()
    with logfile.open('w', encoding='utf-8') as output:
        proc = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, text=True)
        while proc.poll() is None:
            if STOP:
                proc.terminate()
                proc.wait(timeout=4)
                raise InterruptedError('Stopped by signal')
            if time.monotonic() - begin > timeout:
                proc.kill()
                proc.wait(timeout=4)
                raise TimeoutError('Joshua move exceeded timeout')
            try:
                proc.wait(timeout=progress)
            except subprocess.TimeoutExpired:
                logger.event('HEARTBEAT', engine='JOSHUA', fen=fen[:32], search_s=round(time.monotonic()-begin, 3))
    wall = round(time.monotonic()-begin, 3)
    if proc.returncode:
        raise RuntimeError(f'JOSHUA exit={proc.returncode}; see {logfile}')
    with (folder / 'selfplay_timeline.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 1:
        raise RuntimeError('Expected exactly one Joshua move row; engine may have stopped early')
    move = rows[0]['chosen_uci']
    if not re.fullmatch('[a-h][1-8][a-h][1-8][qrbn]?', move):
        raise RuntimeError('Malformed JOSHUA move')
    with (folder / 'run_evidence.json').open(encoding='utf-8') as stream:
        evidence = json.load(stream)
    if evidence.get('adaptive_graph_version') != model['version']:
        raise RuntimeError('Joshua did not load expected adaptive graph version')
    if evidence.get('adaptive_graph_evaluations', 0) < 1:
        raise RuntimeError('No evidence Joshua evaluated adaptive paceval graph')
    return {'move': move, 'score': float(rows[0]['white_score_cp']), 'graph_folder':str(folder),
            'move_s': wall, 'evidence': {'version': evidence['adaptive_graph_version'],
             'graph_evaluations': evidence['adaptive_graph_evaluations'],
             'paceval_graph_points': evidence.get('paceval_graph_point_evaluations'),
             'verified_moves': evidence.get('v12_verified_moves', 0),
             'verify_changed': evidence.get('v12_verified_decisions_changed', 0),
             'verify_margin_cp': evidence.get('v12_verify_margin_cp', 0),
             'verify_extra_depth': evidence.get('v12_verify_extra_depth', 0)}}


def expected_score(score):
    """Heuristic expected points (not Stockfish-calibrated WDL or FIDE Elo)."""
    if score is None:
        return None
    kind, raw = score
    if kind == 'mate':
        return 1.0 if raw > 0 else 0.0
    cp = max(-2000.0, min(2000.0, float(raw)))
    return 1.0 / (1.0 + math.exp(-cp / 180.0))


def stockfish_loss(teacher, fen_before, fen_after, nodes, after_status="ongoing", logger=None, progress_seconds=5):
    """Bounded expected-points loss with explicit mate alerts and raw UCI scores."""
    prior = teacher.go(fen_before, nodes, logger, progress_seconds, reset_hash=True)
    if after_status == 'checkmate':
        after = {'score': ('mate', -1), 'depth': None}
    elif after_status != 'ongoing':
        after = {'score': ('cp', 0), 'depth': None}
    else:
        after = teacher.go(fen_after, nodes, logger, progress_seconds, reset_hash=True)
    before_p = expected_score(prior['score'])
    opponent_p = expected_score(after['score'])
    loss = None if before_p is None or opponent_p is None else round(
        max(0., min(100., 100. * (before_p + opponent_p - 1.0))), 3)
    before_mate = prior['score'] is not None and prior['score'][0] == 'mate'
    after_mate = after['score'] is not None and after['score'][0] == 'mate'
    mate_alert = bool(after_mate and after['score'][1] > 0 and
                      (not before_mate or prior['score'][1] > 0))
    if mate_alert:
        kind = 'mate_turnaround'
    elif loss is not None and loss >= 20:
        kind = 'major_tactical_regression'
    elif loss is not None and loss >= 7:
        kind = 'candidate_tactical_regression'
    else:
        kind = 'no_large_loss'
    return {'loss_pp': loss, 'before_expected_score': before_p,
            'after_expected_score': None if opponent_p is None else 1.0-opponent_p,
            'before_uci_score': prior['score'], 'after_uci_score_opponent': after['score'],
            'mate_alert': mate_alert, 'finding_type': kind,
            'before_depth': prior['depth'], 'after_depth': after['depth']}


def sync_graph_export(target: Path, source: Path, version: int):
    """Publish only graph expressions actually exported by an engine run."""
    text_file = source / 'paceval_graph.txt'
    csv_file = source / 'paceval_graph_terms.csv'
    if not text_file.is_file() or not csv_file.is_file():
        raise RuntimeError('Engine did not export actual registered graph files')
    graph = text_file.read_text(encoding='utf-8')
    if f'version={version}\n' not in graph or 'expression=' not in graph:
        raise RuntimeError('Engine-exported graph version/expression mismatch')
    atomic_text(target / 'active_graph_expression.txt', graph)
    atomic_text(target / 'active_graph_terms.csv', csv_file.read_text(encoding='utf-8'))
    full_catalog = source / 'paceval_all_graphs.csv'
    if full_catalog.is_file():
        atomic_text(target / 'active_full_graph_catalog.csv', full_catalog.read_text(encoding='utf-8'))
    return hashlib.sha256(graph.encode('utf-8')).hexdigest()


def check_active_limit(directory: Path, logger: Logger):
    active = sum(file_footprint(p) for p in directory.rglob('*') if p.is_file())
    if active > MEMORY_LIMIT:
        logger.event('ACTIVE_LOG_LIMIT', bytes=active, limit=MEMORY_LIMIT)
        raise RuntimeError('Active game data exceeded 25 MB. Stop before unbounded growth.')
    return active


def file_footprint(path):
    st = path.stat()
    return max(st.st_size, getattr(st, 'st_blocks', 0) * 512)


def rotate(archives: Path, max_bytes: int, logger: Logger):
    files = sorted(archives.glob('game_*.zip'))
    used = sum(file_footprint(p) for p in files)
    while used > max_bytes and files:
        oldest = files.pop(0)
        size = file_footprint(oldest)
        oldest.unlink()
        used -= size
        logger.event('ROTATE_DELETE', removed=oldest.name, freed_bytes=size, remaining_bytes=used)
    return used


def archive_game(directory: Path, archives: Path, game: int, limit: int, logger: Logger):
    archives.mkdir(parents=True, exist_ok=True)
    destination = archives / f'game_{game:06d}.zip'
    temporary = destination.with_suffix('.zip.partial')
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for path in sorted(directory.rglob('*')):
                if path.is_file():
                    z.write(path, path.relative_to(directory))
        with zipfile.ZipFile(temporary) as check:
            bad = check.testzip()
            if bad is not None:
                raise RuntimeError('ZIP CRC failure for ' + bad)
        os.replace(temporary, destination)
        logger.event('ARCHIVE_COMMITTED', archive=destination.name, bytes=destination.stat().st_size)
        shutil.rmtree(directory)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return rotate(archives, limit, logger)


def baseline_holdouts(referee_binary):
    # Fixed and independent positions covering BOTH colors, not a proof of chess strength.
    # The first position reproduces the historically documented 15...Nxe5 risk.
    yield 'r1bqkb1r/pp1p1pp1/n1p1p3/4P2p/1PnPBB2/PQN2N2/5PPP/R4RK1 b kq - 1 15'
    for white_move, black_reply in (('e2e4', 'e7e5'), ('d2d4', 'd7d5'),
                                    ('c2c4', 'e7e5'), ('g1f3', 'g8f6')):
        black_to_move = referee(referee_binary, START, white_move)['fen']
        yield black_to_move
        yield referee(referee_binary, black_to_move, black_reply)['fen']


def evaluate_model_on_fens(fens, model, graph_file, args, teacher, directory, logger, label):
    results = []
    for i, f in enumerate(fens):
        if STOP:
            raise InterruptedError('Stopped during model validation')
        started = time.monotonic()
        logger.event('GRAPH_TEST_START', graph_version=model['version'], group=label, index=i, fen=f)
        chosen = joshua_choice(args.joshua, f, model, graph_file, args.depth,
                               args.quiescence, args.move_timeout, directory / f'{label}_{i}',
                               logger, args.progress_seconds,
                               verify_margin_cp=args.verify_margin_cp,
                               verify_extra_depth=args.verify_extra_depth)
        after = referee(args.referee, f, chosen['move'])
        assessment = stockfish_loss(teacher, f, after["fen"], args.teacher_nodes, after["status"], logger, args.progress_seconds)
        logger.event('GRAPH_TEST_END', graph_version=model['version'], group=label,
                     index=i, loss_pp=assessment['loss_pp'], mate_alert=assessment['mate_alert'], test_s=round(time.monotonic()-started, 3))
        results.append({'fen': f, 'chosen_uci': chosen['move'],
                        'loss_pp': assessment['loss_pp'], 'mate_alert': assessment['mate_alert'],
                        'finding_type':assessment['finding_type'],
                        'graph_evidence': chosen['evidence'], 'graph_folder': str(directory / f'{label}_{i}')})
    return results


def result_mean(items):
    values = [item['loss_pp'] for item in items]
    if not values or any(x is None for x in values):
        return None
    return round(sum(values) / len(values), 3)


def candidate_plans(game_id, urgent_mate, active, args):
    """Generate a bounded deterministic V12 candidate pool from whitelisted mathematical templates."""
    if urgent_mate:
        priority = ['king_check_combo', 'king_tactics', 'king_alarm', 'check_pressure']
    else:
        pool = ['hanging_capture_combo', 'hanging_pressure', 'queen_exposure',
                'active_captures', 'king_tactics', 'king_alarm', 'pawn_race']
        offset = ((game_id // 2)-1) % len(pool)
        priority = pool[offset:] + pool[:offset]
    fresh = [term for term in priority if term not in active['extra']]
    existing = [term for term in priority if term in active['extra']]
    selected = (fresh + existing)[:3]
    index = ((game_id - 1)//2) % len(TERMS)
    linear = [TERMS[index], TERMS[(index+3)%len(TERMS)]]
    plans = []
    for term in selected:
        for delta in (-args.structural_step,args.structural_step):
            plans.append(('nonlinear', term, delta))
    for term in linear:
        for delta in (-args.step,args.step):
            plans.append(('linear',term,delta))
    return plans[:getattr(args,'candidate_budget',8)]


def adjust_graph(game_id, errors, active_model_path, teacher, args, directory, logger):
    """Bounded, real decision-based coordinate and STRUCTURAL graph proposals.

    This is not autonomous source-code rewriting or a general learning proof.
    All models use the real paceval evaluator, and distinct FENs guard against
    immediate regressions. Acceptance is provisional until paired match evidence.
    """
    report = {'status': 'not_attempted', 'reason': '', 'candidates': [],
              'method': 'V12 multi-template bounded trials; held-out reference checks; champion/challenger paired matches',
              'promotion_claim': 'Local gate only; not evidence of global chess-strength improvement'}
    if not args.adapt:
        report.update(status='disabled', reason='--no-adapt')
        return report
    suspects = sorted((r for r in errors if r.get('loss_pp') is not None and r['loss_pp'] >= args.training_loss_pp),
                      key=lambda x: (-bool(x.get('mate_alert')), -x['loss_pp']))
    if not suspects:
        report.update(status='rejected', reason='No measured high-loss Joshua position')
        return report
    active = parse_model(active_model_path)
    train_fens = list(dict.fromkeys(x['fen_before'] for x in suspects))[:args.train_positions]
    heldout = [f for f in baseline_holdouts(args.referee) if f not in train_fens][:args.holdout_positions]
    if not heldout:
        report.update(status='rejected', reason='No separate holdout positions')
        return report
    stage = directory / 'graph_trials'
    stage.mkdir(exist_ok=True)
    baseline = evaluate_model_on_fens(train_fens + heldout, active, active_model_path,
                                     args, teacher, stage, logger, 'baseline')
    btrain = result_mean(baseline[:len(train_fens)])
    bhold = result_mean(baseline[len(train_fens):])
    report['baseline_train_loss_pp'] = btrain
    report['baseline_holdout_loss_pp'] = bhold
    if btrain is None or bhold is None:
        report.update(status='rejected', reason='Stockfish expected-score estimate unavailable')
        return report
    urgent_mate = any(x.get('mate_alert') for x in suspects)
    plans = candidate_plans(game_id, urgent_mate, active, args)
    report['candidate_plan'] = [{'category':c,'term':term,'change':delta} for c,term,delta in plans]
    revisions = active_model_path.parent / 'model_versions'
    historical_ids = [int(x.stem.removeprefix('version_')) for x in revisions.glob('version_*.tsv')
                      if re.fullmatch(r'version_[0-9]{7}', x.stem)] if revisions.exists() else []
    next_version = max([active['version'], *historical_ids]) + 1
    if next_version >= 9_999_999:
        report.update(status='rejected',reason='Model version registry exhausted')
        return report
    accepted = None
    for category, term, change in plans:
        candidate = {'version': next_version, 'weights': dict(active['weights']),
                     'extra': dict(active.get('extra', {}))}
        key = 'extra' if category == 'nonlinear' else 'weights'
        limit = 8 if category == 'nonlinear' else 32
        old = candidate[key].get(term, 0.0)
        new = round(max(-limit, min(limit, old + change)), 4)
        if new == old:
            continue
        if category == 'nonlinear' and new and term not in candidate['extra'] and len(candidate['extra']) >= 6:
            report['candidates'].append({'term':term,'category':category,'pass':False,'reason':'six-term topology limit'})
            continue
        if new == 0 and category == 'nonlinear':
            candidate['extra'].pop(term, None)
        else:
            candidate[key][term] = new
        label = f'candidate_{len(report["candidates"]):02d}'
        candidate_path = stage / (label + '.tsv')
        atomic_text(candidate_path, model_text(candidate))
        try:
            checks = evaluate_model_on_fens(train_fens + heldout, candidate, candidate_path,
                                           args, teacher, stage, logger, label)
            t = result_mean(checks[:len(train_fens)])
            h = result_mean(checks[len(train_fens):])
            decisions_changed = sum(x['chosen_uci'] != y['chosen_uci'] for x, y in zip(checks, baseline))
            holdout_safe = all(y['loss_pp'] is not None and x['loss_pp'] is not None and
                               y['loss_pp'] <= x['loss_pp'] + args.max_holdout_regression
                               for x, y in zip(baseline[len(train_fens):], checks[len(train_fens):]))
            mate_guard = all(not (y.get('mate_alert') and not x.get('mate_alert'))
                             for x, y in zip(baseline[len(train_fens):], checks[len(train_fens):]))
            okay = bool(decisions_changed and t is not None and h is not None and
                        t <= btrain - args.min_improvement and
                        h <= bhold and holdout_safe and mate_guard)
            trial = {'category':category,'term':term,'change':change,
                     'version':candidate['version'],'train_loss_pp':t,
                     'holdout_loss_pp':h,'decisions_changed':decisions_changed,
                     'holdout_safe':holdout_safe,'mate_guard':mate_guard,'local_gate_pass':okay,'pass':False,
                     'graph_tsv':candidate_path.name}
            if okay and (accepted is None or t < accepted[0]):
                accepted = (t, candidate_path, candidate, Path(checks[0]['graph_folder']))
        except Exception as exc:
            trial = {'category':category,'term':term,'change':change,'pass':False,
                     'reason':'Candidate execution or reference validation failed: '+str(exc)[:250]}
        report['candidates'].append(trial)
        logger.event('GRAPH_TRIAL', **trial)
    if accepted:
        old_text = active_model_path.read_text(encoding='utf-8')
        atomic_text(directory / 'model_previous.tsv', old_text)
        # A local Stockfish decision gate is NOT evidence that the new model
        # improves chess play. Test actual fully-adjudicated games against the
        # immutable incumbent before changing the active TSV.
        try:
            verdict=champion_gate.compare(active_model_path, accepted[1], args,
                                           directory/'champion_duel', logger, RuntimeAPI())
            report['champion_gate']=verdict
            if not verdict['accepted']:
                report.update(status='rejected_after_champion_gate', reason=verdict['reason'])
                logger.event('GRAPH_NOT_PROMOTED', reason=verdict['reason'])
                return report
            # Store both frozen models before touching the active model. This
            # ensures a failure in the snapshot preparation leaves it unchanged.
            snapshots=active_model_path.parent/'model_versions'
            snapshots.mkdir(exist_ok=True)
            atomic_text(snapshots/f'version_{active["version"]:07d}.tsv', old_text)
            atomic_text(snapshots/f'version_{accepted[2]["version"]:07d}.tsv',
                        accepted[1].read_text(encoding='utf-8'))
            # The expression was generated and successfully executed by authentic
            # paceval, rather than generated as an unvalidated Python string.
            graph_hash=sync_graph_export(active_model_path.parent, accepted[3], accepted[2]['version'])
            if active_model_path.read_text(encoding='utf-8') != old_text:
                raise RuntimeError('Active model changed during model gate')
            atomic_text(active_model_path, accepted[1].read_text(encoding='utf-8'))
            # Bound auxiliary history. The complete duel is still in the ZIP.
            for previous in sorted(snapshots.glob('version_*.tsv'))[:-16]:
                previous.unlink()
            report.update(status='promoted_provisional',
                 reason='Local FEN tests and actual paired champion matches passed. General chess strength NOT established.',
                 new_version=accepted[2]['version'], graph_sha256=graph_hash,
                 new_graph_terms=accepted[2].get('extra', {}),
                 new_graph_coefficients=accepted[2]['weights'])
            logger.event('GRAPH_PROMOTED_PROVISIONAL', version=accepted[2]['version'],
                         graph_sha256=graph_hash,duel_score=verdict.get('score'))
        except Exception as exc:
            report.update(status='rejected_champion_gate_error',reason=str(exc)[:300])
            logger.event('GRAPH_GATE_ERROR', reason=report['reason'])
    else:
        report.update(status='rejected', reason='No real tested graph candidate met all local gates')
        logger.event('GRAPH_REJECTED', reason=report['reason'])
    return report


def comparison_key(row):
    """Keep different opponents, depths, skill levels and teacher scales apart."""
    fields = ('stockfish_id','stockfish_nodes','stockfish_skill','joshua_depth','quiescence')
    if any(field not in row for field in fields):
        return None  # Historical V9 index lacks the settings; not comparable.
    # Search policies with different selective depth must NOT be grouped.
    # Pre-V12 games had no verification; represent their implicit setting as 0.
    return tuple(str(row[k]) for k in fields) + (
        str(row.get('verify_margin_cp', 0)), str(row.get('verify_extra_depth', 0)))


def paired_opening_results(rows):
    """Two consecutive games on one prescribed opening, opposite colors."""
    grouped = {}
    by_id = {int(r['game']):r for r in rows if r.get('joshua_points') is not None}
    for odd, a in sorted(by_id.items()):
        if odd % 2 == 0:continue
        b = by_id.get(odd+1)
        if not b or a.get('graph_version') != b.get('graph_version'):
            continue
        ka, kb = comparison_key(a), comparison_key(b)
        if ka is None or ka != kb or a.get('opening_book') != b.get('opening_book'):
            continue
        if a.get('white') != 'Stockfish' or b.get('white') != 'JOSHUA':
            continue
        key = (ka, int(a['graph_version']), a.get('opening_book'))
        grouped.setdefault(key, []).append((float(a['joshua_points'])+float(b['joshua_points']))/2.)
    return grouped


def sign_test_two_sided(diffs):
    """Exploratory sign-test for distinct openings; ignore ties."""
    outcomes = [1 if x > 0 else -1 for x in diffs if x != 0]
    count = len(outcomes)
    if not count:return None
    positive = outcomes.count(1)
    low = min(positive, count-positive)
    return min(1., 2. * sum(math.comb(count,k) for k in range(low+1)) / (2**count))


def summary_metrics(rows):
    complete = [r for r in rows if r['result'] in ('1-0','0-1','1/2-1/2') and r.get('joshua_points') is not None]
    if not complete:
        return {'completed_games':0,'strength_claim':'INSUFFICIENT_DATA'}
    scores = [float(r['joshua_points']) for r in complete]
    mean = sum(scores)/len(scores)
    elo = 400*math.log10(mean/(1-mean)) if 0 < mean < 1 else None
    groups = {}
    for r in complete:
        key = str(r['graph_version']) + '|' + (str(comparison_key(r)) if comparison_key(r) else 'legacy-settings-unverified')
        groups.setdefault(key,[]).append(r)
    pair_data = paired_opening_results(complete)
    versions = {}
    for key,group in sorted(groups.items()):
        points=[float(r['joshua_points']) for r in group]
        losses=[float(r['mean_stockfish_loss_pp']) for r in group if r.get('mean_stockfish_loss_pp') is not None]
        signature=comparison_key(group[0]);version=int(group[0]['graph_version'])
        paired=sum(len(v) for (settings,v_id,_),v in pair_data.items() if settings==signature and v_id==version)
        versions[key]={'games':len(group),'paired_color_opening_samples':paired,
                       'wins':points.count(1.),'draws':points.count(.5),'losses':points.count(0.),
                       'mean_points':round(sum(points)/len(points),4),
                       'mean_heuristic_loss_pp':round(sum(losses)/len(losses),3) if losses else None,
                       'status':'PRELIMINARY' if paired>=8 else 'INSUFFICIENT_PAIRED_OPENINGS'}
    comparisons=[]
    models=sorted({(setting,version) for setting,version,opening in pair_data},key=str)
    for (a_settings,a_version) in models:
        for (b_settings,b_version) in models:
            if a_settings != b_settings or a_version >= b_version:continue
            old={opening:sum(scores)/len(scores) for (setting,v,opening),scores in pair_data.items()
                 if setting==a_settings and v==a_version}
            new={opening:sum(scores)/len(scores) for (setting,v,opening),scores in pair_data.items()
                 if setting==b_settings and v==b_version}
            common=sorted(old.keys() & new.keys())
            diffs=[new[k]-old[k] for k in common]
            p=sign_test_two_sided(diffs) if len(common)>=8 else None
            if p is None or p>=.05:
                status='NOT_ESTABLISHED'
            elif sum(diffs)>0:
                status='BETTER_ON_COMPARED_OPENINGS_PROVISIONAL'
            else:
                status='WORSE_ON_COMPARED_OPENINGS_PROVISIONAL'
            comparisons.append({'old_version':a_version,'new_version':b_version,
                                'settings':list(a_settings),'matched_distinct_openings':len(common),
                                'paired_score_delta':round(sum(diffs)/len(diffs),4) if diffs else None,
                                'exploratory_sign_test_p':round(p,5) if p is not None else None,
                                'status':status})
    return {'completed_games':len(complete),'wins':scores.count(1.),'draws':scores.count(.5),
            'losses':scores.count(0.),'mean_match_points':round(mean,4),
            'observed_relative_elo_difference':round(elo,1) if elo is not None else None,
            'model_versions':versions,'version_comparisons':comparisons,
            'strength_claim':'NO_UNSUPPORTED_STRENGTH_GAIN_CLAIM',
            'caveat':'Exploratory paired-opening outcomes against fixed settings. Same openings are correlated, and repeat games may be deterministic. No absolute Elo or independent generalization proof.'}


def main():
    parser = argparse.ArgumentParser(description='Stockfish vs JOSHUA V12; tactical score analysis and evolving paceval graph formulas')
    parser.add_argument('--joshua', type=Path, default=(BASE / 'joshua' if (BASE / 'joshua').is_file() else BASE / 'bin/joshua'))
    parser.add_argument('--referee', type=Path, default=(BASE / 'joshua_referee' if (BASE / 'joshua_referee').is_file() else BASE / 'bin/joshua_referee'))
    parser.add_argument('--stockfish', type=Path, default=Path(shutil.which('stockfish') or '/usr/games/stockfish'))
    parser.add_argument('--paceval-runtime', type=Path, default=None)
    parser.add_argument('--output', type=Path, default=Path('stockfish_sessions'))
    parser.add_argument('--graph-file', type=Path, default=None)
    parser.add_argument('--max-games', type=int, default=0)
    parser.add_argument('--max-plies', type=int, default=400)
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--verify-margin-cp', type=float, default=25.0,
                        help='V12: investigate ambiguous root choices when top two are within this many centipawns; 0 disables')
    parser.add_argument('--verify-extra-depth', type=int, default=1,
                        help='V12: add one or two full search plies for ambiguous roots')
    parser.add_argument('--quiescence', type=int, default=2)
    parser.add_argument('--stockfish-nodes', type=int, default=1000)
    parser.add_argument('--teacher-nodes', type=int, default=2500)
    parser.add_argument('--stockfish-skill', type=int, default=20)
    parser.add_argument('--stockfish-hash', type=int, default=32)
    parser.add_argument('--stockfish-threads', type=int, default=1)
    parser.add_argument('--move-timeout', type=float, default=120)
    parser.add_argument('--progress-seconds', type=int, default=5)
    parser.add_argument('--opening', choices=['cycle', 'none'], default='cycle')
    parser.add_argument('--max-logs-mb', type=float, default=25)
    parser.add_argument('--adapt', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--candidate-budget', type=int, default=8,
                        help='V12 whitelisted candidate trials (4..12)')
    parser.add_argument('--step', type=float, default=2.0)
    parser.add_argument('--training-loss-pp', type=float, default=7.0)
    parser.add_argument('--structural-step', type=float, default=0.5)
    parser.add_argument('--train-positions', type=int, default=2)
    parser.add_argument('--holdout-positions', type=int, default=8)
    parser.add_argument('--minimum-pairs-per-version', type=int, default=4)
    parser.add_argument('--min-improvement', type=float, default=1.0)
    parser.add_argument('--max-holdout-regression', type=float, default=2.0)
    parser.add_argument('--champion-pairs', type=int, default=4, help='Distinct color-paired challenger/champion openings, 1..6')
    parser.add_argument('--champion-max-plies', type=int, default=100, help='Maximum plies per duel; truncation cannot qualify')
    parser.add_argument('--champion-min-score', type=float, default=0.625, help='Minimum candidate match score; provisional gate only')
    args = parser.parse_args()
    if not 1 <= args.depth <= 10 or not 1 <= args.max_plies <= 1000 or not 0 <= args.max_games <= 1_000_000:
        parser.error('Invalid depth or game bounds')
    if not (math.isfinite(args.verify_margin_cp) and 0 <= args.verify_margin_cp <= 10000 and
            0 <= args.verify_extra_depth <= 2 and args.depth + args.verify_extra_depth <= 10 and
            (args.verify_extra_depth == 0 or args.verify_margin_cp > 0)):
        parser.error('Invalid V12 verification depth/margin combination')
    if not (1 <= args.stockfish_nodes <= 2_000_000 and 1 <= args.teacher_nodes <= 2_000_000):
        parser.error('Invalid Stockfish node count')
    if not (0 <= args.stockfish_skill <= 20 and 1 <= args.progress_seconds <= 60 and args.move_timeout >= 5):
        parser.error('Invalid skill, progress interval or move timeout')
    if not (4 <= args.candidate_budget <= 12):
        parser.error('candidate-budget must be 4..12')
    if not (0 < args.step <= 4 and 0 < args.structural_step <= 2 and 1 <= args.train_positions <= 4 and 1 <= args.holdout_positions <= 8 and 1 <= args.minimum_pairs_per_version <= 100):
        parser.error('Invalid learning bounds')
    if not (1 <= args.champion_pairs <= len(champion_gate.CHALLENGE_OPENINGS) and 20 <= args.champion_max_plies <= 200 and .5 < args.champion_min_score <= 1.0):
        parser.error('Invalid champion comparison settings')
    for p in (args.joshua, args.referee, args.stockfish):
        if not p.is_file() or not os.access(p, os.X_OK):
            parser.error(f'Required executable missing or not executable: {p}')
    if args.paceval_runtime:
        os.environ['PACEVAL_RUNTIME'] = str(args.paceval_runtime.resolve())
    elif not os.getenv('PACEVAL_RUNTIME'):
        candidate = args.joshua.resolve().parent / 'libpaceval_linux_sharedLIB.so'
        if candidate.is_file():
            os.environ['PACEVAL_RUNTIME'] = str(candidate)
        else:
            candidate = BASE / 'runtime/libpaceval_linux_sharedLIB.so'
            os.environ['PACEVAL_RUNTIME'] = str(candidate)
    if not Path(os.environ['PACEVAL_RUNTIME']).is_file():
        parser.error('Original paceval runtime not found; set PACEVAL_RUNTIME or --paceval-runtime')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    archives = out / 'archives'
    archives.mkdir(exist_ok=True)
    graph_file = args.graph_file.resolve() if args.graph_file else out / 'active_graph.tsv'
    if not graph_file.exists():
        atomic_text(graph_file, (BASE / 'config/active_graph.tsv').read_text(encoding='utf-8'))
    parse_model(graph_file)
    counter_file = out / 'next_game_id.txt'
    game_id = int(counter_file.read_text()) if counter_file.exists() else 1
    limit = int(args.max_logs_mb * 1_000_000)
    if not 10000 <= limit <= MEMORY_LIMIT:
        parser.error('Log rotation budget must be between 10,000 and 25,000,000 bytes')
    # Probe that the actual Joshua binary can create and use a paceval graph
    # BEFORE starting a potentially unlimited schedule. Fail closed.
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)
    match = UCI(args.stockfish, args.stockfish_threads, args.stockfish_hash, timeout=args.move_timeout, skill=args.stockfish_skill)
    teacher = UCI(args.stockfish, args.stockfish_threads, args.stockfish_hash, timeout=args.move_timeout, skill=20)
    completed = 0
    try:
        while not STOP and (args.max_games == 0 or completed < args.max_games):
            game_dir = out / 'current_game'
            if game_dir.exists():
                # Preserve uncommitted logs, never silently overwrite a crashed game.
                raise RuntimeError(f'Uncommitted game directory exists: {game_dir}. Inspect/rename before resuming.')
            game_dir.mkdir()
            logger = Logger(game_dir / 'debug_timeline.log', args.progress_seconds)
            model = parse_model(graph_file)
            game_id_current = game_id
            # Reserve durable game number before starting; never reuse after crash.
            game_id += 1
            atomic_text(counter_file, str(game_id) + '\n')
            white = 'Stockfish' if game_id_current % 2 else 'JOSHUA'
            black = 'JOSHUA' if white == 'Stockfish' else 'Stockfish'
            fen = START
            initial = referee(args.referee, fen)
            counts = {initial['key']: 1}
            moves = []
            joshua_errors = []
            result, reason = '*', 'incomplete'
            logger.event('GAME_START', game=game_id_current, white=white, black=black,
                         graph_version=model['version'], stockfish=match.name,
                         stockfish_nodes=args.stockfish_nodes, teacher_nodes=args.teacher_nodes)
            atomic_text(game_dir / 'model_used.tsv', model_text(model))
            if args.opening == 'cycle':
                opening = OPENINGS[((game_id_current - 1)//2) % len(OPENINGS)]
                a = referee(args.referee, fen, opening)
                fen = a['fen']
                counts[a['key']] = counts.get(a['key'], 0) + 1
                moves.append({'ply': 1, 'side': 'white', 'actor': white, 'uci': opening, 'san': a['san'],
                              'fen_before': START, 'fen_after': fen, 'move_s': 0.0,
                              'source': 'forced opening book (identical for paired colors)', 'graph_version': model['version']})
                logger.event('OPENING_BOOK', ply=1, uci=opening, san=a['san'], note='Book move is not an engine decision')
            try:
                while not STOP and len(moves) < args.max_plies:
                    state = referee(args.referee, fen)
                    if state['status'] != 'ongoing':
                        reason = state['status']
                        break
                    if counts.get(state['key'], 0) >= 3:
                        reason = 'threefold_repetition_claim'
                        break
                    ply = len(moves) + 1
                    side = 'white' if ' w ' in fen else 'black'
                    actor = white if side == 'white' else black
                    logger.event('SEARCH_START', ply=ply, side=side, actor=actor, graph_version=model['version'])
                    start = time.monotonic()
                    if actor == 'Stockfish':
                        played = match.go(fen, args.stockfish_nodes, logger, args.progress_seconds)
                    else:
                        played = joshua_choice(args.joshua, fen, model, graph_file, args.depth,
                                              args.quiescence, args.move_timeout,
                                              game_dir / f'joshua_ply_{ply:03d}', logger,
                                              args.progress_seconds,
                                              verify_margin_cp=args.verify_margin_cp,
                                              verify_extra_depth=args.verify_extra_depth)
                    move_s = round(time.monotonic() - start, 3)
                    move = played['move']
                    advanced = referee(args.referee, fen, move)
                    counts[advanced['key']] = counts.get(advanced['key'], 0) + 1
                    row = {'ply': ply, 'side': side, 'actor': actor, 'uci': move,
                           'san': advanced['san'], 'fen_before': fen, 'fen_after': advanced['fen'],
                           'move_s': move_s, 'engine_score': played.get('score'),
                           'graph_version': model['version'], 'source': 'engine'}
                    moves.append(row)
                    logger.event('MOVE', ply=ply, actor=actor, uci=move, san=advanced['san'],
                                 move_s=move_s, score=played.get('score'))
                    if actor == 'JOSHUA':
                        row['v12_verified_moves'] = played['evidence'].get('verified_moves', 0)
                        row['v12_verify_changed'] = played['evidence'].get('verify_changed', 0)
                        logger.event('V12_SEARCH_POLICY', ply=ply,
                            margin_cp=args.verify_margin_cp, extra_depth=args.verify_extra_depth,
                            verification_used=row['v12_verified_moves'], changed=row['v12_verify_changed'])
                        graph_hash = sync_graph_export(out, Path(played['graph_folder']), model['version'])
                        row['adaptive_graph_sha256'] = graph_hash
                        grade = stockfish_loss(teacher, fen, advanced['fen'], args.teacher_nodes,
                                               advanced['status'], logger, args.progress_seconds)
                        e = {'ply': ply, 'fen_before': fen, 'chosen_uci': move, **grade}
                        joshua_errors.append(e)
                        logger.event('STOCKFISH_GRADE', ply=ply, loss_pp=grade['loss_pp'], mate_alert=grade['mate_alert'], finding=grade['finding_type'],
                                     grading_s=round(time.monotonic()-start-move_s, 3))
                    fen = advanced['fen']
                    check_active_limit(game_dir, logger)
                    if advanced['status'] != 'ongoing':
                        reason = advanced['status']
                        break
                else:
                    if STOP:
                        reason = 'interrupted'
                    else:
                        reason = 'max_plies_unfinished'
                if reason == 'checkmate':
                    result = '0-1' if ' w ' in fen else '1-0'
                elif reason in ('stalemate', 'insufficient_material', 'threefold_repetition_claim', 'fifty_move_claim'):
                    result = '1/2-1/2'
                else:
                    result = '*'
                logger.event('GAME_END', result=result, termination=reason, plies=len(moves))
                # A PGN containing SAN reconstructed independently by C++ referee.
                headers = {'Event': 'Joshua vs Stockfish automatic', 'Date': dt.datetime.now().strftime('%Y.%m.%d'),
                           'White': white, 'Black': black, 'Result': result, 'JoshuaGraphVersion': str(model['version']),
                           'StockfishNodes': str(args.stockfish_nodes)}
                pgn = ''.join(f'[{key} "{value}"]\n' for key, value in headers.items()) + '\n'
                pgn_tokens = []
                for i, row in enumerate(moves, 1):
                    if i % 2:
                        pgn_tokens.append(f'{(i+1)//2}.')
                    pgn_tokens.append(row['san'])
                pgn += ' '.join(pgn_tokens) + ' ' + result + '\n'
                atomic_text(game_dir / 'game.pgn', pgn)
                json_write(game_dir / 'moves.json', moves)
                json_write(game_dir / 'joshua_stockfish_grades.json', joshua_errors)
                # Reproducible, user-readable queue of positions worth deeper review.
                with (game_dir / 'tactical_findings.csv').open('w', newline='', encoding='utf-8') as stream:
                    columns = ['ply','fen_before','chosen_uci','loss_pp','mate_alert','finding_type',
                               'before_expected_score','after_expected_score','before_uci_score','after_uci_score_opponent']
                    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
                    writer.writeheader()
                    for issue in sorted(joshua_errors, key=lambda e: -(e.get('loss_pp') or 0)):
                        if issue.get('mate_alert') or (issue.get('loss_pp') or 0) >= args.training_loss_pp:
                            writer.writerow(issue)
                if (out / 'active_graph_expression.txt').exists():
                    atomic_text(game_dir / 'evaluated_graph_expression.txt', (out / 'active_graph_expression.txt').read_text())
                    atomic_text(game_dir / 'evaluated_graph_terms.csv', (out / 'active_graph_terms.csv').read_text())
                pair_signature = {
                    'model_sha256': hashlib.sha256(graph_file.read_bytes()).hexdigest(),
                    'graph_version':model['version'],
                    'stockfish_id':match.name,'stockfish_nodes':args.stockfish_nodes,
                    'stockfish_skill':args.stockfish_skill,
                    'joshua_depth':args.depth,'quiescence':args.quiescence,
                    'verify_margin_cp':args.verify_margin_cp,
                    'verify_extra_depth':args.verify_extra_depth,
                    'opening':OPENINGS[((game_id_current-1)//2)%len(OPENINGS)] if args.opening=='cycle' else 'none'
                }
                if STOP:
                    adaptation = {'status': 'interrupted', 'reason': 'No model change in interrupted game'}
                elif reason != 'max_plies_unfinished' and game_id_current % 2 == 1:
                    # Preserve paired-color comparability. The same graph version
                    # must face Stockfish on both colors before it is promoted.
                    json_write(out / 'pending_pair.json', {'game':game_id_current,
                        'graph_version':model['version'], 'errors':joshua_errors[:40],
                        'pair_signature':pair_signature})
                    adaptation = {'status':'deferred_for_color_pair',
                                  'reason':'First color of fixed-opening pair. Change evaluated after return game.'}
                    logger.event('GRAPH_DEFERRED', reason=adaptation['reason'])
                elif reason != 'max_plies_unfinished':
                    pending_file = out / 'pending_pair.json'
                    paired = json.loads(pending_file.read_text()) if pending_file.exists() else {}
                    if paired.get('game') == game_id_current-1 and paired.get('pair_signature') == pair_signature:
                        all_errors = paired.get('errors', []) + joshua_errors
                    else:
                        all_errors = joshua_errors
                        logger.event('COLOR_PAIR_WARNING', note='Prior color not present with same graph version; no paired learning data')
                    prior_index = out / 'match_index.json'
                    historical = json.loads(prior_index.read_text()) if prior_index.exists() else []
                    # Never count V9/V10/V11 games with incompatible search
                    # settings towards a new version's minimum evidence window.
                    current_setting = (str(match.name),str(args.stockfish_nodes),
                                       str(args.stockfish_skill),str(args.depth),
                                       str(args.quiescence),str(args.verify_margin_cp),
                                       str(args.verify_extra_depth))
                    complete_pairs = sum(1 for row in historical
                         if int(row.get('game',0)) % 2 == 0 and row.get('graph_version')==model['version']
                         and row.get('metric_version')=='v10-bounded-loss-pp'
                         and comparison_key(row) == current_setting
                         and row.get('result') in ('1-0','0-1','1/2-1/2'))
                    if not (paired.get('game') == game_id_current-1 and paired.get('pair_signature') == pair_signature):
                        adaptation = {'status':'skipped_missing_color_pair',
                            'reason':'No matching previous white/black game for training'}
                        logger.event('GRAPH_DEFERRED_FOR_EVIDENCE', **adaptation)
                    elif complete_pairs + 1 < args.minimum_pairs_per_version:
                        adaptation = {'status':'deferred_until_model_pair_count',
                            'reason':'Collect paired colors before another model update',
                            'completed_pairs_after_this_game':complete_pairs+1,
                            'minimum_pairs':args.minimum_pairs_per_version}
                        logger.event('GRAPH_DEFERRED_FOR_EVIDENCE', **adaptation)
                    else:
                        logger.event('GRAPH_VALIDATION_START', version=model['version'], failed_positions=len(all_errors))
                        adaptation = adjust_graph(game_id_current, all_errors, graph_file, teacher,
                                              args, game_dir, logger)
                    pending_file.unlink(missing_ok=True)
                else:
                    adaptation = {'status': 'skipped', 'reason': 'Incomplete game; no training on truncated result'}
                json_write(game_dir / 'adaptation.json', adaptation)
                check_active_limit(game_dir, logger)
                json_write(game_dir / 'summary.json', {'game':game_id_current, 'white':white,'black':black,
                           'result':result,'termination':reason, 'moves':len(moves),'model_used':model['version'],
                           'model_after':parse_model(graph_file)['version'],
                           'stockfish_binary':str(args.stockfish), 'stockfish_id':match.name,
                           'stockfish_skill':args.stockfish_skill, 'stockfish_nodes':args.stockfish_nodes,
                           'teacher_nodes':args.teacher_nodes,
                           'verify_margin_cp':args.verify_margin_cp,'verify_extra_depth':args.verify_extra_depth,
                           'reference_scores':'fixed-node stockfish heuristic; mate separated; bounded expected-score loss in percentage points',
                           'timestamp_utc':utc()})
                completed += 1
                jscore = 1.0 if (result == '1-0' and white == 'JOSHUA' or result == '0-1' and black == 'JOSHUA') else (0.5 if result == '1/2-1/2' else (0 if result != '*' else None))
                index_path = out / 'match_index.json'
                old = json.loads(index_path.read_text()) if index_path.exists() else []
                measured_losses = [x['loss_pp'] for x in joshua_errors if x.get('loss_pp') is not None]
                old.append({'game':game_id_current, 'white':white, 'black':black,
                            'graph_version':model['version'], 'result':result,'joshua_points':jscore,
                            'mean_stockfish_loss_pp':round(sum(measured_losses)/len(measured_losses),3) if measured_losses else None,
                            'metric_version':'v10-bounded-loss-pp',
                            'opening_book':OPENINGS[((game_id_current-1)//2)%len(OPENINGS)] if args.opening=='cycle' else 'none',
                            'stockfish_id':match.name,'stockfish_nodes':args.stockfish_nodes,
                            'stockfish_skill':args.stockfish_skill,'joshua_depth':args.depth,
                            'quiescence':args.quiescence,'verify_margin_cp':args.verify_margin_cp,
                            'verify_extra_depth':args.verify_extra_depth,
                            'termination':reason, 'archive':f'game_{game_id_current:06d}.zip'})
                # Bounded index, retained summary only. Complete data is in game ZIP.
                atomic_text(index_path, json.dumps(old[-250:], indent=2) + '\n')
                json_write(out / 'strength_summary.json', summary_metrics(old[-250:]))
                atomic_text(out / 'latest_game.txt', f'game={game_id_current} result={result} reason={reason} '
                            f'graph_before={model["version"]} graph_after={parse_model(graph_file)["version"]}\n')
            except (Exception, KeyboardInterrupt) as e:
                logger.event('GAME_ERROR', error=str(e)[:500])
                json_write(game_dir / 'error.json', {'error':str(e), 'game':game_id_current, 'time':utc()})
                logger.close()
                last = out / 'last_archive_debug.log'
                last.unlink(missing_ok=True)
                arlog = Logger(last, args.progress_seconds)
                try:
                    archive_game(game_dir, archives, game_id_current, limit, arlog)
                finally:
                    arlog.close()
                if STOP:
                    return 0
                raise
            logger.close()
            # A separate small logger cannot grow unbounded across games.
            # Archive rotation diagnostics are stored in latest_archive.log, not an unlimited aggregate.
            last = out / 'last_archive_debug.log'
            last.unlink(missing_ok=True)
            arlog = Logger(last, args.progress_seconds)
            archive_game(game_dir, archives, game_id_current, limit, arlog)
            arlog.close()
        return 0
    finally:
        match.close()
        teacher.close()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt) as error:
        print(f'JOSHUA_V11_MATCH_ERROR {error}', file=sys.stderr, flush=True)
        sys.exit(2)
