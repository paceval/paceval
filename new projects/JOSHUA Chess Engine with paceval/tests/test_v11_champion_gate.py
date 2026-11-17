#!/usr/bin/env python3
"""V11 deterministic policy tests. Explicit mocks are NOT chess-strength evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('v11_gate',ROOT/'scripts/v11_champion_gate.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

def fake_pair(opening, winner='challenger'):
    def row(color):
        if winner=='draw':res='1/2-1/2';why='stalemate'
        elif winner=='challenger':res='1-0' if color=='white' else '0-1';why='checkmate'
        else:res='0-1' if color=='white' else '1-0';why='checkmate'
        return {'opening':opening,'candidate_color':color,'result':res,'termination':why}
    return [row('black'),row('white')]

def test_decision_policy():
    good=sum([fake_pair(x) for x in gate.CHALLENGE_OPENINGS[:4]],[])
    assert gate.criteria(good)['accepted']
    assert gate.criteria(sum([fake_pair(x,'champion') for x in gate.CHALLENGE_OPENINGS[:4]],[]))['accepted'] is False
    assert gate.criteria(sum([fake_pair(x,'draw') for x in gate.CHALLENGE_OPENINGS[:4]],[]))['accepted'] is False
    assert not gate.criteria(good[:1])['accepted']
    corrupt=[dict(x) for x in good];corrupt[-1]['result']='*'
    assert not gate.criteria(corrupt)['accepted']
    corrupt=[dict(x) for x in good];corrupt[1]['candidate_color']='black'
    assert not gate.criteria(corrupt)['accepted']
    print('V11_CHAMPION_CRITERIA_PASS: paired color, wins, draws, truncations, mismatch')

def test_frozen_files():
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp);champ=folder/'active.tsv';challenger=folder/'new.tsv'
        champ.write_text('old model');challenger.write_text('new model')
        assert gate.sha256(champ)!=gate.sha256(challenger)
        # Champion file is never modified by criteria computation.
        _=gate.criteria(fake_pair('b2b4'))
        assert champ.read_text()=='old model'
        print('V11_IMMUTABLE_GATE_TEST_PASS: external model remains unchanged')

if __name__=='__main__':
    test_decision_policy();test_frozen_files()
