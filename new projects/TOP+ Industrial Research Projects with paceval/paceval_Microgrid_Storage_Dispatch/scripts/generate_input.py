#!/usr/bin/env python3
"""Synthetic, deterministic dispatch candidates, NOT measured industrial records."""
import csv, math, random, pathlib
root=pathlib.Path(__file__).resolve().parents[1]; out=root/'input'; out.mkdir(exist_ok=True)
with (out/'parameters.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n'); w.writerow(['parameter','value','unit']);
    for a,b,c in [
        ('dt',1,'h'),('etaC',.95,'1'),('etaD',.93,'1'),('etaSlope',.26,'1'),
        ('emax',650,'kWh'),('emin',60,'kWh'),('eres',145,'kWh'),('goal',205,'kWh'),('einitial',350,'kWh'),
        ('chmax',125,'kW'),('dismax',125,'kW'),('genmax',230,'kW'),('impmax',280,'kW'),('expmax',210,'kW'),
        ('fuel',.26,'USD/kWh'),('sell',.08,'USD/kWh'),('ccurt',.025,'USD/kWh'),
        ('cshed',4.0,'USD/kWh'),('cage',.035,'USD/kWh'),('ramp',.001,'USD/kW-change'),
        ('rampmax',150,'kW/step'),('tol',.00005,'kW')]:w.writerow([a,str(b),c])
rows=[]
for scenario in ['grid_sunny','grid_cloudy','island_outage']:
 for sid in range(360):
    rng=random.Random(20261114+sid*29+10000*(['grid_sunny','grid_cloudy','island_outage'].index(scenario)))
    amp=(.95 if scenario=='grid_sunny' else .40 if scenario=='grid_cloudy' else .63)
    level=.52+sid/360*1.06
    lastgen=0.0
    for h in range(24):
        pv=max(0,330*amp*math.sin(math.pi*(h-6)/12))
        load=155 + 36*(1+math.sin(2*math.pi*(h-8)/24))/2 + 34*(1+math.cos(4*math.pi*(h-18)/24))/2
        load*= 1 + .07*math.sin(sid*0.7)
        ch=(42*level if 10<=h<=15 else (8*level if h in [0,1] and sid%4==0 else 0))
        dis=(49*level if 18<=h<=22 else (15*level if 6<=h<=8 and sid%3==0 else 0))
        if sid%71==0 and h==15:dis=7  # Deliberate charge/discharge conflict
        if sid%83==0 and h==12:ch=140  # Deliberate power-bound violation
        buy=.18 + (.16 if 17<=h<=21 else .025 if 9<=h<=15 else .075)
        if scenario=='island_outage':
            gen=max(0,min(230,load+ch-dis-pv))
            shed=max(0,load+ch-dis-pv-gen)
            curt=max(0,pv+gen+dis-ch-(load-shed))
            pimp=pexp=0.
            if sid%49==0 and h==21: gen=max(0,gen-7) # intentionally unbalanced
        else:
            gen=(16+sid%6*9 if scenario=='grid_cloudy' else sid%9*5)
            shed=0.
            curt=0.
            net=load+ch+0-gen-dis-pv
            if net>=0:
                pimp=min(280,net); pexp=0.
            else:
                pimp=0.; pexp=min(210,-net); curt=max(0,-net-pexp)
            if sid%43==0 and h==7:pimp+=3 # intentionally unbalanced
        rows.append([scenario,f'{sid:04d}',h,pv,load,gen,ch,dis,pimp,pexp,curt,shed,buy])
with (out/'dispatch_candidates.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(['scenario','schedule_id','hour','pv_kW','load_kW','gen_kW','charge_kW','discharge_kW','import_kW','export_kW','curtail_kW','shed_kW','buy_USD_per_kWh']);
    for row in rows:w.writerow([*(row[:3]),*(f'{x:.10f}' for x in row[3:])])
print('generated',len(rows),'hourly synthetic rows,',len(rows)//24,'24-hour schedules')
