#!/usr/bin/env python3
"""Joshua V9: durable Stockfish-vs-paceval Joshua matches and bounded graph evolution.

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

BASE = Path(__file__).resolve().parent.parent
OPENINGS = ['e2e4', 'd2d4', 'c2c4', 'g1f3', 'b1c3', 'e2e3', 'd2d3',
            'g2g3', 'b2b3', 'f2f4', 'a2a3', 'h2h3', 'a2a4', 'h2h4']
START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
TERMS = ('mobility', 'captures', 'hanging', 'attacked', 'passed', 'kingdanger', 'queenthreat', 'rookthreat')
MEMORY_LIMIT = 25_000_000
STOP = False


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
    if set(values) != {'version', *TERMS} or not re.fullmatch(r'[0-9]{1,7}', values['version']):
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
    return {'version': int(values['version']), 'weights': weights}


def model_text(model):
    return '# Validated decimal paceval graph coefficients. Never inject formulas here.\n' + \
           'version\t' + str(model['version']) + '\n' + \
           ''.join(f'{term}\t{model["weights"][term]:.4f}\n' for term in TERMS)


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
                  folder: Path, logger: Logger, progress, explore_cp=0, explore_plies=0, seed=0):
    folder.mkdir(parents=True, exist_ok=True)
    command = [str(binary), '--mode', 'alphabeta', '--model', '4', '--depth', str(depth),
               '--quiescence', str(quiescence), '--plies', '1', '--fen', fen,
               '--graph-file', str(graph_file), '--no-board', '--output', str(folder),
               '--explore-cp', str(explore_cp), '--explore-plies', str(explore_plies),
               '--game-seed', str(seed)]
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
    return {'move': move, 'score': float(rows[0]['white_score_cp']),
            'move_s': wall, 'evidence': {'version': evidence['adaptive_graph_version'],
             'graph_evaluations': evidence['adaptive_graph_evaluations'],
             'paceval_graph_points': evidence.get('paceval_graph_point_evaluations')}}


def cp_value(score):
    if score is None:
        return None
    kind, number = score
    if kind == 'mate':
        return math.copysign(30000 - min(1000, abs(number)*100), number)
    return float(number)


def stockfish_loss(teacher, fen_before, fen_after, nodes, after_status="ongoing", logger=None, progress_seconds=5):
    # UCI scores are always from the perspective of the side to move.
    # The second position is seen from the opposite side, so invert it.
    prior = teacher.go(fen_before, nodes, logger, progress_seconds, reset_hash=True)
    if after_status == "checkmate":
        b, after = -30000.0, {"depth": None}
    elif after_status != "ongoing":
        b, after = 0.0, {"depth": None}
    else:
        after = teacher.go(fen_after, nodes, logger, progress_seconds, reset_hash=True)
        b = cp_value(after["score"])
    a = cp_value(prior["score"])
    return {'cp_loss': round(max(0.0, a + b), 2) if a is not None and b is not None else None,
            'before_cp': a, 'after_cp_opponent': b,
            'before_depth': prior['depth'], 'after_depth': after['depth']}


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
    # Separately validated fixed FENs covering BOTH side-to-move colors.
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
                               logger, args.progress_seconds)
        after = referee(args.referee, f, chosen['move'])
        assessment = stockfish_loss(teacher, f, after["fen"], args.teacher_nodes, after["status"], logger, args.progress_seconds)
        logger.event('GRAPH_TEST_END', graph_version=model['version'], group=label,
                     index=i, cp_loss=assessment['cp_loss'], test_s=round(time.monotonic()-started, 3))
        results.append({'fen': f, 'chosen_uci': chosen['move'],
                        'cp_loss': assessment['cp_loss'], 'graph_evidence': chosen['evidence']})
    return results


def result_mean(items):
    values = [item['cp_loss'] for item in items]
    if not values or any(x is None for x in values):
        return None
    return round(sum(values) / len(values), 3)


def adjust_graph(game_id, errors, active_model_path, teacher, args, directory, logger):
    """Bounded coordinate-search proposal. No speculative source-code rewriting.

    Train positions are the previous game's high-loss JOSHUA turns. Holdout
    positions are fixed, *separate* FEN positions from known legal openings.
    Candidates must change actual paceval decisions, improve the measured
    training cp loss, and not worsen holdout mean or any held-out move by >5cp.
    A short holdout does not prove Elo improvement; all trial data is retained.
    """
    report = {'status': 'not_attempted', 'reason': '', 'candidates': [],
              'method': 'two signed coordinate trials; independent stockfish score; fixed separate holdout'}
    if not args.adapt:
        report.update(status='disabled', reason='--no-adapt')
        return report
    suspects = sorted((r for r in errors if r.get('cp_loss') is not None and r['cp_loss'] >= args.training_loss_cp),
                      key=lambda x: -x['cp_loss'])
    if not suspects:
        report.update(status='rejected', reason='No Stockfish-observed costly Joshua position')
        return report
    active = parse_model(active_model_path)
    train_fens = list(dict.fromkeys(x['fen_before'] for x in suspects))[:args.train_positions]
    heldout = [f for f in baseline_holdouts(args.referee) if f not in train_fens][:args.holdout_positions]
    if not heldout:
        report.update(status='rejected', reason='No independent holdout FEN')
        return report
    stage = directory / 'graph_trials'
    stage.mkdir(exist_ok=True)
    baseline = evaluate_model_on_fens(train_fens + heldout, active, active_model_path,
                                     args, teacher, stage, logger, 'baseline')
    btrain = result_mean(baseline[:len(train_fens)])
    bhold = result_mean(baseline[len(train_fens):])
    report['baseline_train_cp_loss'] = btrain
    report['baseline_holdout_cp_loss'] = bhold
    if btrain is None or bhold is None:
        report.update(status='rejected', reason='Stockfish score unavailable')
        return report
    term = TERMS[((game_id - 1)//2) % len(TERMS)]
    accepted = None
    for direction in (-1, 1):
        candidate = {'version': active['version']+1, 'weights': dict(active['weights'])}
        candidate['weights'][term] = round(max(-32, min(32, candidate['weights'][term] + direction * args.step)), 4)
        if candidate['weights'][term] == active['weights'][term]:
            continue
        candidate_path = stage / ('candidate_plus.tsv' if direction > 0 else 'candidate_minus.tsv')
        atomic_text(candidate_path, model_text(candidate))
        checks = evaluate_model_on_fens(train_fens + heldout, candidate, candidate_path,
                                       args, teacher, stage, logger, f'candidate_{direction}')
        t = result_mean(checks[:len(train_fens)])
        h = result_mean(checks[len(train_fens):])
        decisions_changed = sum(x['chosen_uci'] != y['chosen_uci'] for x, y in zip(checks, baseline))
        no_bad_holdout = all(y['cp_loss'] is not None and x['cp_loss'] is not None and
                             y['cp_loss'] <= x['cp_loss'] + args.max_holdout_regression
                             for x, y in zip(baseline[len(train_fens):], checks[len(train_fens):]))
        okay = bool(decisions_changed and t is not None and h is not None and
                    t <= btrain - args.min_improvement and
                    h <= bhold and no_bad_holdout)
        trial = {'term': term, 'direction': direction, 'version': candidate['version'],
                 'train_cp_loss': t, 'holdout_cp_loss': h,
                 'decisions_changed': decisions_changed, 'all_heldout_within_regression_bound': no_bad_holdout,
                 'pass': okay, 'graph_tsv': candidate_path.name}
        report['candidates'].append(trial)
        logger.event('GRAPH_TRIAL', **trial)
        if okay and (accepted is None or t < accepted[0]):
            accepted = (t, candidate_path, candidate)
    if accepted:
        old_text = active_model_path.read_text(encoding='utf-8')
        atomic_text(directory / 'model_previous.tsv', old_text)
        atomic_text(active_model_path, accepted[1].read_text(encoding='utf-8'))
        report.update(status='promoted', reason='Train improved; independent holdout criteria passed',
                      new_version=accepted[2]['version'],
                      new_graph_coefficients=accepted[2]['weights'])
        logger.event('GRAPH_PROMOTED', version=accepted[2]['version'], changed_term=term)
    else:
        report.update(status='rejected', reason='No candidate passed measured decision improvement and holdout gates')
        logger.event('GRAPH_REJECTED', reason=report['reason'], term=term)
    return report


def summary_metrics(rows):
    complete = [r for r in rows if r['result'] in ('1-0', '0-1', '1/2-1/2')]
    if not complete:
        return {'completed_games': 0, 'note': 'No completed games. No rating estimate.'}
    scores = [float(r['joshua_points']) for r in complete]
    n = len(scores)
    mean = sum(scores)/n
    # The Elo conversion is a score transformation against this exact opponent
    # setting. Never call it a FIDE Elo or a calibrated absolute engine rating.
    elo = 400 * math.log10(mean/(1-mean)) if 0 < mean < 1 else None
    strength = {'completed_games': n, 'wins': scores.count(1.0), 'draws': scores.count(0.5),
                'losses': scores.count(0.0), 'mean_match_points': round(mean, 4),
                'observed_relative_elo_difference': round(elo, 1) if elo is not None else None,
                'elo_note': 'Exploratory relative score transform only; not absolute Elo. Confidence needs many paired games.'}
    groups = {}
    losses = {}
    for r in complete:
        version = str(r['graph_version'])
        groups.setdefault(version, []).append(float(r['joshua_points']))
        if r.get('mean_stockfish_cp_loss') is not None:
            losses.setdefault(version, []).append(float(r['mean_stockfish_cp_loss']))
    strength['model_versions'] = {v: {'games': len(items), 'mean_match_points':round(sum(items)/len(items), 4),
                         'mean_stockfish_cp_loss':round(sum(losses[v])/len(losses[v]),2) if v in losses else None}
                                  for v, items in sorted(groups.items())}
    strength['trend_claim'] = 'NOT ESTABLISHED: Stockfish fixed-node score is only a heuristic. Changes require held-out, paired match replication.'
    return strength


def main():
    parser = argparse.ArgumentParser(description='Stockfish vs JOSHUA V9; rotating zipped logs; adaptive paceval graph')
    parser.add_argument('--joshua', type=Path, default=BASE / 'bin/joshua')
    parser.add_argument('--referee', type=Path, default=BASE / 'bin/joshua_referee')
    parser.add_argument('--stockfish', type=Path, default=Path(shutil.which('stockfish') or '/usr/games/stockfish'))
    parser.add_argument('--paceval-runtime', type=Path, default=None)
    parser.add_argument('--output', type=Path, default=Path('stockfish_sessions'))
    parser.add_argument('--graph-file', type=Path, default=None)
    parser.add_argument('--max-games', type=int, default=0)
    parser.add_argument('--max-plies', type=int, default=400)
    parser.add_argument('--depth', type=int, default=2)
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
    parser.add_argument('--step', type=float, default=2.0)
    parser.add_argument('--training-loss-cp', type=float, default=35.0)
    parser.add_argument('--train-positions', type=int, default=2)
    parser.add_argument('--holdout-positions', type=int, default=4)
    parser.add_argument('--min-improvement', type=float, default=1.0)
    parser.add_argument('--max-holdout-regression', type=float, default=5.0)
    args = parser.parse_args()
    if not 1 <= args.depth <= 10 or not 1 <= args.max_plies <= 1000 or not 0 <= args.max_games <= 1_000_000:
        parser.error('Invalid depth or game bounds')
    if not (1 <= args.stockfish_nodes <= 2_000_000 and 1 <= args.teacher_nodes <= 2_000_000):
        parser.error('Invalid Stockfish node count')
    if not (0 <= args.stockfish_skill <= 20 and 1 <= args.progress_seconds <= 60 and args.move_timeout >= 5):
        parser.error('Invalid skill, progress interval or move timeout')
    if not (0 < args.step <= 4 and 1 <= args.train_positions <= 4 and 1 <= args.holdout_positions <= 4):
        parser.error('Invalid learning bounds')
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
                                              args.progress_seconds)
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
                        grade = stockfish_loss(teacher, fen, advanced['fen'], args.teacher_nodes,
                                               advanced['status'], logger, args.progress_seconds)
                        e = {'ply': ply, 'fen_before': fen, 'chosen_uci': move, **grade}
                        joshua_errors.append(e)
                        logger.event('STOCKFISH_GRADE', ply=ply, cp_loss=grade['cp_loss'],
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
                if STOP:
                    adaptation = {'status': 'interrupted', 'reason': 'No model change in interrupted game'}
                elif reason != 'max_plies_unfinished' and game_id_current % 2 == 1:
                    # Preserve paired-color comparability. The same graph version
                    # must face Stockfish on both colors before it is promoted.
                    json_write(out / 'pending_pair.json', {'game':game_id_current,
                        'graph_version':model['version'], 'errors':joshua_errors[:40]})
                    adaptation = {'status':'deferred_for_color_pair',
                                  'reason':'First color of fixed-opening pair. Change evaluated after return game.'}
                    logger.event('GRAPH_DEFERRED', reason=adaptation['reason'])
                elif reason != 'max_plies_unfinished':
                    pending_file = out / 'pending_pair.json'
                    paired = json.loads(pending_file.read_text()) if pending_file.exists() else {}
                    if paired.get('game') == game_id_current-1 and paired.get('graph_version') == model['version']:
                        all_errors = paired.get('errors', []) + joshua_errors
                    else:
                        all_errors = joshua_errors
                        logger.event('COLOR_PAIR_WARNING', note='Prior color not present with same graph version; no paired learning data')
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
                           'teacher_nodes':args.teacher_nodes,'reference_scores':'fixed-node stockfish heuristic',
                           'timestamp_utc':utc()})
                completed += 1
                jscore = 1.0 if (result == '1-0' and white == 'JOSHUA' or result == '0-1' and black == 'JOSHUA') else (0.5 if result == '1/2-1/2' else (0 if result != '*' else None))
                index_path = out / 'match_index.json'
                old = json.loads(index_path.read_text()) if index_path.exists() else []
                measured_losses = [x['cp_loss'] for x in joshua_errors if x.get('cp_loss') is not None]
                old.append({'game':game_id_current, 'white':white, 'black':black,
                            'graph_version':model['version'], 'result':result,'joshua_points':jscore,
                            'mean_stockfish_cp_loss':round(sum(measured_losses)/len(measured_losses),2) if measured_losses else None,
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
        print(f'JOSHUA_V9_MATCH_ERROR {error}', file=sys.stderr, flush=True)
        sys.exit(2)
