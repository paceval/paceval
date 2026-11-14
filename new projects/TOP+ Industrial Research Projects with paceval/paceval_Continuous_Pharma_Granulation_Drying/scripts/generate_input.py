#!/usr/bin/env python3
"""Deterministic synthetic research input, NOT measured granulation or PAT data."""
from pathlib import Path
import csv,math,random
r=random.Random(20261115)
root=Path(__file__).resolve().parents[1]
cols=['solid','water','baseMoist','Tair','Tin','Tref','time','kref','Ea','RH','eqBase','eqRH','eqTC','hcoef','latentCool','fastFraction','spread','rtdWidth','Mmin','Mmax','Tmax','sensor','sensorTol','target']
root.joinpath('input').mkdir(exist_ok=True)
with (root/'input/cases.csv').open('w',newline='',encoding='utf8') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['case_id','scenario']+cols)
 for i in range(2880):
  group=('normal','humid','hot','short_residence')[i%4]
  solid=r.uniform(10,32);L=r.uniform(.10,.255);water=solid*L
  Tin=r.uniform(287,306);Tref=345.;Tair=r.uniform(332,376) if group!='hot' else r.uniform(375,390)
  t=r.uniform(440,1000) if group!='short_residence' else r.uniform(200,530)
  kref=r.uniform(.0035,.0065);Ea=r.uniform(10000,18000)
  RH=r.uniform(.18,.46) if group!='humid' else r.uniform(.5,.78)
  base=r.uniform(.008,.026); eqBase=.007;eqRH=.016;eqTC=.004;hcoef=r.uniform(.0025,.005);cool=r.uniform(9,26);fast=.64;spread=.4;rtd=.12
  Mmin=.009;Mmax=.050;Tmax=362.;sensorTol=.012;target=.023
  M0=base+L;eq=eqBase+eqRH*RH*math.exp(-eqTC*(Tair-Tref));k=kref*math.exp((-Ea/8.31446261815324)*(1/Tair-1/Tref));Md=eq+(M0-eq)*math.exp(-k*t);wet=Md/(1+Md)
  sensor=wet+r.uniform(-.003,.003)
  row=[solid,water,base,Tair,Tin,Tref,t,kref,Ea,RH,eqBase,eqRH,eqTC,hcoef,cool,fast,spread,rtd,Mmin,Mmax,Tmax,sensor,sensorTol,target]
  w.writerow([f'CASE{i:05d}',group]+[format(x,'.16g') for x in row])
print('Generated 2880 deterministic synthetic cases, seed 20261115')
