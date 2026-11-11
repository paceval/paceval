#!/usr/bin/env python3
"""Independent high-accuracy ODE check (SciPy DOP853; optional dependency).

Usage: python3 src/validate_trajectories.py examples/scenarios.csv examples/trajectories.csv
The reference uses adaptive integration, not the demonstrator's fixed-step RK4.
"""
import csv
import sys
from pathlib import Path
from scipy.integrate import solve_ivp

def audit(scenarios_file, outputs_file):
    with Path(scenarios_file).open(newline='') as f:
        scenarios={s['scenario_id']:s for s in csv.DictReader(f)}
    with Path(outputs_file).open(newline='') as f:
        trajectories=list(csv.DictReader(f))
    if not trajectories: raise RuntimeError('No trajectory records')
    maximum=0.
    for row in trajectories:
        x=scenarios[row['scenario_id']]
        val=lambda name:float(x[name])
        t0,t1,ta=val('t1'),val('t2'),val('tamb')
        power,c1,c2,k12,h1,h2,krad=(val(k) for k in ['power','c1','c2','k12','h1','h2','krad'])
        def rhs(t,y):
            a,b=y
            q12=k12*(a-b)
            loss=h2*(b-ta)+krad*((b/300)**4-(ta/300)**4)
            return ((power-q12-h1*(a-ta))/c1,(q12-loss)/c2)
        solution=solve_ivp(rhs,(0.,float(row['time_s'])),[t0,t1],method='DOP853',rtol=2e-13,atol=2e-13)
        if not solution.success: raise RuntimeError(solution.message)
        reference=solution.y[:,-1]
        for k,name in enumerate(('paceval_T1_K','paceval_T2_K')):
            error=abs(reference[k]-float(row[name]))
            maximum=max(error,maximum)
            if error>1e-6: raise RuntimeError('%s %s: error %.12g K'%(row['scenario_id'],name,error))
    print('PASS: %d complete two-zone trajectories agree with independent SciPy DOP853' % len(trajectories))
    print('Maximum absolute temperature deviation: %.5g K'%maximum)

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: validate_trajectories.py scenarios.csv trajectories.csv')
    audit(sys.argv[1],sys.argv[2])
