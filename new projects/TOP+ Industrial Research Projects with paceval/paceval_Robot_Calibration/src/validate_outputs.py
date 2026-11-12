#!/usr/bin/env python3
"""Independent high-precision and observability audit for the six-axis demo.

Uses mpmath for 100-decimal-place forward kinematics and NumPy for SVD.
No paceval or C++ library is imported here. Inputs are converted from the
actually supplied binary64 values, not treated as exact decimal strings.
"""
import argparse, csv, json, math
from pathlib import Path
import numpy as np
import mpmath as mp
mp.mp.dps=100

LINK=(.45,.53,.42,.16,.27,.14)

def read_csv(path):
    with open(path, newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def m(v):return mp.mpf(float(v))

def reference(q,theta):
    lens=[m(x) for x in LINK]
    for idx,k in ((6,1),(7,2),(8,5)):lens[k]+=m(theta[idx])
    r=mp.eye(3);p=mp.matrix([0,0,0])
    for k,axis in enumerate('ZYYXYZ'):
        t=m(q[k])+m(theta[k]);c=mp.cos(t);s=mp.sin(t)
        if axis=='Z':rot=mp.matrix([[c,-s,0],[s,c,0],[0,0,1]])
        elif axis=='Y':rot=mp.matrix([[c,0,s],[0,1,0],[-s,0,c]])
        else:rot=mp.matrix([[1,0,0],[0,c,-s],[0,s,c]])
        r=r*rot
        v=mp.matrix([0,0,lens[k]]) if k in (0,3) else mp.matrix([lens[k],0,0])
        p+=r*v
    return p

def audit(root):
    train=read_csv(root/'training_observations.csv');hold=read_csv(root/'holdout_observations.csv')
    params=read_csv(root/'parameters.csv')
    fitted=[float(row['fitted']) for row in params]
    true=[float(row['true']) for row in params]
    nominal=[0.0]*9
    summary=json.loads((root/'summary.json').read_text())
    errs=[];checks=0
    for split,records in [('train',train),('holdout',hold)]:
        predictions=read_csv(root/(split+'_predictions.csv'))
        assert len(predictions)==len(records), 'Prediction data length mismatch'
        for row,pred in zip(records,predictions):
            assert row['id']==pred['id'] and row['split']==pred['split'], 'Dataset row mismatch'
            q=[float(row[f'q{i}']) for i in range(1,7)]
            meas=[m(row['m'+k+'_m']) for k in 'xyz']
            for prefix,theta in (('nominal',nominal),('fitted',fitted)):
                p=reference(q,theta)
                for k in range(3):
                    got=m(pred[f'{prefix}_r{"xyz"[k]}'])
                    exact=meas[k]-p[k]
                    error=abs(got-exact)
                    limit=mp.mpf('3e-12')+mp.mpf('5e-12')*abs(exact)
                    assert error<=limit, (split,row['id'],prefix,k,str(error))
                    errs.append(float(error));checks+=1
    assert checks==(len(train)+len(hold))*6
    # Independent SVD of the training and deliberately identical-pose sets.
    svs={}
    for label,data in [('training',train),('degenerate',read_csv(root/'degenerate_observations.csv'))]:
        J=np.zeros((3*len(data),9))
        for j in range(9):
            plus=np.zeros(9);minus=np.zeros(9);step=1e-5 if j<6 else 2e-5
            plus[j]=step;minus[j]=-step
            for i,row in enumerate(data):
                q=[float(row[f'q{k}']) for k in range(1,7)]
                fp=reference(q,plus);fm=reference(q,minus)
                for d in range(3): J[3*i+d,j]=float((fp[d]-fm[d])/(2*step))
        svs[label]=list(map(float,np.linalg.svd(J,compute_uv=False)))
    assert svs['training'][-1]>0.05,'Training design is not full rank'
    assert svs['degenerate'][-1]<1e-6,'Degenerate pose set should be rank-deficient'
    assert abs(svs['training'][-1]-summary['train_singular_min'])<2e-4
    assert summary['holdout_rmse_after_m']<.2*summary['holdout_rmse_before_m']
    assert max(abs(a-b) for a,b in zip(fitted,true))<1e-4
    # Independent precision-100 inclusion check using the input as binary64.
    tinc=read_csv(root/'tinc_samples.csv');count=0;miss=[]
    for row in tinc:
        exact=m(row['l2_m'])*mp.cos(m(row['q2_rad'])+m(row['o2_rad']))
        low=m(row['lower_m']);high=m(row['upper_m'])
        if not low<=exact<=high:miss.append(row['id'])
        else:count+=1
    assert not miss,f'TINC raw intervals missed reference at ids {miss}'
    report={
        'status':'passed',
        'reference_precision_decimal_digits':mp.mp.dps,
        'coordinate_residual_comparisons':checks,
        'max_absolute_coordinate_residual_difference_m':max(errs),
        'raw_TINC_inclusions':count,
        'raw_TINC_total':len(tinc),
        'holdout_rmse_nominal_mm':1000*summary['holdout_rmse_before_m'],
        'holdout_rmse_calibrated_mm':1000*summary['holdout_rmse_after_m'],
        'training_singular_value_min':svs['training'][-1],
        'degenerate_singular_value_min':svs['degenerate'][-1],
        'maximum_parameter_error':max(abs(a-b) for a,b in zip(fitted,true)),
        'note':'TINC inclusions apply only to the specific tested smooth subexpression and binary64 sample values.'}
    (root/'high_precision_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--examples',type=Path,required=True)
    args=ap.parse_args();audit(args.examples)
