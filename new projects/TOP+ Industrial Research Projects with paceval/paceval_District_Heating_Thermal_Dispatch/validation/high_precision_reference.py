#!/usr/bin/env python3
"""Independent 90-digit reference checks of the RECORDED remote paceval data.
Uses explicit physical equations, not the serialized paceval formula manifest.
The reference is used solely for audit, never to generate publication curves.
"""
from pathlib import Path
import csv, json, sys
import mpmath as mp
mp.mp.dps=90
R=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])

def num(x):return mp.mpf(str(x))
def ok(ref,record,context,checks):
    a=num(record)
    # Reconstructed decimal columns are rounded to 12-14 significant digits.
    tol=mp.mpf('5e-10')*(1+abs(ref))
    diff=abs(a-ref)
    checks.append({'context':context,'difference':mp.nstr(diff,18),'tolerance':mp.nstr(tol,18),'pass':bool(diff<=tol)})
    if diff>tol:raise AssertionError(f'{context}: remote decimal value not consistent with independent formula')
def pipe_exact(tin,amb,UA,m,cp):return amb+(tin-amb)*mp.exp(-UA/(m*cp))
def pipe_mid(tin,amb,UA,m,cp):
    h=UA/(m*cp)
    return tin-(tin-amb)*h/(1+h/2)
def press(m,f,L,D,rho):
    velocity=4*m/(rho*mp.pi*D**2)
    return f*L/D*rho*velocity**2/2
checks=[]
edge_inputs={r['case_id']:r for r in csv.DictReader((R/'examples/synthetic_edge_grid.csv').open())}
edge_out=list(csv.DictReader((R/'results/mcp_edge_observed.csv').open()))
assert len(edge_inputs)==len(edge_out)==49
for row in edge_out:
    e=edge_inputs[row['case_id']]
    m,cp,T,amb,UA,tr,Tmin,f,L,D,rho,eta,dpmax,qreq=[num(e[k]) for k in ['m','cp','Tin','Tamb','UA','Tr','Tmin','f','L','D','rho','eta','dpmax','Qreq']]
    t2=pipe_exact(T,amb,UA,m,cp); t1=pipe_mid(T,amb,UA,m,cp)
    loss=m*cp*(T-t2)
    frac=loss/(m*cp*(T-tr))
    expected={'outlet_v1_C':t1,'outlet_v2_C':t2,'heat_loss_v2_W':loss,'temp_margin_v2_K':t2-Tmin,'loss_fraction_v2':frac}
    for field,reference in expected.items():ok(reference,row[field],row['case_id']+':'+field,checks)

net_inputs={r['scenario_id']:r for r in csv.DictReader((R/'examples/synthetic_network_dispatch.csv').open())}
net_out=list(csv.DictReader((R/'results/mcp_network_observed.csv').open()))
assert len(net_inputs)==len(net_out)==25
accept1=accept2=0
for row in net_out:
    n=net_inputs[row['scenario_id']];a={k:num(v) for k,v in n.items() if k!='scenario_id'}
    mt=a['mA']+a['mB']
    path_head=press(mt,a['fT'],a['LT'],a['DT'],a['rho'])+max(
        press(a['mA'],a['fA'],a['LA'],a['DA'],a['rho']),press(a['mB'],a['fB'],a['LB'],a['DB'],a['rho']))
    pump=mt/a['rho']*path_head/a['eta']
    def model(out):
        trunk=out(a['Ts'],a['Tamb'],a['UAt'],mt,a['cp'])
        branch_a=out(trunk,a['Tamb'],a['UAa'],a['mA'],a['cp'])
        branch_b=out(trunk,a['Tamb'],a['UAb'],a['mB'],a['cp'])
        delivery=(a['mA']*(branch_a-a['Tr'])+a['mB']*(branch_b-a['Tr']))*a['cp']
        source=mt*a['cp']*(a['Ts']-a['Tr'])
        loss=source-delivery
        tmin=min(branch_a,branch_b)
        accepted=int(tmin>=a['Tmin'] and delivery>=a['Demand'] and pump<=a['Pmax'])
        return trunk,branch_a,branch_b,delivery,loss,tmin,accepted
    v1=model(pipe_mid);v2=model(pipe_exact)
    expected={'branchA_v2_C':v2[1],'branchB_v2_C':v2[2],
       'delivered_v1_kW':v1[3]/1000,'delivered_v2_kW':v2[3]/1000,
       'loss_v2_kW':v2[4]/1000,'pump_W':pump,
       'temp_margin_v1_K':v1[5]-a['Tmin'],'temp_margin_v2_K':v2[5]-a['Tmin'],
       'demand_margin_v2_kW':(v2[3]-a['Demand'])/1000,
       'loss_fraction_v2':v2[4]/(mt*a['cp']*(a['Ts']-a['Tr'])),
       'delivered_delta_W':v2[3]-v1[3]}
    sc=min(v2[5]-a['Tmin'],(v2[3]-a['Demand'])/(mt*a['cp']),(a['Pmax']-pump)/2000)
    expected['dispatch_score_K']=sc
    for field,reference in expected.items():ok(reference,row[field],row['scenario_id']+':'+field,checks)
    for version,index in [(1,6),(2,6)]:
        name='guard_v'+str(version)
        assert int(row[name])==(v1 if version==1 else v2)[index],row['scenario_id']+':'+name
    assert abs(float(v2[3]+v2[4]-mt*a['cp']*(a['Ts']-a['Tr'])))<1e-7
    accept1+=v1[6];accept2+=v2[6]
assert accept1==accept2==15
# Boundary case is an expressly artificial narrow threshold for version semantics.
a={k:num(v) for k,v in net_inputs['N0101'].items() if k!='scenario_id'}
a['Tmin']=num('67.777')
mt=a['mA']+a['mB']
def bd(model):
    t=model(a['Ts'],a['Tamb'],a['UAt'],mt,a['cp'])
    ta=model(t,a['Tamb'],a['UAa'],a['mA'],a['cp'])
    tb=model(t,a['Tamb'],a['UAb'],a['mB'],a['cp'])
    return min(ta,tb)-a['Tmin']
B=json.loads((R/'results/boundary_case.json').read_text())
ok(bd(pipe_mid),B['v1_margin_K'],'boundary:v1',checks)
ok(bd(pipe_exact),B['v2_margin_K'],'boundary:v2',checks)
assert bd(pipe_mid)<0<bd(pipe_exact) and B['v1_guard']==0 and B['v2_guard']==1
# Only sample-specific TINC. Decimal serialization may not encode full binary bounds.
tinc=json.loads((R/'results/mcp_tinc_samples.json').read_text())
tinc_results=[]
for j,(amb,UA) in enumerate(tinc['cases']):
    Te=pipe_exact(num('82'),num(amb),num(UA),num('10'),num('4180'))
    loss=(num('82')-Te)*num('10')*num('4180')
    for idx,ref in [(0,Te),(1,loss)]:
        lo=num(tinc['lower'][idx][j]);hi=num(tinc['upper'][idx][j]);point=num(tinc['values'][idx][j]);
        enclosed=bool(lo<=ref<=hi)
        tinc_results.append({'case':j,'graph':tinc['graph_ids'][idx],'decimal_text_inclusion':enclosed,'point_inside_returned_bounds':bool(lo<=point<=hi)})
summary={'status':'PASS' if all(r['pass'] for r in checks) else 'FAIL','precision_digits':90,
 'edge_scenarios':49,'network_scenarios':25,'accepted_v1':accept1,'accepted_v2':accept2,
 'reference_checks':len(checks),'tinc_recorded_decimal_cases':len(tinc_results),
 'tinc_decimal_inclusion_count':sum(x['decimal_text_inclusion'] for x in tinc_results),
 'tinc_warning':'TINC checks apply to only fixed inputs and rounded decimal response bounds; not a proof for continuous input ranges.',
 'all_synthetic':True,'cpp_local_runtime_executed':False}
(R/'results/independent_validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(R/'results/independent_numerical_audit.json').write_text(json.dumps({'summary':summary,'numeric_checks':checks,'tinc_checks':tinc_results},indent=2)+'\n')
print(json.dumps(summary,indent=2))
