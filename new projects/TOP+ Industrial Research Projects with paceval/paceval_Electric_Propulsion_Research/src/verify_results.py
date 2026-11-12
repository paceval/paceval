#!/usr/bin/env python3
"""Audit released files, physical identities, graph registry and replay counts."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'examples'
def rows(filename):return list(csv.DictReader(open(D/filename)))
def main():
    reg=rows('rule_registry.csv');assert len(reg)==51
    assert len({r['formula'] for r in reg})==51,'formulas must be distinct'
    assert [int(r['version']) for r in reg].count(2)==1
    surfaces=[rows(name+'_surface.csv') for name in ['efficiency','thrust','specific_impulse','thrust_to_power','waste_power']]
    assert all(len(s)==3721 for s in surfaces)
    g0=9.80665
    for r_eta,r_t,r_isp,r_tp,r_w in zip(*surfaces):
        p=float(r_eta['power_w']);m=float(r_eta['flow_mg_s']);eta=float(r_eta['value']);T=float(r_t['value'])/1000
        assert 0<eta<1
        assert abs(T*T/(2*m*1e-6*p)-eta)<1e-10
        assert abs(float(r_isp['value'])-T/(m*1e-6*g0))<1e-8
        assert abs(float(r_tp['value'])-1e6*T/p)<1e-8
        assert abs(float(r_w['value'])-p*(1-eta))<1e-8
    replay=rows('performance_replay.csv');assert len(replay)>500
    log=(D/'sdk_execution.txt').read_text()
    assert 'STATUS PASS' in log and 'REPLAY_UPDATES 10000' in log and 'GRAPH_COUNT 51' in log
    assert 'BATCH_VERIFIED 1600' in log
    print('PASS registry, replay, five surfaces, physical identities')
if __name__=='__main__':main()
