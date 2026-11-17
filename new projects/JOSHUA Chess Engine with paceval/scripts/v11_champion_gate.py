#!/usr/bin/env python3
"""V12 immutable champion-versus-challenger match gate.

This is a decision-quality / chess-result gate, NOT a training oracle or a
statistical proof of stronger play. Every move comes from the real Joshua
binary with a specified TSV and is adjudicated by the real C++ referee.
An opening appears twice with candidate and incumbent alternating colors.
Games ending by artificial ply limits are marked inconclusive and cannot
cause promotion. The gate never writes the active model.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path

# Balanced complete four-ply openings, fixed before training. Each candidate
# plays twice from the identical resulting FEN, once per color. Unlike the
# earlier single-ply gate these are normal, symmetric opening developments.
CHALLENGE_LINES = {
    'open_king': ('e2e4','e7e5','g1f3','b8c6'),
    'queen_pawn': ('d2d4','d7d5','g1f3','g8f6'),
    'english': ('c2c4','e7e5','b1c3','g8f6'),
    'reti': ('g1f3','d7d5','g2g3','g8f6'),
    'fianchetto': ('b2b3','e7e5','c1b2','b8c6'),
    'sicilian': ('e2e4','c7c5','g1f3','d7d6'),
}
CHALLENGE_OPENINGS = tuple(CHALLENGE_LINES)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def criteria(results, min_score=0.625):
    """Outcome-only gate. Fail closed for incomplete, inconsistent or unpaired games."""
    if not results or len(results) % 2:
        return {'accepted': False, 'reason': 'No complete color pairs'}
    points = 0.0
    wins = draws = losses = 0
    for i in range(0, len(results), 2):
        a,b=results[i:i+2]
        if a.get('opening') != b.get('opening') or a.get('candidate_color') != 'black' or b.get('candidate_color') != 'white':
            return {'accepted': False, 'reason': 'Color-pair identity mismatch'}
        for game in (a,b):
            if game.get('result') not in ('1-0', '0-1', '1/2-1/2'):
                return {'accepted': False, 'reason': 'Incomplete or truncated comparison game'}
            if game.get('termination') not in ('checkmate','stalemate','insufficient_material','fifty_move_claim','threefold_repetition_claim'):
                return {'accepted': False, 'reason': 'Unverified termination condition'}
            z = (1.0 if game['result']=='1-0' and game['candidate_color']=='white' or
                 game['result']=='0-1' and game['candidate_color']=='black' else
                 0.5 if game['result']=='1/2-1/2' else 0.0)
            points += z
            if z == 1: wins += 1
            elif z == .5: draws += 1
            else: losses += 1
    total = len(results)
    score = points/total
    # A tiny sample provides a safety filter only, not statistical significance.
    accepted = score >= min_score and wins >= losses + 2
    return {'accepted': accepted, 'reason': 'Candidate passed paired result gate' if accepted else
            'Candidate did not outperform frozen champion by preset margin',
            'score': round(score, 4), 'points': points, 'games': total,
            'wins': wins, 'draws': draws, 'losses': losses,
            'minimum_score': min_score, 'win_margin_required': 2,
            'statistical_strength_claim': 'NOT_ESTABLISHED'}


def play_one(opening, candidate_color, frozen_champion, candidate_path,
             champion, challenger, args, directory, logger, api):
    """Creates a full trace while deleting large per-move scratch outputs."""
    fen = api.START
    position_counts = {api.referee(args.referee, fen)['key']: 1}
    moves = []
    for forced_move in CHALLENGE_LINES[opening]:
        previous_fen = fen
        a = api.referee(args.referee, fen, forced_move)
        fen = a['fen']
        position_counts[a['key']] = position_counts.get(a['key'],0) + 1
        moves.append({'ply':len(moves)+1,'actor':'forced opening',
                      'uci':forced_move,'san':a['san'],
                      'fen_before':previous_fen,'fen_after':fen})
    end_reason='max_plies_unfinished'
    count=0
    # Temporary per-move engine outputs are deleted after evidence verification.
    with tempfile.TemporaryDirectory(prefix='v11_chess_scratch_') as temporary:
        scratch=Path(temporary)
        for ply in range(len(moves)+1,args.champion_max_plies+1):
            if api.STOP:
                raise InterruptedError('Stopped during champion gate, no model promotion')
            state=api.referee(args.referee,fen)
            if state['status']!='ongoing':end_reason=state['status']; break
            if position_counts.get(state['key'],0)>=3:
                end_reason='threefold_repetition_claim';break
            actor_color='white' if ' w ' in fen else 'black'
            selecting = challenger if actor_color == candidate_color else champion
            model_path = candidate_path if actor_color == candidate_color else frozen_champion
            out_dir=scratch/f'ply_{ply}'
            begin=time.monotonic()
            chosen=api.joshua_choice(args.joshua,fen,selecting,model_path,args.depth,args.quiescence,
                                     args.move_timeout,out_dir,logger,args.progress_seconds,
                                     verify_margin_cp=args.verify_margin_cp,
                                     verify_extra_depth=args.verify_extra_depth)
            advance=api.referee(args.referee,fen,chosen['move'])
            row={'ply':ply,'actor':'challenger' if actor_color==candidate_color else 'champion',
                 'graph_version':selecting['version'], 'side':actor_color,
                 'uci':chosen['move'],'san':advance['san'], 'fen_before':fen,
                 'fen_after':advance['fen'],'move_s':round(time.monotonic()-begin,3),
                 'paceval_adaptive_evaluations':chosen['evidence']['graph_evaluations']}
            moves.append(row)
            logger.event('CHAMPION_DUEL_MOVE',ply=ply,actor=row['actor'],uci=row['uci'],
                         graph_version=row['graph_version'],move_s=row['move_s'])
            shutil.rmtree(out_dir)
            fen=advance['fen'];position_counts[advance['key']]=position_counts.get(advance['key'],0)+1
            count+=1
            if advance['status']!='ongoing':end_reason=advance['status'];break
    if end_reason=='checkmate': result='0-1' if ' w ' in fen else '1-0'
    elif end_reason in ('stalemate','insufficient_material','fifty_move_claim','threefold_repetition_claim'):result='1/2-1/2'
    else:result='*'
    return {'opening':opening,'candidate_color':candidate_color,'result':result,
            'termination':end_reason,'played_plies':len(moves),'moves':moves,
            'candidate_model_sha256':sha256(candidate_path),
            'champion_model_sha256':sha256(frozen_champion)}


def compare(champion_path, candidate_path, args, folder, logger, api):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    frozen=folder/'frozen_champion.tsv'
    frozen.write_bytes(Path(champion_path).read_bytes())
    candidate_snapshot=folder/'frozen_challenger.tsv'
    candidate_snapshot.write_bytes(Path(candidate_path).read_bytes())
    champion=api.parse_model(frozen);challenger=api.parse_model(candidate_snapshot)
    if champion['version'] == challenger['version']:
        raise ValueError('Champion and challenger must use distinct version numbers')
    original_champion=sha256(champion_path)
    results=[]
    for index,opening in enumerate(CHALLENGE_OPENINGS[:args.champion_pairs]):
        for side in ('black','white'):
            logger.event('CHAMPION_DUEL_START',opening=opening,candidate_side=side,
                         champion_version=champion['version'],challenger_version=challenger['version'])
            game=play_one(opening,side,frozen,candidate_snapshot,champion,challenger,args,
                          folder,logger,api)
            results.append(game)
            api.json_write(folder/f'pair_{index+1:02d}_{side}.json',game)
            logger.event('CHAMPION_DUEL_END',opening=opening,candidate_side=side,
                         result=game['result'],reason=game['termination'])
    if sha256(champion_path)!=original_champion:
        raise RuntimeError('Frozen champion file changed during comparison')
    verdict=criteria(results,args.champion_min_score)
    summary={'gate':'V11_champion_challenger_actual_Joshua_match',
             'champion_version':champion['version'],'challenger_version':challenger['version'],
             'champion_sha256':sha256(frozen),'candidate_sha256':sha256(candidate_snapshot),
             'paired_openings':list(CHALLENGE_OPENINGS[:args.champion_pairs]),
             'depth':args.depth,'quiescence':args.quiescence,'max_plies':args.champion_max_plies,
             'verify_margin_cp':args.verify_margin_cp,
             'verify_extra_depth':args.verify_extra_depth,
             'opening_lines':{name:list(CHALLENGE_LINES[name]) for name in CHALLENGE_OPENINGS[:args.champion_pairs]},
             'results':[{k:v for k,v in r.items() if k!='moves'} for r in results],
             **verdict}
    api.json_write(folder/'champion_gate_verdict.json',summary)
    logger.event('CHAMPION_GATE_VERDICT',accepted=verdict['accepted'],reason=verdict['reason'],
                 score=verdict.get('score'),games=verdict.get('games'))
    return summary
