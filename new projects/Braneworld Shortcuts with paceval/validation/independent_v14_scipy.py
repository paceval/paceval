"""External-only, independently written SciPy method-of-lines validator.
Not linked into any paceval C++ source or production executable.
"""
import argparse,json
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

def calculate(ny=81,maxy=3,tmax=1.0,rho0=0.1,w=0,k=0,amp=0.04,start=.15,duration=.30,mode='pulse'):
    y=np.linspace(0,maxy,ny);dy=y[1]-y[0]
    def H(t):
        r=rho0*np.exp(-3*(1+w)*t)
        return np.sqrt((r/6)*(2+r/6))
    def rhs(T,Y):
        la=Y[0]
        u=Y[1:ny+1];q=Y[ny+1:]
        h=H(la);v=-h/np.sqrt(1+h*h);zb=np.exp(-la)
        if mode=='static': v=0;zb=1;la_rate=0
        else:la_rate=np.exp(la)*h/np.sqrt(1+h*h)
        source=amp*np.sin(np.pi*(T-start)/duration)**2 if mode=='pulse' and start<T<start+duration else 0
        # No C++ code path or paceval formulas reused: independent array operator.
        uy=np.gradient(u,dy,edge_order=2)
        qy=np.gradient(q,dy,edge_order=2)
        uy[0]=source-v*q[0]
        uy[-1]=0
        uyy=np.empty_like(u)
        uyy[1:-1]=(u[2:]-2*u[1:-1]+u[:-2])/dy**2
        uyy[0]=2*(u[1]-u[0])/dy**2-2*(source-v*q[0])/dy
        uyy[-1]=2*(u[-2]-u[-1])/dy**2
        du=q+v*uy
        dq=uyy-3*uy/(zb+y)-k*k*u+v*qy
        return np.concatenate(([la_rate],du,dq))
    y0=np.zeros(1+2*ny)
    if mode!='pulse':y0[1:ny+1]=1
    sol=solve_ivp(rhs,(0,tmax),y0,rtol=2e-9,atol=1e-11,max_step=.003,method='DOP853')
    if not sol.success:raise RuntimeError(sol.message)
    u=sol.y[1:ny+1,-1]
    return dict(scipy_brane=float(u[0]),scipy_quarter=float(u[ny//4]),
                scipy_half=float(u[ny//2]),scipy_threequarter=float(u[(3*ny)//4]),
                scipy_edge=float(u[-1]),scipy_lna=float(sol.y[0,-1]),nfev=sol.nfev)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--ny',type=int,default=81)
    ap.add_argument('--tmax',type=float,default=1)
    ap.add_argument('--mode',default='pulse')
    ap.add_argument('--k',type=float,default=0)
    ap.add_argument('--rho0',type=float,default=0.1)
    ap.add_argument('--w',type=float,default=0)
    ap.add_argument('--csv',required=True)
    a=ap.parse_args()
    result=calculate(ny=a.ny,tmax=a.tmax,mode=a.mode,k=a.k,rho0=a.rho0,w=a.w)
    row=pd.read_csv(a.csv).iloc[-1]
    delta={name:float(row[col])-result[name] for name,col in [
      ('scipy_brane','h_brane'),('scipy_quarter','h_yquart'),('scipy_half','h_yhalf'),
      ('scipy_threequarter','h_ythreequart'),('scipy_edge','h_edge')]}
    print(json.dumps(dict(reference=result,diff=delta,max_abs_difference=max(map(abs,delta.values()))),indent=2))
