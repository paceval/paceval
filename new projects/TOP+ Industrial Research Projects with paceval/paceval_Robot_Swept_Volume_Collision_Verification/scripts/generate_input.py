#!/usr/bin/env python3
"""Synthetic dyadic-relative-trajectory dataset; seed fixed; no industrial measurements."""
import csv,random,sys
from pathlib import Path
random.seed(20261115)
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'input/cases.csv'
OUT.parent.mkdir(parents=True,exist_ok=True)
H=['case_id','scenario','x0','x1','x2','y0','y1','y2','z0','z1','z2','r1','r2','buffer']
def q(n):return f'{n/256:.8f}'  # every original input is an EXACT binary rational
cases=[]
def add(name,p):
 cases.append((f'T{len(cases):05d}',name,[q(n) for n in p]))
# Explicit contacts and sparse-waypoint counterexamples. Units: metres, time u=t/T in [0,1].
add('narrow_between_waypoints',[-516,1024,0,0,0,0,0,0,0,1,1,32])
add('tangency_midpoint',[-256,512,0,128,0,0,0,0,0,64,64,32])
add('endpoint_contact',[128,256,0,0,0,0,0,0,0,64,64,32])
add('near_miss_nominal',[-256,512,0,132,0,0,0,0,0,64,64,32])
add('clear_both',[-256,512,0,256,0,0,0,0,0,64,64,32])
add('static_overlap',[0,0,0,0,0,0,0,0,0,64,64,32])
add('static_clear',[256,0,0,256,0,0,0,0,0,64,64,32])
add('grazing_accelerated',[-128,256,0,128,0,0,0,0,0,64,64,32])
for i in range(4088):
 group=['crossing','clearance','accelerated','near_buffer'][i%4]
 if group=='crossing':
  v=[random.randint(-320,-128),random.randint(400,760),random.randint(-110,110),random.randint(-96,96),random.randint(-170,170),random.randint(-100,100),random.randint(-70,70),random.randint(-100,100),random.randint(-80,80)]
 elif group=='clearance':
  v=[random.randint(-320,-128),random.randint(250,600),random.randint(-110,110),random.randint(280,620),random.randint(-90,90),random.randint(-90,90),random.randint(-128,128),random.randint(-60,60),random.randint(-60,60)]
 elif group=='accelerated':
  v=[random.randint(-410,410),random.randint(-590,590),random.randint(-340,340),random.randint(-260,260),random.randint(-350,350),random.randint(-260,260),random.randint(-170,170),random.randint(-230,230),random.randint(-160,160)]
 else:
  v=[-256,512,random.randint(-30,30),random.randint(110,180),random.randint(-24,24),random.randint(-24,24),random.randint(-45,45),random.randint(-24,24),random.randint(-24,24)]
 r1=random.randint(39,76);r2=random.randint(39,76)
 buf=random.choice([16,32,48])
 add(group,v+[r1,r2,buf])
with OUT.open('w',newline='',encoding='utf8') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(H)
 for r in cases:w.writerow([r[0],r[1],*r[2]])
assert len(cases)==4096
print('DATASET',OUT,len(cases),'EXACT_DYADIC',True)
