#!/usr/bin/env python3
"""V12 bounded multiple template proposals. Synthetic policy-only fixture."""
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import stockfish_match as m
args=SimpleNamespace(candidate_budget=8,structural_step=.5,step=2)
active={'extra':{'king_alarm':.5}}
for game in (2,6,14,25):
 for mate in (False,True):
  plans=m.candidate_plans(game,mate,active,args)
  assert len(plans)==8,plans
  assert len(set(t for cat,t,_ in plans if cat=='nonlinear'))>=3
  assert all(cat=='nonlinear' and term in m.EXTRA_FORMULAS or
             cat=='linear' and term in m.TERMS for cat,term,delta in plans)
  assert len({(cat,term,delta) for cat,term,delta in plans})==len(plans)
  assert plans==m.candidate_plans(game,mate,active,args)
print('V12_MULTI_TEMPLATE_POLICY_PASS: deterministic, bounded, 3 nonlinear features, no custom text')
