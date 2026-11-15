#!/usr/bin/env python3
"""Regenerate exactly the recorded deterministic synthetic candidate inputs."""
from pathlib import Path
import csv,random,sys,hashlib,tempfile

def create(path):
 random.seed(20261115)
 with open(path,'w',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['candidate_id','k1','k2','k3','a','b','c','d','p1','p2','R','eps','umax'])
  for i in range(192):
   k1=round(random.uniform(-.58,1.2),5);k2=round(random.uniform(-1.13,1.13),5);k3=round(random.uniform(0,1.4),5)
   a=round(random.uniform(.32,.62),5);b=round(random.uniform(.34,.72),5);c=round(random.uniform(.1,.25),5);d=round(random.uniform(.06,.19),5)
   p1,p2,R,eps,umax=1.2,1.0,1.0,.05,2.8
   if i==0:k1,k2,k3,a,b,c,d=.4,0,.7,.5,.65,.16,.11
   if i==1:k1,k2,k3,a,b,c,d=-.45,0,0,.42,.55,.12,.1
   if i==2:k1,k2,k3,a,b,c,d=.28,.9,.5,.5,.55,.2,.13
   w.writerow([f'C{i:04d}',k1,k2,k3,a,b,c,d,p1,p2,R,eps,umax])
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--check':
  with tempfile.TemporaryDirectory() as td:
   q=Path(td)/'generated.csv';create(q);a=q.read_bytes();b=Path(sys.argv[2]).read_bytes();assert a==b,'Synthetic generator does not reproduce canonical input bytes';print('GENERATOR REPRODUCIBILITY PASS',len(a),'bytes')
 elif len(sys.argv)==2:create(sys.argv[1]);print('CREATED',sys.argv[1])
 else:raise SystemExit('Usage: generate_input.py OUTPUT.csv | --check INPUT.csv')
