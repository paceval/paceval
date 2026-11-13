#!/usr/bin/env python3
"""Independent numerical audit: original SDK outputs vs native FV trajectory and
80-digit independently coded physical and analytical graph equations.
The code never calls paceval; it operates on the serialized output data.
"""
import argparse, csv, json, math, re
from pathlib import Path
from collections import defaultdict
import mpmath as mp
import numpy as np
mp.mp.dps=80

def reader(p):
    with open(p,newline='',encoding='utf8') as f:return list(csv.DictReader(f))

def validclose(a,b,tol=1e-9):return abs(float(a)-float(b))<=tol*(1+abs(float(b)))

def oracle(g,d):
    # The physics below is deliberately formulated independently of the SDK
    # formula strings; all values are exact binary64 inputs promoted to mpf.
    z={k:mp.mpf(float(d[k])) for k in 'A AL AR B BL BR C CL CR u D dx dt kf kr K lc rc Ain Bin Cin L target'.split()}
    A,AL,AR,B,BL,BR,C,CL,CR=[z[k] for k in 'A AL AR B BL BR C CL CR'.split()]
    u,D,dx,dt,kf,kr,K,lc,rc=[z[k] for k in 'u D dx dt kf kr K lc rc'.split()]
    Ain,Bin,Cin,L,target=[z[k] for k in 'Ain Bin Cin L target'.split()]
    ver=int(re.search(r'_v([12])',g).group(1)) if re.search(r'_v([12])',g) else 1
    rate0=kf*A*B-kr*C
    forward=kf*A*B if ver==1 else kf*A*B/(1+K*A)
    r=forward-kr*C
    def transfer(left,cent,right):
        incoming=u*left-D*lc*(cent-left)/dx
        outgoing=u*cent-D*rc*(right-cent)/dx
        return (incoming-outgoing)/dx
    ta,tb,tc=transfer(AL,A,AR),transfer(BL,B,BR),transfer(CL,C,CR)
    if g=='reaction_rate_v2_minus_v1':return kf*A*B/(1+K*A)-kf*A*B
    if g.startswith('reaction_rate_v'): return r
    if g.startswith('forward_rate_v'):return forward
    if g.startswith('reverse_rate_v'):return kr*C
    if g.startswith('transport_A_v'):return ta
    if g.startswith('transport_B_v'):return tb
    if g.startswith('transport_C_v'):return tc
    if g.startswith('A_next_v'):return A+dt*(ta-r)
    if g.startswith('B_next_v'):return B+dt*(tb-r)
    if g.startswith('C_next_v'):return C+dt*(tc+r)
    if g.startswith('d_rate_dA_v'):return kf*B if ver==1 else kf*B/(1+K*A)**2
    if g.startswith('d_rate_dB_v'):return kf*A if ver==1 else kf*A/(1+K*A)
    if g.startswith('d_rate_dC_v'):return -kr
    if g.startswith('d_rate_dkf_v'):return A*B if ver==1 else A*B/(1+K*A)
    if g.startswith('d_rate_dK_v'):return mp.mpf(0) if ver==1 else -kf*A*A*B/(1+K*A)**2
    if g.startswith('mole_sum_A_C_v'):return A+C
    if g.startswith('mole_sum_B_C_v'):return B+C
    if g.startswith('influx_A_C_v'):return u*(Ain+Cin)-2*D*((A-Ain)+(C-Cin))/dx
    if g.startswith('influx_B_C_v'):return u*(Bin+Cin)-2*D*((B-Bin)+(C-Cin))/dx
    if g.startswith('outflux_A_C_v'):return u*(A+C)
    if g.startswith('outflux_B_C_v'):return u*(B+C)
    if g.startswith('outlet_reacted_fraction_v'):return C/(A+C+mp.mpf('.000000000001'))
    if g.startswith('outlet_product_ratio_v'):return C/Ain
    if g.startswith('outlet_molar_flux_C_v'):return u*C
    if g.startswith('target_product_margin_v'):return C-target
    if g.startswith('reacted_fraction_margin_v'):return C/(A+C+mp.mpf('.000000000001'))-mp.mpf('.25')
    if g.startswith('local_rate_guard_v'):return rate0
    if g.startswith('modified_rate_minus_original_v'):return r-rate0
    if g.startswith('score_v'):
        j=int(g.rsplit('_',1)[-1]); w=mp.mpf('.015')+mp.mpf('.014')*j;v1=mp.mpf('.5')+mp.mpf('.035')*(j%5);v2=mp.mpf('.18')+mp.mpf('.012')*(j%4)
        return v1*(C-target)**2+w*((u-mp.mpf('.40'))/mp.mpf('.40'))**2+v2*(1-A/Ain-C/Ain)**2
    if g=='peclet_channel':return u*L/D
    if g=='damkohler_nominal':return kf*Bin*L/u
    if g=='flow_residence_time':return L/u
    if g=='reaction_rate_v2_minus_v1':return kf*A*B/(1+K*A)-kf*A*B
    raise ValueError('Unknown graph in independent verification: '+g)

def independent_path(row,cells,steps):
    u=float(row['velocity_mm_per_s']);kf=float(row['forward_k_L_per_mmol_s']);kr=float(row['reverse_k_per_s']);ksat=float(row['saturation_K_L_per_mmol']);v=int(row['model_version']);dt=.1;L=20.;dx=L/cells;D=.006
    A=np.zeros(cells);B=np.zeros(cells);C=np.zeros(cells)
    def transport(x,cin):
        left=np.empty_like(x);left[0]=cin;left[1:]=x[:-1]
        right=np.empty_like(x);right[:-1]=x[1:];right[-1]=x[-1]
        lc=np.ones(cells);lc[0]=2
        rc=np.ones(cells);rc[-1]=0
        return (u*(left-x)+(D/dx)*(rc*(right-x)-lc*(x-left)))/dx
    for _ in range(steps):
        r=kf*A*B/(1+ksat*A if v==2 else 1)-kr*C
        na=A+dt*(transport(A,1.)-r)
        nb=B+dt*(transport(B,.9)-r)
        nc=C+dt*(transport(C,0.)+r)
        A,B,C=na,nb,nc
    return A,B,C

def main(root):
    p=root/'results';exe=(p/'sdk_execution.txt').read_text(); info={a:b for a,b in (line.split('=',1) for line in exe.splitlines() if '=' in line)}
    steps=int(info['steps']);cells=int(info['cells']);probe=reader(p/'graph_probe.csv');registry=reader(p/'formula_registry.csv');summ=reader(p/'scenario_summary.csv');sc=reader(root/'examples/synthetic_operating_scenarios.csv');bal=reader(p/'mass_balance.csv');prof=reader(p/'concentration_profiles.csv')
    assert len(registry)==int(info['registered_executed_graphs']) and len({q['graph_id'] for q in registry})==len(registry)
    assert {q['graph_id'] for q in registry}=={q['graph_id'] for q in probe}
    assert len(summ)==len(sc)==int(info['scenarios'])
    worst=0;hp=0
    for q in probe:
        result=float(q['paceval_result']);reference=float(oracle(q['graph_id'],q));error=abs(result-reference)/(1+abs(reference));worst=max(worst,error);hp+=1
        if not math.isfinite(result) or error>1e-9:raise RuntimeError(f"80-digit oracle mismatch for {q['graph_id']} {error}")
    maxtraj=0;numberTraj=0;last={}
    for q in prof:
        if math.isclose(float(q['time_s']),steps*.1,rel_tol=0,abs_tol=1e-10):last[(int(q['scenario_id']),round(float(q['x_mm']),8))]=q
    for r in sc:
        sid=int(r['scenario_id']);a,b,c=independent_path(r,cells,steps);s=next(x for x in summ if int(x['scenario_id'])==sid)
        for value,ref in ((s['A_out_mmol_per_L'],a[-1]),(s['B_out_mmol_per_L'],b[-1]),(s['C_out_mmol_per_L'],c[-1]),(s['outlet_stoichiometric_reacted_fraction'],c[-1]/(a[-1]+c[-1]+1e-12)),(s['outlet_C_to_A_inlet_ratio'],c[-1]),(s['product_outlet_flux'],float(r['velocity_mm_per_s'])*c[-1])):
            er=abs(float(value)-ref)/(1+abs(ref));maxtraj=max(maxtraj,er);numberTraj+=1
            if er>3e-10:raise RuntimeError(f'Full independent reaction-transport trajectory mismatch case {sid} err={er}')
        for i in (0,cells//4,cells//2,cells-1):
            q=last[(sid,round((i+.5)*20./cells,8))]
            for m,value in [('A_mmol_per_L',a[i]),('B_mmol_per_L',b[i]),('C_mmol_per_L',c[i])]:
                er=abs(float(q[m])-value)/(1+abs(value));maxtraj=max(maxtraj,er);numberTraj+=1
                if er>3e-10:raise RuntimeError(f'Independent concentration profile mismatch {sid} index {i} {m} err={er}')
    maxbal=max(max(abs(float(q['balance_residual_AplusC'])),abs(float(q['balance_residual_BplusC']))) for q in bal)
    assert maxbal<2e-8
    assert all(float(q['A_out_mmol_per_L'])>=0 and float(q['B_out_mmol_per_L'])>=0 and float(q['C_out_mmol_per_L'])>=0 for q in summ)
    out={'status':'PASS','high_precision_decimal_digits':80,'high_precision_graph_samples':hp,'verified_graph_ids':len(registry),'native_independent_trajectory_fields':numberTraj,'max_scaled_high_precision_difference_technical_audit_only':worst,'max_scaled_trajectory_difference_technical_audit_only':maxtraj,'max_absolute_molar_balance_residual_technical_audit_only':maxbal,'scenario_count':len(sc),'time_steps':steps,'grid_cells':cells,'scientific_scope':'synthetic isothermal cross-section-averaged 1D reactor; no CFD validation'}
    (p/'high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print('WP047 INDEPENDENT VALIDATION PASS: graphs=',len(registry),'80_digit_oracle=',hp,'trajectory_values=',numberTraj,'mass_closure=',maxbal)
    return out
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);args=ap.parse_args();main(args.root)
