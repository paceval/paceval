#!/usr/bin/env python3
"""Independent high-precision scientific oracle; no paceval numerical code reused."""
from pathlib import Path
import csv, json, math, random
import mpmath as mp
mp.mp.dps=80
R=Path(__file__).resolve().parents[1]
def read(name):
    with (R/'examples'/name).open(newline='') as f:return list(csv.DictReader(f))
S=read('paceval_coefficient_surface.csv')
W=read('paceval_operating_sweep.csv')
T=read('paceval_rotor_time_series.csv')
SUMMARY=json.loads((R/'results/execution_summary.json').read_text())
assert len(S)==SUMMARY['coefficient_surface_points'] and len(W)==SUMMARY['operating_sweep_points']
assert len(T)==2*SUMMARY['dynamic_steps_per_version']
assert SUMMARY['paceval_graphs']==31
m=mp.mpf
def highprecision(row):
    lam=m(row['tip_speed_ratio']);b=m(row['pitch_deg']);v=m(row['wind_ms']);om=m(row['omega_rad_s'])
    rho=m('1.225');radius=m('63');one=m('1');cp=m('0.475')*mp.exp(-((lam-m('7.6'))/m('3.1'))**2)*mp.exp(-b/m('22'))
    cp2=cp*(1+m('0.015')*mp.sin(m('0.5')*lam)*mp.exp(-b/m('25')))
    ct=m('0.03')+m('0.78')*mp.exp(-((lam-m('7'))/m('6'))**2)*mp.exp(-b/m('30'))
    air=m('0.5')*rho*m('3.141592653589793')*radius**2*v**3
    dcdl=cp*(-2*(lam-m('7.6'))/(m('3.1')**2));dcdb=-cp/m('22')
    return dict(Cp_base=cp,Cp_v2=cp2,Ct=ct,rotor_power_W=air*cp,aero_torque_Nm=air*cp/om,thrust_N=m('0.5')*rho*m('3.141592653589793')*radius**2*v**2*ct,dCp_dlambda=dcdl,dCp_dbeta=dcdb,dP_dv_fixedomega_W_per_ms=m('0.5')*rho*m('3.141592653589793')*radius**2*v**2*(3*cp-lam*dcdl),dP_domega_W_per_rad_s=air*dcdl*radius/v,betz_margin=m(16)/27-cp)

rng=random.Random(20261113)
subset=sorted(rng.sample(range(len(S)),min(160,len(S))))
maxerr=0.;tests=0
for i in subset:
    row=S[i]
    for key,want in highprecision(row).items():
        actual=m(row[key]);err=float(abs(actual-want)/(1+abs(want)))
        maxerr=max(maxerr,err);tests+=1
        assert err<2e-11,(i,key,err)
    assert float(row['Cp_base'])<16/27 and float(row['Cp_base'])>=0
    assert float(row['Cp_v2'])<16/27 and float(row['Cp_v2'])>=0

# Finite-difference checks use an independent analytical formula rather than SDK outputs.
def cp(l,b):return 0.475*math.exp(-((l-7.6)/3.1)**2)*math.exp(-b/22)
fd=0
for i in rng.sample(range(len(S)),40):
    row=S[i];l=float(row['tip_speed_ratio']);b=float(row['pitch_deg']);h=1e-5
    dp=(cp(l+h,b)-cp(l-h,b))/(2*h)
    assert abs(dp-float(row['dCp_dlambda']))<3e-9
    db=(cp(l,b+h)-cp(l,b-h))/(2*h)
    assert abs(db-float(row['dCp_dbeta']))<3e-9
    fd+=2

# Check full dynamical trace and the state equation from separate reference math.
tol=3e-9
trace_checks=0
last_energy=[0.,0.];last_next=[None,None]
for r in T:
    k=int(r['version'])-1
    omega=float(r['omega_rad_s']);v=float(r['wind_ms']);b=float(r['pitch_deg'])
    if last_next[k] is not None:
        assert abs(omega-last_next[k])<1e-10
    p=0.5*1.225*math.pi*63**2*v**3*cp(omega*63/v,b)
    if k==1:
        p*=1+0.015*math.sin(0.5*omega*63/v)*math.exp(-b/25)
    gen_raw=2.3e6*(omega/1.12)**2
    raw_power=0.95*gen_raw*omega
    grid=0.5*(raw_power+5e6-math.sqrt((raw_power-5e6)**2+1500**2))
    gen=grid/(0.95*omega)
    alpha=(p/omega-gen-1.2e5*omega)/4e7
    expected=omega+alpha
    assert abs(expected-float(r['omega_next_rad_s']))<tol
    assert abs(alpha-float(r['angular_accel_rad_s2']))<tol
    assert abs(p-float(r['rotor_power_W']))/(1+abs(p))<2e-11
    assert abs(gen-float(r['generator_torque_Nm']))/(1+abs(gen))<2e-11
    assert abs(grid-float(r['grid_power_W']))/(1+grid)<2e-11
    last_energy[k]+=float(r['grid_power_W'])/(3.6e6)
    assert abs(last_energy[k]-float(r['cumulative_energy_kWh']))<1e-7
    assert 0 < float(r['Cp']) < 16/27
    last_next[k]=expected
    trace_checks+=5
assert abs(last_energy[0]-SUMMARY['energy_version1_kWh'])<1e-6
assert abs(last_energy[1]-SUMMARY['energy_version2_kWh'])<1e-6

# Bilinear interpolation of an explicitly tabulated paceval map is a reference,
# NOT a calibrated aerodynamic model or a speed comparison.
allL=sorted(set(round(float(r['tip_speed_ratio']),10) for r in S))
allB=sorted(set(round(float(r['pitch_deg']),10) for r in S))
grid={(round(float(r['tip_speed_ratio']),10),round(float(r['pitch_deg']),10)):float(r['Cp_base']) for r in S}
assert len(allL)*len(allB)==len(grid)
def interp(l,b):
    import bisect
    i=max(0,min(len(allL)-2,bisect.bisect_right(allL,l)-1));j=max(0,min(len(allB)-2,bisect.bisect_right(allB,b)-1))
    la,lb=allL[i:i+2];ba,bb=allB[j:j+2];tx=(l-la)/(lb-la);ty=(b-ba)/(bb-ba)
    return ((1-tx)*(1-ty)*grid[la,ba]+tx*(1-ty)*grid[lb,ba]+(1-tx)*ty*grid[la,bb]+tx*ty*grid[lb,bb])
errors=[]
with (R/'results/lookup_interpolation_audit.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['lambda','pitch_deg','reference_surrogate_Cp','bilinear_lookup_Cp','absolute_difference'])
    for j in range(24):
        for i in range(24):
            l=3+11*(i+0.37)/24;b=20*(j+0.41)/24
            true=cp(l,b);table=interp(l,b);d=abs(true-table);errors.append(d);writer.writerow([f'{l:.16g}',f'{b:.16g}',f'{true:.16g}',f'{table:.16g}',f'{d:.16g}'])
report=dict(status='passed',independent_reference='mpmath 80 decimal digits',high_precision_values=tests,high_precision_max_scaled_error=maxerr,finite_difference_checks=fd,rotor_dynamics_reference_checks=trace_checks,lookup_map_test_points=len(errors),lookup_abs_difference_max=max(errors),lookup_abs_difference_mean=sum(errors)/len(errors),source='synthetic_explicit_surrogate_not_measured_turbine',scope='validates program mathematics, not aeroelastic or IEC certification')
(R/'results/high_precision_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
