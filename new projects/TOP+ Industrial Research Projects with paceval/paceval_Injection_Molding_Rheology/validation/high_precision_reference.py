#!/usr/bin/env python3
"""Independent 90-digit interpretation of the exact binary numerical input values.
This computes a separate mathematical reference. It does not create primary paceval results.
"""
import csv,json,sys,math
from pathlib import Path
import mpmath as mp
mp.mp.dps=90
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
COL=['Q','T','rA','LA','rB','LB','K','n','E','Rg','Tref','etaZero','tauStar','MachineMax','CavityReq','ShearMax','Tmin','Tmax','Pheater','Theat','Pinject','Tinject','Emax']
checks=0; problems=[]; examples=[]
def m(x): return mp.mpf(float(x))
def read(name): return list(csv.DictReader((R/name).open(encoding='utf8')))
def vref(a):
    x={k:m(a[k]) for k in COL};q=x['Q'];t=x['T'];n=x['n'];
    pi=mp.pi; temp=mp.exp(x['E']/x['Rg']*(1/t-1/x['Tref']));cor=(3*n+1)/(4*n)
    gA=4*q/(pi*x['rA']**3);gB=4*q/(pi*x['rB']**3)
    def P(g,L,r,coef):return 2*x['K']*temp*L/r*(g*coef)**n
    p1=P(gA,x['LA'],x['rA'],1)+P(gB,x['LB'],x['rB'],1)
    p2=P(gA,x['LA'],x['rA'],cor)+P(gB,x['LB'],x['rB'],cor)
    margin1=x['MachineMax']-x['CavityReq']-p1
    margin2=x['MachineMax']-x['CavityReq']-p2
    shear1=x['ShearMax']-max(gA,gB)
    shear2=x['ShearMax']-max(gA,gB)*cor
    tm=min(t-x['Tmin'],x['Tmax']-t)
    energy=x['Pheater']*x['Theat']+x['Pinject']*x['Tinject']
    em=x['Emax']-energy
    def score(mar,shr):return min(mar/x['MachineMax'],shr/x['ShearMax'],tm/(x['Tmax']-x['Tmin']),em/x['Emax'])
    newton=8*x['K']*temp*q/pi*(x['LA']/x['rA']**4+x['LB']/x['rB']**4)
    return dict(pressure_v1_Pa=p1,pressure_v2_Pa=p2,margin_v1_Pa=margin1,margin_v2_Pa=margin2,score_v1=score(margin1,shear1),score_v2=score(margin2,shear2),guard_v1=int(margin1>=0 and shear1>=0 and tm>=0 and em>=0),guard_v2=int(margin2>=0 and shear2>=0 and tm>=0 and em>=0),newton_limit_Pa=newton)
def checkcase(case,got,expect,exact=False):
    global checks
    checks+=1
    if exact:
        if int(got)!=int(expect):problems.append(f'{case}: boolean {got} != {int(expect)}')
    else:
        lhs=mp.mpf(got);rhs=expect
        if not mp.isfinite(lhs) or abs(lhs-rhs)>mp.mpf('1e-8')+mp.mpf('2e-12')*abs(rhs):
            problems.append(f'{case}: result {got} inconsistent with independent reference')
def inputmap(name):return {r['case_id']:r for r in read(name)}
for datatype,iname,oname in [('grid','examples/synthetic_grid_inputs.csv','results/mcp_grid_observed.csv'),('edge','examples/synthetic_edge_inputs.csv','results/mcp_edge_observed.csv')]:
    inp=inputmap(iname)
    for out in read(oname):
        id=out['case_id']
        if id not in inp:problems.append(f'{id}: input missing');continue
        r=vref(inp[id]);
        for k,shown in out.items():
            if k in r:checkcase(f'{datatype}/{id}/{k}',shown,r[k],k.startswith('guard_'))
        if datatype=='edge' and inp[id]['n']=='1':
            checks+=1
            if abs(r['pressure_v1_Pa']-r['pressure_v2_Pa'])>mp.mpf('1e-65')*abs(r['pressure_v2_Pa']):problems.append(f'{id}: n=1 analytical equality')
        if id in ('G012','G020','G028','S004','S011'):
            examples.append({'case_id':id,'pressure_v1_MPa':float(r['pressure_v1_Pa']/1e6),'pressure_v2_MPa':float(r['pressure_v2_Pa']/1e6),'guard_v1':r['guard_v1'],'guard_v2':r['guard_v2']})
# Bound check on exact binary numerical inputs, no interval claim on a continuum.
tinc=json.loads((R/'results/tinc_point_samples.json').read_text(encoding='utf8'))
for item in tinc['scenarios']:
    row={k:str(v) for k,v in zip(COL,[item['Q'],item['T'],.0035,.12,.0027,.14,440,.48,18000,8.314,500,600,20000,13300000,10200000,2850,480,540,2500,5,3800,1.2,18500])}
    ref=vref(row)
    for k,refkey in [('pressure_v2','pressure_v2_Pa'),('margin_v2','margin_v2_Pa')]:
        checks+=1
        x=item[k]
        if not (mp.mpf(x['lo'])<=ref[refkey]<=mp.mpf(x['hi'])):problems.append(f"TINC {item['case']}/{k}: exact-binary point reference not enclosed by printed decimal bounds")
# Seven additional *observed* remote MCP rheology/sensitivity records at T=506 K.
for row in read('results/mcp_rheology_diagnostics.csv'):
    a={k:str(v) for k,v in zip(COL,[float(row['Q_m3s']),506,.0035,.12,.0027,.14,440,.48,18000,8.314,500,600,20000,13300000,10200000,2850,480,540,2500,5,3800,1.2,18500])}
    x={k:m(a[k]) for k in COL};tmp=mp.exp(x['E']/x['Rg']*(1/x['T']-1/x['Tref']));gA=4*x['Q']/(mp.pi*x['rA']**3);gB=4*x['Q']/(mp.pi*x['rB']**3)
    etaPower=x['K']*gA**(x['n']-1)*tmp
    e0=x['etaZero']*tmp
    cA=e0/(1+(e0*gA/x['tauStar'])**(1-x['n']))
    cB=e0/(1+(e0*gB/x['tauStar'])**(1-x['n']))
    p=vref(a)['pressure_v2_Pa']
    expected={'gammaA_s-1':gA,'etaPowerA_Pas':etaPower,'etaCrossA_Pas':cA,'etaCrossB_Pas':cB,'dP_dQ_v2_Pas_m3':x['n']*p/x['Q'],'dP_dT_v2_PaK':-x['E']/(x['Rg']*x['T']**2)*p,'dpCrossProxy_Pa':8*x['Q']/mp.pi*(cA*x['LA']/x['rA']**4+cB*x['LB']/x['rB']**4),'etaCrossPowerRatio_A':cA/etaPower}
    for k,ref in expected.items():checkcase(f'diagnostic/{row["Q_m3s"]}/{k}',row[k],ref)
res={'status':'PASS' if not problems else 'FAIL','precision_decimal_digits':90,'reference_checks':checks,'grid_rows':len(read('results/mcp_grid_observed.csv')),'edge_rows':len(read('results/mcp_edge_observed.csv')),'tinc_point_tests':10,'failure_count':len(problems),'failures':problems,'selected_case_reference':examples,'tolerance':'abs <= 1e-8 + 2e-12*abs(reference), boolean exact; TINC strict decimal inclusion'}
(R/'results/high_precision_validation.json').write_text(json.dumps(res,indent=2),encoding='utf8')
print('High precision audit:',res['status'],'checks',checks,'failures',len(problems))
for p in problems[:15]:print('FAIL',p)
if problems:sys.exit(1)
