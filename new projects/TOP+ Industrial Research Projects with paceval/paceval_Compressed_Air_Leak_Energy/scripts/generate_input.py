#!/usr/bin/env python3
"""Deterministic synthetic SI-pressure, leak and useful demand grid. NOT measurements."""
from pathlib import Path
import csv, math
COLS='Pabs Pamb Tin area Cd gamma Rgas mref Pref exponent demand supplyCap Pmin kdrop eta cp hours price maxFraction Pmax'.split()
OUT=Path(__file__).resolve().parents[1]/'input'/'cases.csv'
def sample():
 for i in range(3072):
  group='near_atmosphere' if i%32==0 else ['normal','high_pressure','lower_pressure','demand_peak'][i%4]
  baseP={'normal':680000,'high_pressure':900000,'lower_pressure':520000,'demand_peak':750000,'near_atmosphere':185000}[group]
  P=baseP+(i%37-18)*(800 if group=='near_atmosphere' else 3500)
  T=288+((i*7)%34)
  area=0.35+((i*13)%57)*.06
  Cd=.61+(i%9)*.016
  pa=101325.;gamma=1.4; R=287.05; Pref=750000.
  # Calibrated V1 reference input from the independent V2 ideal-gas choked formula at Pref.
  c=Cd*area*1e-6*Pref*math.sqrt(gamma/(R*T))*(2/(gamma+1))**((gamma+1)/(2*(gamma-1)))
  exponent=.50+(i%8)*.04
  demand=.035+(i*17%107)*.0011
  capacity=.125+(i%13)*.0075
  pmin=445000+(i%7)*16000
  kdrop=100000+(i%9)*22000
  eta=.71+(i%7)*.02
  cp=1005.
  hours=3800+(i%7)*420
  price=.13+(i%7)*.017
  fmax=.045+(i%9)*.013
  pmax=960000.
  row=[P,pa,T,area,Cd,gamma,R,c,Pref,exponent,demand,capacity,pmin,kdrop,eta,cp,hours,price,fmax,pmax]
  yield [f'CASE{i:05d}',group]+[format(float(x),'.17g') for x in row]
if __name__=='__main__':
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',encoding='utf8',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['case_id','scenario']+COLS);w.writerows(sample())
 print(OUT)
