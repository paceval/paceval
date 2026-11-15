#!/usr/bin/env python3
"""Independent feature extraction + Decimal(80) checks of real local paceval batch output."""
import csv,sys
from decimal import Decimal, getcontext
getcontext().prec=80
FEATURES=['wp','wn','wb','wr','wq','bp','bn','bb','br','bq','wc','bc','wd','bd','wa','ba','wk','bk','bias','wpsq','bpsq','wdoub','bdoub','wisolated','bisolated','wpassed','bpassed','wbpair','bbpair','wshield','bshield','tempo']

def feats(fen):
 parts=fen.split();assert len(parts)==6
 ranks=parts[0].split('/'); assert len(ranks)==8
 cells={}
 for r,row in enumerate(ranks):
  f=0
  for ch in row:
   if ch.isdigit():f+=int(ch)
   else:
    cells[(r,f)]=ch;f+=1
  assert f==8
 result={name:Decimal(0) for name in FEATURES}
 result['bias']=Decimal(1);result['tempo']=Decimal(1 if parts[1]=='w' else -1)
 pawns=[[0]*8,[0]*8]
 for (r,f),p in cells.items():
  if p.lower()=='p':pawns[0 if p.isupper() else 1][f]+=1
 for idx,col in enumerate(('w','b')):
  pcs={p.lower():0 for p in 'PNBRQ'}
  for p in cells.values():
   if p.isupper()==(idx==0) and p.lower() in pcs:pcs[p.lower()]+=1
  for key,suffix in [('p','p'),('n','n'),('b','b'),('r','r'),('q','q')]: result[col+suffix]=Decimal(pcs[key])
  result[col+'bpair']=Decimal(pcs['b']>=2)
  for f in range(8):
   n=pawns[idx][f]
   result[col+'doub']+=Decimal(max(0,n-1))
   if (f==0 or not pawns[idx][f-1]) and (f==7 or not pawns[idx][f+1]):result[col+'isolated']+=Decimal(n)
 for (r,f),p in cells.items():
  side=0 if p.isupper() else 1
  col='w' if side==0 else 'b'
  if 2<=r<=5 and 2<=f<=5:result[col+'c']+=1
  if p in 'NB' and r<7:result['wd']+=1
  if p in 'nb' and r>0:result['bd']+=1
  if p=='P':result['wa']+=6-r
  if p=='p':result['ba']+=r-1
  if p=='K':result['wk']=Decimal(f in (2,6))
  if p=='k':result['bk']=Decimal(f in (2,6))
  cf=min(f,7-f);cr=min(r,7-r)
  typ=p.lower();q=0
  if typ=='n':q=8*(cf+cr)
  if typ=='b':q=5*(cf+cr)
  if typ=='r':q=3*cr
  if typ=='q':q=2*(cf+cr)
  if typ=='p':q=3*cf+2*(6-r if side==0 else r-1)
  result[col+'psq']+=q
  if typ=='p':
   enemy='p' if side==0 else 'P'
   passed=not any(cp==enemy and abs(ff-f)<=1 and (rr<r if side==0 else rr>r) for (rr,ff),cp in cells.items())
   if passed:result[col+'passed']+=1
  if typ=='k':
   ahead=-1 if side==0 else 1
   own='P' if side==0 else 'p'
   for delta in (1,2):
    for df in (-1,0,1):
     if cells.get((r+ahead*delta,f+df))==own:result[col+'shield']+=1
 return result

def expected(features):
 d=features
 material=sum(Decimal(w)*(d['w'+x]-d['b'+x]) for x,w in [('p',100),('n',320),('b',330),('r',500),('q',900)])
 activity=d['wpsq']-d['bpsq']
 structure=-16*(d['wdoub']-d['bdoub'])-12*(d['wisolated']-d['bisolated'])+22*(d['wpassed']-d['bpassed'])+28*(d['wbpair']-d['bbpair'])
 shelter=9*(d['wshield']-d['bshield']);tempo=7*d['tempo']
 center=d['wc']-d['bc']; development=d['wd']-d['bd']; advance=d['wa']-d['ba'];king=d['wk']-d['bk']
 score=material+13*center+17*development+3*advance+18*king+activity+structure+shelter+tempo
 return {'SCORE':score,'MATERIAL':material,'POSITIONAL_ACTIVITY':activity,'PAWN_STRUCTURE':structure,'KING_SHELTER':shelter,'TEMPO':tempo,'SCORE_MARGIN':Decimal(2000)-abs(score),'SCORE_GUARD':Decimal(int(abs(score)<=2000 and d['wp']>=0 and d['bp']>=0)),'SENSITIVITY_ACTIVITY_WEIGHT':activity,'POSITIONAL_COMPOSITE':13*center+17*development+activity}

def audit(path):
 with open(path,newline='',encoding='utf8') as f:rows=list(csv.DictReader(f))
 assert len(rows)==10
 comparisons=0
 for row in rows:
  f=feats(row['fen']);e=expected(f)
  for key in FEATURES:
   assert Decimal(row[key])==f[key],f'feature {key} case {row["case"]}: {row[key]} != {f[key]}'
   comparisons+=1
  for key,value in e.items():
   got=Decimal(row[key]);assert abs(got-value)<Decimal('1e-10'),f'paceval value mismatch {key} {row["case"]}: {got} != {value}'
   comparisons+=1
 print(f'V3_INDEPENDENT_DECIMAL_PASS cases={len(rows)} independent_checks={comparisons} precision={getcontext().prec}')
if __name__=='__main__':audit(sys.argv[1])
