import csv,math
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from models import eval_model,hubble

def fast(rho,w,D):
    # Integrate the brane's Minkowski coordinates once; avoid repeated quadratures.
    def rhs(t,y):
        a=math.exp(t); H=hubble(a,rho,w)
        return [math.sqrt(1+H*H)/(a*H), -1/(a), 1/(a*H),1/H]
    # log(a) interval; terminate if particle horizon reached before D
    sol=solve_ivp(rhs,(0,4),[0,1,0,0],rtol=2e-10,atol=2e-12,dense_output=True,max_step=.05)
    def vals(t):return sol.sol(t)
    def xb(t):return vals(t)[2]
    if xb(4)<=D:return None
    tb=brentq(lambda t:xb(t)-D,1e-10,4,xtol=2e-12)
    def bulk_dist(t):
        T,z,_,_=vals(t);return math.sqrt(max(0,T*T-(z-1)**2))
    tg=brentq(lambda t:bulk_dist(t)-D,1e-10,tb,xtol=2e-12)
    B=vals(tb);G=vals(tg)
    return dict(rho0=rho,w=w,D=D,tau_brane=B[3],tau_bulk=G[3],advance=B[3]-G[3],relative_pct=100*(B[3]-G[3])/B[3],a_brane=math.exp(tb),a_bulk=math.exp(tg),null_residual=G[0]**2-D**2-(G[1]-1)**2)

if __name__=='__main__':
    rows=[]
    for rho in [.1,1,10]:
      for w in [-1,-.9,-.5,0,1/3,1]:
       for D in [.1,.5,1]:
        try:
         r=fast(rho,w,D)
         if r:rows.append(r)
        except (ValueError,OverflowError):pass
    with open('scan_refined.csv','w',newline='') as f:
     out=csv.DictWriter(f,fieldnames=list(rows[0]));out.writeheader();out.writerows(rows)
    positive=[r for r in rows if r['w']>-1]
    print('Cases',len(rows),'positive w>-1',len(positive),'nonpositive',sum(r['advance']<=-1e-8 for r in positive))
    for r in sorted(positive,key=lambda r:r['relative_pct'],reverse=True)[:8]:print(r)
    print('deSitter max abs advance',max(abs(r['advance']) for r in rows if r['w']==-1))
    # Independent quadrature validation of representative case
    for rho,w,D in [(1,0,.5),(1,1/3,.5),(10,1,1)]:
      a=fast(rho,w,D);b=eval_model(rho,w,D)
      print('independent',rho,w,D,'advance',a['advance'],b['advance'],'difference',a['advance']-b['advance'])
