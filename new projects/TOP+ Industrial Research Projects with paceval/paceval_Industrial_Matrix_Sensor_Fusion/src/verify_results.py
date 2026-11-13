#!/usr/bin/env python3
"""Independent numerical audit. Never used to generate productive paceval results."""
import csv, json, math, sys
from pathlib import Path
import numpy as np
from mpmath import mp

ROOT = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
R = ROOT/'results'
mp.dps=80

def matrix_a(n,version=0):
    l=np.zeros((n,n),dtype=float)
    for i in range(n):
        for j in range(i+1):
            l[i,j]=(1.13+0.003*(i%9)+.004*version) if i==j else (.0017*math.sin((i+1)*(j+1)*.017)+.0012*math.cos((i+3)*(j+2)*.021))
    return l@l.T

def aclose(x,y,threshold=5e-10,label=''):
    difference=float(np.max(np.abs(np.asarray(x)-np.asarray(y))))
    if not np.isfinite(difference) or difference>threshold:
        raise AssertionError(f'{label}: max absolute error {difference:.17g} > {threshold:.17g}')
    return difference

report={'matrix_checks':{},'sensor_cases_checked':0,'high_precision_values_checked':0,'scientific_limitations':['synthetic models','well conditioned dense SPD inputs','no certified physical measurement or real-time claim']}
for n in (128,512):
    p=R/f'matrix_{n}_'
    summary=json.loads((R/f'matrix_{n}_summary.json').read_text())
    aa=np.fromfile(str(p)+'original.f64',dtype='<f8').reshape((n,n))
    L=np.fromfile(str(p)+'cholesky.f64',dtype='<f8').reshape((n,n))
    inv=np.fromfile(str(p)+'inverse.f64',dtype='<f8').reshape((n,n))
    # Independently reconstruct and analyze the full original matrix.
    check_source=aclose(aa,matrix_a(n),1e-12,label=f'input matrix {n}')
    chol_ref=np.linalg.cholesky(aa)
    inv_ref=np.linalg.inv(aa)
    factor_check=aclose(L,chol_ref,2e-11,label=f'Cholesky {n}')
    inverse_check=aclose(inv,inv_ref,2e-11,label=f'full inverse {n}')
    residual_check=aclose(aa@inv,np.eye(n),2e-11,label=f'residual {n}')
    reconstruction=aclose(L@L.T,aa,2e-11,label=f'reconstruction {n}')
    sym_check=aclose(inv,inv.T,1e-13,label=f'symmetry {n}')
    sign,logdet=np.linalg.slogdet(aa)
    assert sign>0
    assert abs(float(logdet)-summary['log_determinant'])<2e-10
    assert summary['real_paceval_graphs']>=16
    report['matrix_checks'][str(n)]={'validated_entries':int(n*n),'matrix_input_check':check_source,'max_abs_factor_difference':factor_check,'max_abs_inverse_difference':inverse_check,'inverse_residual':residual_check,'cholesky_residual':reconstruction,'inverse_symmetry':sym_check,'paceval_graph_outputs':summary['graph_outputs'],'log_determinant':summary['log_determinant'],'positive_definite':True}
    print(f'OK full n={n}: {n*n} inverse entries, full Cholesky and determinant independently checked')

rows=list(csv.DictReader((R/'sensor_fusion.csv').open()))
assert len(rows)==32
for row in rows:
    n=6;s=int(row['scenario']);v=int(row['model_version'])-1
    P1=matrix_a(n,v)*(0.02+.002*(s%3))
    P2=matrix_a(n,1-v)*(0.025+.002*(s%4))
    i1=np.linalg.inv(P1);i2=np.linalg.inv(P2)
    covariance=np.linalg.inv(i1+i2)
    shift=.78 if s>=12 else (.37 if s>=8 else .018)
    m1=np.array([.10*i+.03*math.sin((s+1)*(i+1)*.17) for i in range(n)])
    m2=np.array([m1[i]+shift*(1+.12*i)*math.cos(.7*i+.03*s) for i in range(n)])
    fused=covariance@(i1@m1+i2@m2)
    d=m1-m2
    d2=float(d@np.linalg.solve(P1+P2,d))
    radius=float(np.sqrt(np.trace(covariance)))
    bias=float(np.linalg.norm(d))
    temp=18+4*(s%8)
    if v==0:
        score=d2+.06*((temp-25)/25)**2+.12*radius+.30*abs(bias)
        derivative=.12*(temp-25)/625
    else:
        score=d2+.09*((temp-25)/25)**2+.18*radius+.18*abs(bias)
        derivative=.18*(temp-25)/625
    guard=12.592-score
    decision='ACCEPT' if guard>=0 else ('REVIEW' if guard>=-8 else 'REJECT')
    aclose(float(row['mahalanobis_squared']),d2,4e-10,label='Mahalanobis')
    aclose(float(row['quality_score']),score,4e-10,label='score')
    aclose(float(row['quality_guard']),guard,4e-10,label='guard')
    aclose(float(row['temperature_sensitivity']),derivative,3e-12,label='sensitivity')
    aclose(float(row['uncertainty_radius']),radius,3e-12,label='radius')
    aclose(float(row['relative_sensor_bias']),bias,3e-12,label='sensor bias')
    aclose([float(row['fused_'+str(i)]) for i in range(n)],fused,4e-10,label='fused state')
    aclose([float(row['cov_diag_'+str(i)]) for i in range(n)],np.diag(covariance),4e-10,label='fused covariance diagonal')
    aclose(float(row['cov_01']),float(covariance[0,1]),4e-10,label='off diagonal')
    assert row['decision']==decision
    report['sensor_cases_checked']+=1
print('OK full independent sensor fusion scenarios:',len(rows))

surface=list(csv.DictReader((R/'quality_score_surface.csv').open()))
assert len(surface)==625
for r in surface:
    d2=float(r['mahalanobis_squared']);temp=float(r['temperature_c'])
    s1=d2+.06*((temp-25)/25)**2+.12*.32+.30*abs(.2)
    s2=d2+.09*((temp-25)/25)**2+.18*.32+.18*abs(.2)
    for name,value in [('model_v1_score',s1),('model_v2_score',s2),('model_v1_guard',12.592-s1),('model_v2_guard',12.592-s2),('model_v1_temp_sensitivity',.12*(temp-25)/625),('model_v2_temp_sensitivity',.18*(temp-25)/625)]:
        aclose(float(r[name]),value,2e-11,label='surface '+name)
report['surface_points_checked']=625
print('OK 625 actual graph surface points')

# Independent 80-digit high-precision check for synthetic sensor covariance.
# Rounds the source matrix entries to the actual IEEE-754 doubles before converting to mpmath.
for row in rows:
    if int(row['scenario']) not in (0,7,10,14):continue
    s=int(row['scenario']);v=int(row['model_version'])-1;n=6
    P1=matrix_a(n,v)*(0.02+.002*(s%3));P2=matrix_a(n,1-v)*(0.025+.002*(s%4))
    a1=mp.matrix([[mp.mpf(float(x)) for x in rr] for rr in P1]);a2=mp.matrix([[mp.mpf(float(x)) for x in rr] for rr in P2]);ip1=a1**-1;ip2=a2**-1
    shift=.78 if s>=12 else (.37 if s>=8 else .018)
    m1=[mp.mpf(float(.10*i+.03*math.sin((s+1)*(i+1)*.17))) for i in range(n)]
    m2=[mp.mpf(float(float(m1[i])+shift*(1+.12*i)*math.cos(.7*i+.03*s))) for i in range(n)]
    out=(ip1+ip2)**-1*(ip1*mp.matrix(m1)+ip2*mp.matrix(m2));
    d=mp.matrix([m1[i]-m2[i] for i in range(n)]);md2=(d.T*(a1+a2)**-1*d)[0]
    assert abs(md2-mp.mpf(row['mahalanobis_squared']))<mp.mpf('1e-9')
    report['high_precision_values_checked']+=1
    for i in range(n):
        assert abs(out[i]-mp.mpf(row['fused_'+str(i)]))<mp.mpf('1e-9')
        report['high_precision_values_checked']+=1
print('OK mpmath 80-digit independent checks:',report['high_precision_values_checked'])
(R/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS all independent numerical validations')
