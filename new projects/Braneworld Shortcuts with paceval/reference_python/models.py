"""Z2 planar brane, 8piG5=ell=c=1; AdS5 pure bulk (mu=0).
Israel: H^2=(rho_total/6)^2-1, rho_total=6+rho_m, rho_m=rho_m0 a^-3(1+w).
Bulk Poincare ds^2=z^-2(-dT^2+dX^2+dz^2).
"""
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

def hubble(a,rho0,w):
    rho=rho0*a**(-3*(1+w))
    return np.sqrt((1+rho/6)**2-1)
def coords(a,rho0,w):
    # at a=1, T=0, z=1. dT/da=sqrt(1+H^2)/(a^2 H), dz/da=-1/a²
    T=quad(lambda u: np.sqrt(1+hubble(u,rho0,w)**2)/(u*u*hubble(u,rho0,w)),1,a,epsabs=1e-11)[0]
    z=1/a
    x=quad(lambda u: 1/(u*u*hubble(u,rho0,w)),1,a,epsabs=1e-11)[0]
    return T,z,x

def eval_model(rho0,w,D):
    if not (rho0>0 and -1<=w<=1 and D>0):raise ValueError('invalid')
    def xbrane(a):return coords(a,rho0,w)[2]
    upper=2.0
    while xbrane(upper)<D and upper<1e5:upper*=2
    if xbrane(upper)<D:raise ValueError("receiver beyond brane particle horizon")
    a_b=brentq(lambda a:xbrane(a)-D,1+1e-10,upper,xtol=1e-11)
    def xbulk(a):
        T,z,_=coords(a,rho0,w)
        return np.sqrt(max(0,T*T-(z-1)**2))
    a_g=brentq(lambda a:xbulk(a)-D,1+1e-10,a_b,xtol=1e-11)
    # time is monotone in a; proper time difference
    tau=lambda a:quad(lambda u:1/(u*hubble(u,rho0,w)),1,a,epsabs=1e-11)[0]
    Tb,zb,_=coords(a_b,rho0,w); Tg,zg,_=coords(a_g,rho0,w)
    return dict(rho0=rho0,w=w,D=D,a_brane=a_b,a_bulk=a_g,tau_brane=tau(a_b),tau_bulk=tau(a_g),advance=tau(a_b)-tau(a_g),bulk_null_residual=Tg*Tg-D*D-(zg-1)**2,bulk_T=Tg,bulk_z=zg)
if __name__=='__main__':
 for w in [0,1/3,-1]:
  for D in [.1,.5,1]:
   try:print(eval_model(1,w,D))
   except Exception as e:print(type(e).__name__,str(e))
