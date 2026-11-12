#!/usr/bin/env python3
"""Independent Python SplitMix64 implementation and 55-digit mpmath spot checks."""
from pathlib import Path
import csv,json,mpmath as m
m.mp.dps=55
ROOT=Path(__file__).resolve().parent.parent
MASK=(1<<64)-1
class Splitmix:
 def __init__(self,s):self.s=s
 def next(self):
  self.s=(self.s+0x9e3779b97f4a7c15)&MASK;z=self.s
  z=((z^(z>>30))*0xbf58476d1ce4e5b9)&MASK
  z=((z^(z>>27))*0x94d049bb133111eb)&MASK
  return (z^(z>>31))&MASK
 def uniform(self):return (self.next()>>11)*(1/9007199254740992.)

def terms(s,n):
 rng=Splitmix(0xACE20261112+s*10991)
 for i in range(n):
  a=(rng.uniform()*2-1)*.065/(n/2048.)**.5
  cx=-1.15+2.3*rng.uniform();cy=-1.15+2.3*rng.uniform()
  sx=.006+.09*rng.uniform();sy=.006+.09*rng.uniform()
  yield tuple(map(lambda z:m.mpf(z),[a,cx,cy,sx,sy]))

def bg(s,x,y):
 c=m.mpf
 def ga(a,b,p,q):return m.exp(-((x-c(a))**2/c(p)+(y-c(b))**2/c(q)))
 if s==0:
  return c('.72')*ga('-.46','.19','.082','.14')+c('.57')*ga('.48','.53','.12','.085')-c('.85')*ga('.27','-.31','.085','.11')+c('.10')*m.sin(7*x)*m.cos(5*y)-c('.055')*(x+y)
 if s==1:
  t1=c('.95')*ga('-.07','.06','.17','.19')
  t2=-c('.62')*ga('-.07','.06','.028','.03')
  t3=c('.16')*m.sin(12*x+4*y)*m.exp(-((x+c('.04'))**2+(y-c('.09'))**2)/c('.75'))
  t4=-c('.13')*ga('.62','-.44','.08','.1')
  return t1+t2+t3+t4
 return c('.35')*m.sin(c('2.8')*x+c('1.4')*y)+c('.22')*m.cos(c('3.8')*y-c('.6')*x)-c('.65')*m.exp(-((x+c('.2')*y+c('.13'))**2/c('.028')))+c('.18')*ga('.62','-.45','.048','.095')+c('.11')*m.sin(11*x+3*y)*m.cos(5*y)

def verify():
 stats=[]
 for s,(name,n) in enumerate([('alpine_lake',2048),('volcanic_caldera',3072),('canyon_ridges',4096)]):
  rows=list(csv.DictReader((ROOT/'examples'/f'{name}_height_grid.csv').open()))
  ts=list(terms(s,n)); worst=0
  for ix in [0,len(rows)//2,len(rows)-1]:
   r=rows[ix];x=m.mpf(float(r['x']));y=m.mpf(float(r['y']))
   val=bg(s,x,y)+m.fsum(a*m.exp(-((x-cx)**2/sx+(y-cy)**2/sy)) for a,cx,cy,sx,sy in ts)
   delta=abs(val-m.mpf(float(r['height'])));worst=max(worst,float(delta))
   assert delta < m.mpf('3e-9'),(name,delta)
  stats.append(dict(scene=name,precision_digits=55,points_verified=3,max_abs_difference=worst,status='PASS'))
 (ROOT/'results'/'high_precision_audit.json').write_text(json.dumps(stats,indent=2)+'\n')
 print('PASS 9 independent 55-digit terrain evaluations')
if __name__=='__main__':verify()
