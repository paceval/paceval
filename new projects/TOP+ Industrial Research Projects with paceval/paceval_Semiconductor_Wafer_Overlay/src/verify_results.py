#!/usr/bin/env python3
"""Independent formula, complete-output and 80-digit numerical audit.

No paceval library or C++ implementation is imported. The reference uses the
published fitted coefficient CSV and independently reconstructs each basis.
"""
import argparse,csv,json,math,collections
from pathlib import Path
import numpy as np
import mpmath as mp

NAMES=['overlayDx','overlayDy','residualX','residualY','residualNorm','waferMargin','residualMargin','riskScore','accept','review','reject','dDx_dU','dDx_dV','dDy_dU','dDy_dV','illustrativeUncertainty','clampedResidual','fieldSlot']
def rows(path):
    with open(path,newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def coeffs(path):
    c=collections.defaultdict(dict)
    for r in rows(path):c[(int(r['lotId']),r['version'])].setdefault(r['axis'],[]).append(float(r['coefficient']))
    return c

def basis(u,v,t):
    t=(t-25)/20
    return [1,u,v,u*u,u*v,v*v,t,t*u,t*v,u**3,u*u*v,u*v*v,v**3,
            math.sin(math.pi*u)*math.cos(math.pi*v),math.sin(math.pi*v)*math.cos(math.pi*u)]
def derivative(u,v,t,axis):
    t=(t-25)/20
    if axis=='u':return [0,1,0,2*u,v,0,0,t,0,3*u*u,2*u*v,v*v,0,
                          math.pi*math.cos(math.pi*u)*math.cos(math.pi*v),-math.pi*math.sin(math.pi*v)*math.sin(math.pi*u)]
    return [0,0,1,0,u,2*v,0,0,t,0,u*u,2*u*v,3*v*v,
            -math.pi*math.sin(math.pi*u)*math.sin(math.pi*v), math.pi*math.cos(math.pi*v)*math.cos(math.pi*u)]

def eval_model(r,c):
    u=float(r['xMm'])/150.;v=float(r['yMm'])/150.;t=float(r['tempC']);xm=float(r['observedDxNm']);ym=float(r['observedDyNm']);sig=.42
    b=basis(u,v,t)
    dot=lambda x,y:sum(a*z for a,z in zip(x,y))
    x=dot(c['dx'],b);y=dot(c['dy'],b)
    rx=xm-x;ry=ym-y;res=math.hypot(rx,ry);margin=1-u*u-v*v
    du=derivative(u,v,t,'u');dv=derivative(u,v,t,'v')
    j=[dot(c['dx'],du),dot(c['dx'],dv),dot(c['dy'],du),dot(c['dy'],dv)]
    unc=math.sqrt(sig**2+(0.00015**2)*sum(a*a for a in j))
    accept=int(margin>=0 and res<=2*sig)
    review=int(margin>=0 and 2*sig<res<=3.5*sig)
    reject=int(margin<0 or res>3.5*sig)
    return [x,y,rx,ry,res,margin,3.5*sig-res,(res/sig)**2+0.06*((t-25)/20)**2,accept,review,reject,
            *j,unc,max(0,min(res,3.5*sig)),int(r['siteId'])%16]

def high_precision(r,c):
    mp.mp.dps=80
    mm=lambda value:mp.mpf(str(value))
    u=mm(r['xMm'])/150;v=mm(r['yMm'])/150;t=mm(r['tempC']);xm=mm(r['observedDxNm']);ym=mm(r['observedDyNm']);sig=mp.mpf('0.42');tau=(t-25)/20
    b=[1,u,v,u*u,u*v,v*v,tau,tau*u,tau*v,u*u*u,u*u*v,u*v*v,v*v*v,
       mp.sin(mp.pi*u)*mp.cos(mp.pi*v),mp.sin(mp.pi*v)*mp.cos(mp.pi*u)]
    calc=lambda cc:sum(mm(val)*basisval for val,basisval in zip(cc,b))
    x=calc(c['dx']);y=calc(c['dy']);res=mp.sqrt((xm-x)**2+(ym-y)**2)
    return x,y,res,mp.mpf('3.5')*sig-res

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',default=str(Path(__file__).resolve().parent.parent));p.add_argument('--results');p.add_argument('--small',action='store_true');args=p.parse_args()
    root=Path(args.project);base=Path(args.results) if args.results else root/'results';cc=coeffs(base/'fitted_coefficients.csv')
    sample=rows(base/'wafer_grid_sample.csv');held=rows(base/'holdout_results.csv');total=0;max_err=0.;booleans=0;types=collections.Counter()
    for kind,records in [('grid',sample),('holdout',held)]:
        for r in records:
            key=(int(r['lotId']),r['version']);expect=eval_model(r,cc[key]);types[kind]+=1
            for k,name in enumerate(NAMES):
                got=float(r[name]);err=abs(got-expect[k]);
                if name in ('accept','review','reject','fieldSlot'):
                    if got!=expect[k]:raise AssertionError(f'{key} {r["siteId"]}: {name} got={got} ref={expect[k]}')
                    booleans+=1
                elif err>1e-9+1e-11*abs(expect[k]):raise AssertionError(f'{key} {r["siteId"]}: {name}: {got} versus {expect[k]}')
                max_err=max(max_err,err);total+=1
    # Independent coefficient fit using LAPACK lstsq; host Householder is not reused.
    train=rows(root/'examples'/'synthetic_metrology.csv');fit_checks=0;fit_max=0
    for key,c in cc.items():
        lot,v=key;data=[r for r in train if int(r['lotId'])==lot and int(r['isHoldout'])==0]
        a=np.array([basis(float(r['xMm'])/150,float(r['yMm'])/150,float(r['tempC']))[:len(c['dx'])] for r in data]);
        for axis,field in [('dx','dxObservedNm'),('dy','dyObservedNm')]:
            sol=np.linalg.lstsq(a,np.array([float(r[field]) for r in data]),rcond=None)[0]
            diff=np.max(abs(sol-np.array(c[axis])));fit_max=max(fit_max,float(diff))
            if diff>1e-6:raise AssertionError(f'Host QR coefficient mismatch {key} {axis}: {diff}')
            fit_checks+=len(sol)
    # High precision checks use the exact published decimal coefficients + inputs.
    mp.mp.dps=80;hp=0;hp_max=0.
    for idx,r in enumerate(sample):
        if idx % (16 if args.small else 5):continue
        c=cc[(int(r['lotId']),r['version'])]
        vals=high_precision(r,c)
        for field,expected in zip(['overlayDx','overlayDy','residualNorm','residualMargin'],vals):
            got=mp.mpf(r[field]);err=float(abs(got-expected));hp_max=max(hp_max,err)
            if err>1e-9+1e-11*abs(float(expected)):raise AssertionError(f'High precision mismatch {field}: {err}')
            hp+=1
    summary=rows(base/'wafer_summary.csv')
    for r in summary:
        if int(r['rows']) != (128 if args.small else 10000) and not args.small:
            raise AssertionError('Expected 10,000 rows per lot-version in published run')
        if sum(int(r[x]) for x in ('accept','review','reject'))!=int(r['rows']):raise AssertionError('Invalid categorical tally')
    audit={'status':'PASS','paceval_sample_cells_independently_checked':total,
           'categorical_exact_checks':booleans,'high_precision_80_digit_cells':hp,
           'independent_lapack_fitted_coefficients_checked':fit_checks,
           'technical_max_abs_formula_difference':max_err,'technical_max_abs_high_precision_difference':hp_max,
           'technical_max_abs_coefficient_difference':fit_max,
           'grid_sample_rows':types['grid'],'holdout_rows':types['holdout'],
           'disclosure':'Detailed numeric differences are engineering audit data, not published performance or precision claims.'}
    base.mkdir(parents=True,exist_ok=True)
    with open(base/'independent_numerical_audit.json','w') as f:json.dump(audit,f,indent=2)
    print('PASS',json.dumps({k:v for k,v in audit.items() if 'difference' not in k},indent=2))
if __name__=='__main__':main()
