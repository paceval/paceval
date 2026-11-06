import math
from models import eval_model,hubble
from refine import fast

def curvature(a,rho0,w):
    rho=rho0*a**(-3*(1+w)); H=hubble(a,rho0,w)
    Hdot=-.5*(1+w)*rho*(1+rho/6)
    return -a*Hdot/(1+H*H)**2

for rho,w,D in [(1,0,.5),(1,1/3,.5),(10,-.5,1),(10,0,1),(10,1/3,1)]:
    a=fast(rho,w,D);b=eval_model(rho,w,D)
    assert a is not None and a['advance']>0
    assert abs(a['advance']-b['advance'])<1e-8
    assert abs(a['null_residual'])<1e-10
    assert curvature(1,rho,w)>0
    print('PASS',rho,w,D,'advance',a['advance'],'independent delta',a['advance']-b['advance'])
for rho in [.1,1,10]:
    a=fast(rho,-1,.5)
    if a:assert abs(a['advance'])<1e-9
print('PASS de Sitter negative controls; analytic convexity sign')
