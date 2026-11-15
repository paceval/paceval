#!/usr/bin/env python3
"""Additional independent consistency checks for all 147 synthetic axis input rows.
This is a reference-model unit test, not a claim that each entry is a stored raw MCP output.
"""
import sys,math,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'validation'))
import independent_model as im
n=0
for cid,rows in im.cases():
 ref=[im.axis_ref(x) for x in rows]
 for v,r in zip(rows,ref):
  I,Ij,Ik,w,wj,wk,h,hj,hk,tau,ext,dt,*rest=v
  # Complete body-frame angular momentum identity for the continuous v2 law.
  assert abs(r['angular_momentum_balance_residual_v2']) <= 1e-14
  # The physical torque is transferred with equal and opposite sign to the wheel.
  assert abs(r['wheel_h_next']-h+tau*dt)<=1e-14
  assert abs(r['acceleration_version_delta']+(wj*hk-wk*hj)/I)<=1e-13
  assert abs(r['sensitivity_accel_to_torque']-1/I)<1e-10
  assert abs(r['sensitivity_momentum_to_torque']+dt)<1e-13
  assert r['candidate_guard_v1']==float(r['normalized_score_v1']>=0)
  assert r['candidate_guard_v2']==float(r['normalized_score_v2']>=0)
  n+=7
 a=im.agg_ref(im.agg_inputs(ref));assert a['joint_guard_v1']==int(all(r['candidate_guard_v1'] for r in ref));assert a['joint_guard_v2']==int(all(r['candidate_guard_v2'] for r in ref));n+=2
# Source code has original SDK numeric gate, and no cloud execution is required for this Python test.
report={'reference_only_assertions':n,'passed':n,'failed':0,'remote_execution_claim':False}
(R/'results'/'reference_properties.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
