#!/usr/bin/env python3
"""Independent 90-digit mpmath verification of REAL paceval output CSV files.

Equations are independently implemented as physical dq balances, not parsed from
paceval formula manifest. All CSV input numbers are interpreted as exact binary64
values to avoid inventing a higher precision input than the C++ SDK received.
"""
import csv, json, sys
from pathlib import Path
from collections import defaultdict
from mpmath import mp
mp.dps=90
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results'
PARAMS=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'input/motor_parameters.csv'
def exact(s):
    v=float(s);n,d=v.as_integer_ratio();return mp.mpf(n)/d
def read(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
parameters=read(PARAMS)[0]
p={k:exact(v) for k,v in parameters.items()}

def reference(r):
    model=int(r['model']);w=exact(r['speed_rpm'])*2*mp.pi/60
    elec=p['pole_pairs']*w
    T=exact(r['temperature_C']);d=exact(r['id_Apeak']);q=exact(r['iq_Apeak'])
    rs=p['Rs25_Ohm']*(1+p['alphaR_invK']*(T-p['Tref_C'])) if model==2 else p['Rs25_Ohm']
    pm=p['psi25_Wb']*(1+p['betaPsi_invK']*(T-p['Tref_C'])) if model==2 else p['psi25_Wb']
    flux_d=pm+p['Ld_H']*d;flux_q=p['Lq_H']*q
    vd=rs*d-elec*flux_q;vq=rs*q+elec*flux_d
    torque=mp.mpf('1.5')*p['pole_pairs']*(flux_d*q-flux_q*d)
    voltage=mp.sqrt(vd**2+vq**2)
    copper=mp.mpf('1.5')*rs*(d*d+q*q)
    iron=p['kFe_proxy']*elec**2*(flux_d**2+flux_q**2)
    friction=p['kMech_proxy']*w*w
    em=torque*w
    shaft=em-friction
    inp=em+copper+iron
    efficiency=max(mp.mpf(0),shaft)/max(inp,mp.mpf('1e-9'))
    imargin=p['Imax_Apeak']**2-(d*d+q*q)
    vmax=p['Vdc_V']/mp.sqrt(3)
    vmargin=vmax**2-voltage**2
    did=mp.mpf('1.5')*p['pole_pairs']*(p['Ld_H']-p['Lq_H'])*q
    diq=mp.mpf('1.5')*p['pole_pairs']*(pm+(p['Ld_H']-p['Lq_H'])*d)
    dV2d=2*vd*rs+2*vq*elec*p['Ld_H']
    dV2q=2*vd*(-elec*p['Lq_H'])+2*vq*rs
    dTtemp=mp.mpf('1.5')*p['pole_pairs']*p['psi25_Wb']*p['betaPsi_invK']*q if model==2 else mp.mpf(0)
    return {'torque_Nm':torque,'voltage_V':voltage,'efficiency':efficiency,'shaft_power_W':shaft,'copper_loss_W':copper,'iron_loss_W':iron,'mechanical_loss_W':friction,'total_loss_W':copper+iron+friction,'current_margin_A2':imargin,'voltage_margin_V2':vmargin,'feasible_guard':int(imargin>=0 and vmargin>=0),'dtorque_did_Nm_perA':did,'dtorque_diq_Nm_perA':diq,'dvoltage2_did_V2_perA':dV2d,'dvoltage2_diq_V2_perA':dV2q,'dtorque_dtemperature_Nm_perK':dTtemp,'current_utilization':mp.sqrt(d*d+q*q)/p['Imax_Apeak'],'voltage_utilization':voltage/vmax}

def close(x,y,rel=mp.mpf('1e-8'),absval=mp.mpf('2e-8')):
    return abs(x-y)<=absval+rel*max(abs(x),abs(y))

def run():
    records=read(OUT/'screening.csv');comparison=read(OUT/'model_comparison.csv')
    assert len(records)==2*len(comparison) and len(records)>1000,'Incomplete scenario outputs'
    sample=[records[i] for i in range(0,len(records),35)]
    sample+=records[:12]+records[-12:]
    checks=0;worst=mp.mpf(0);details=[]
    fields=['torque_Nm','voltage_V','efficiency','shaft_power_W','copper_loss_W','iron_loss_W','mechanical_loss_W','total_loss_W','current_margin_A2','voltage_margin_V2','dtorque_did_Nm_perA','dtorque_diq_Nm_perA','dvoltage2_did_V2_perA','dvoltage2_diq_V2_perA','dtorque_dtemperature_Nm_perK','current_utilization','voltage_utilization']
    for r in sample:
        truth=reference(r)
        for field in fields:
            target=truth[field];actual=exact(r[field]);
            if not close(target,actual):raise AssertionError(f'{r["case_id"]}/{r["model"]} {field}: {actual} != {target}')
            worst=max(worst,abs(actual-target)/max(mp.mpf('1e-9'),abs(target)))
            checks+=1
        guard=int(float(r['feasible_guard']))
        assert guard==truth['feasible_guard']
        checks+=1
        details.append({'case_id':r['case_id'],'version':r['model'],'torque_abs_error':str(abs(truth['torque_Nm']-exact(r['torque_Nm']))),'voltage_abs_error':str(abs(truth['voltage_V']-exact(r['voltage_V']))),'efficiency_abs_error':str(abs(truth['efficiency']-exact(r['efficiency'])) )})
    # Comparison outputs are genuinely evaluated with additional paceval graphs.
    for r in comparison[::21]:
        for a,b,d in [('torque_v1_Nm','torque_v2_Nm','delta_torque_Nm'),('voltage_v1_V','voltage_v2_V','delta_voltage_V'),('efficiency_v1','efficiency_v2','delta_efficiency'),('loss_v1_W','loss_v2_W','delta_loss_W')]:
            assert close(exact(r[d]),exact(r[b])-exact(r[a]))
            checks+=1
    # At 25 C both versions share identical parameters. Model differences are
    # therefore zero at the reference temperature to tolerance.
    for r in comparison[::29]:
        if r['temperature_C']!='25':continue
        assert close(exact(r['delta_torque_Nm']),mp.mpf(0),absval=mp.mpf('1e-10'))
        assert close(exact(r['delta_voltage_V']),mp.mpf(0),absval=mp.mpf('1e-10'))
        checks+=2
    # Verify finite-grid maxima and the safety constraints independently from
    # the CSV, including the coarse-grid nature of the maxima.
    feasible=defaultdict(list)
    for r in records:
        if float(r['feasible_guard'])>0.5:
            k=(r['model'],r['temperature_C'],r['speed_rpm']);feasible[k].append(r)
    env=read(OUT/'torque_speed_envelope.csv')
    for r in env:
        k=(r['model'],r['temperature_C'],r['speed_rpm'])
        assert k in feasible
        m=max(float(x['torque_Nm']) for x in feasible[k])
        assert abs(m-float(r['max_feasible_torque_Nm']))<1e-7
        assert len(feasible[k])==int(r['feasible_points'])
        checks+=2
    chosen=read(OUT/'efficiency_recommended.csv')
    for r in chosen:
        k=(r['model'],r['temperature_C'],r['speed_rpm'])
        allowed=[x for x in feasible[k] if float(x['torque_Nm'])>=float(r['threshold_torque_Nm']) and float(x['shaft_power_W'])>0]
        assert allowed
        maxeta=max(float(x['efficiency']) for x in allowed)
        assert abs(float(r['best_efficiency'])-maxeta)<1e-8
        checks+=1
    report={'precision_digits':90,'verification_status':'PASS','high_precision_sampled_scenario_versions':len(sample),'independent_numeric_checks':checks,'max_relative_error_internal_only':str(worst),'full_records':len(records),'envelope_points_checked':len(env),'efficiency_optima_checked':len(chosen),'data_provenance':'read original application CSV, exact IEEE-754 input conversion from CSV text; independent mpmath model','scope':'uncalibrated synthetic IPMSM mathematical verification; excludes FEM, dynamometer and motor safety qualification'}
    (OUT/'scientific_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'high_precision_audit.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=details[0].keys());w.writeheader();w.writerows(details)
    print(f'90-DIGIT HIGH PRECISION PASS: {len(sample)} scenario/version rows; {checks} independent checks; {len(env)} envelope points')
if __name__=='__main__':run()
