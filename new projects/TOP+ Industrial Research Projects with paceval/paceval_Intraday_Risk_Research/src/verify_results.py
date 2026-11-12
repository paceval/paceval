#!/usr/bin/env python3
"""Structural reproducibility audit for released datasets."""
from pathlib import Path
import csv
root=Path(__file__).resolve().parents[1]
def rows(name):return list(csv.DictReader((root/'examples'/name).open()))
assert len(rows('rule_registry.csv'))==51
assert len(rows('risk_replay.csv'))==800
assert len(rows('family_summary.csv'))==50
assert len(rows('risk_surface.csv'))==3721
assert len(rows('stress_scenarios.csv'))==81
assert len(rows('formula_revision.csv'))==61
log=(root/'examples/sdk_execution.txt').read_text()
for t in ['STATUS PASS','REPLAY_UPDATES 20000','GRAPH_COUNT 51','BATCH_VERIFIED 1600','SURFACE_POINTS 3721']:assert t in log,t
print('PASS released datasets and report counts')
