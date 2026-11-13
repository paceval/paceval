"""Deterministic synthetic *non-metrological* research inputs, no external dependencies."""
from pathlib import Path
import csv,math
ROOT=Path(__file__).resolve().parents[1]
def g(x):return .12+.75*x+.09*math.sin(9*x)+.035*math.sin(37*x)+.04*math.exp(-((x-.72)/.06)**2)
def ref_fun(x,T,drift):
    return g(x)*(1+.00035*(T-20))+.0005*(T-20)+.000075*math.sin(7*x)*(T-20)+drift*(.001+.0015*x)
rows=[]
for sn,tag in enumerate(['machine_axis','precision_sensor','quality_gate','temperature_cycle']):
    for i in range(180):
        x= i/179
        if i in [0,1,2,25,33,75,89,130,158,177,178,179]:
            x=min(1.,max(0., round(x*4096)/4096))
        T=(27+25*math.sin((i+sn*15)*.043)) if sn==3 else (5+11*sn+21*(.5+.5*math.cos((i+5*sn)*.04)))
        drift=.72*math.sin(.031*i+.49*sn)
        # Illustrative deterministic differences from an independent continuous target.
        shift= .00016*math.sin(i*.19+sn) + (.0055 if tag=='quality_gate' and 72<=i<107 else (.0018 if tag=='quality_gate' and 65<=i<125 else 0)) + (.0025 if tag=='precision_sensor' and i%29==0 else 0)
        ref=ref_fun(x,T,drift)+shift
        tol=.0025 if sn!=2 else .0021
        rows.append([tag,i,x,T,drift,ref,tol,.00025,.3,.16,.00035])
with (ROOT/'examples/synthetic_sensor_inputs.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['scenario','seq','x','T','drift','reference','tolerance','u_x','u_T','u_d','u_model']);w.writerows(rows)
print('Created',len(rows),'synthetic scenario inputs')
