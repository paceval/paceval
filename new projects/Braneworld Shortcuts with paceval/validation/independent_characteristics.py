"""Independent characteristic comparison for a finite-radius source in v1.4b.
Not included in C++ physics implementation; SciPy is only external validation.
"""
import json
import pandas as pd
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

rho0,w,D,source_r,source_t=10.,-.5,1.,.12,.02

def ode(T,state):
    a=np.exp(state[0]);r=rho0*np.exp(-3*(1+w)*state[0]);h=np.sqrt((r/6)*(2+r/6));Q=np.sqrt(1+h*h)
    return [a*h/Q,1/Q]
sol=solve_ivp(ode,(0,1.8),[0,0],rtol=2e-13,atol=1e-14,
              max_step=.002,dense_output=True)
la0,x0=sol.sol(source_t); z0=np.exp(-la0)

char={}
for label,distance in [('center',D),('closest_edge',D-source_r)]:
    Tb=brentq(lambda T:sol.sol(T)[1]-x0-distance,source_t+.1,1.8)
    Tg=brentq(lambda T:(T-source_t)**2-(np.exp(-sol.sol(T)[0])-z0)**2-distance**2,
              source_t+.1,1.8)
    char[label]={'bulk_T':Tg,'brane_T':Tb,'delta_T':Tb-Tg}

thresholds=[]
for n in (31,61):
    d=pd.read_csv(f'results/planar_n{n}.csv')
    row={'grid':n,'receiver_final':float(d.field_receiver.iloc[-1])}
    for th in [1e-12,1e-9,1e-7,1e-6,1e-5]:
       subset=d[d.field_receiver.abs()>th]
       row[f'T_first_abs_greater_{th}']=float(subset.T.iloc[0]) if False else (
             float(subset['T'].iloc[0]) if len(subset) else None)
    thresholds.append(row)
print(json.dumps({'physical_model':{'rho0':rho0,'w':w,'receiver_D':D,
      'source_radius':source_r,'emission_start_T':source_t},'ray_characteristics':char,
      'threshold_times_are_not_wavefront_proofs':thresholds},indent=2))
