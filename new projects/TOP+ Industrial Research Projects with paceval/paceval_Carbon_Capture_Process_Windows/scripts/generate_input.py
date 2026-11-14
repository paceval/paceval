#!/usr/bin/env python3
"""Deterministic reduced-order synthetic carbon-capture operating-point design.
The columns are physically dimensional; data are not plant observations.
"""
from pathlib import Path
import csv,math
ROOT=Path(__file__).resolve().parents[1]
NAMES='Fin Fgas Kla Vol Cstar Cbulk S lean maxload Tstrip Tfeed cp hx wt dh hvap etaMin qMax tMax'.split()
def main():
 out=ROOT/'input'/'operating_points.csv'
 # 4 load scenarios x 24 solvent/gas combinations x 32 operating conditions = 3072 rows
 with out.open('w',newline='',encoding='utf8') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['case_id','scenario']+NAMES)
  n=0
  for gi,tag in enumerate(['BASELINE','LOW_PCO2','HOT_STRIPPER','HIGH_CAPTURE']):
   for j in range(24):
    for k in range(32):
     fin=7.2+1.5*math.sin((j+2)/6)+.4*(gi==3)
     fgas=fin/(.10+.025*(gi!=1)+.008*(j%3))
     kla=.25+.009*j+.008*(k%7)
     vol=8+.25*(k%17)
     cstar=4.6+.10*(j%8)-.3*(gi==1)
     cbulk=2.1+.09*(k%9)
     S=27+.85*(j%18)+.22*(k%10)
     lean=.14+.006*(k%11)
     mx=.43+.008*(j%10)
     ts=385+.75*(k%32)+5*(gi==2)
     tf=309+.5*(j%12)
     cp=3.65+.025*(k%8)
     hx=.69+.01*(j%17)
     wt=.30
     dh=72+1.0*(j%9)
     hvap=8.5+.35*(k%11)
     em=.78+.02*(gi==3)
     qmax=4.5-.3*(gi==2)
     tmax=418
     row=[fin,fgas,kla,vol,cstar,cbulk,S,lean,mx,ts,tf,cp,hx,wt,dh,hvap,em,qmax,tmax]
     w.writerow([f'CC{n:05d}',tag]+[f'{v:.16g}' for v in row]);n+=1
 print('generated',n,'synthetic cases',out)
if __name__=='__main__':main()
