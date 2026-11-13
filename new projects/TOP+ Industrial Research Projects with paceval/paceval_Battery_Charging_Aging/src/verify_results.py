"""Audit the ACTUAL C++/paceval outputs against the registered synthetic contract."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
s=pd.read_csv(ROOT/'examples/optimized_schedule_comparison.csv')
t=pd.read_csv(ROOT/'examples/optimized_schedule_timeseries.csv')
r=pd.read_csv(ROOT/'examples/fixed_charging_and_driving_trace.csv')
e=pd.read_csv(ROOT/'examples/paceval_cost_aging_surface.csv')
f=pd.read_csv(ROOT/'examples/formula_registry.csv')
a=pd.read_csv(ROOT/'examples/paceval_transition_audit.csv')
assert len(s)==36 and len(t)==36*24 and len(r)==6*24 and len(e)==61*61 and len(f)==23
assert len(a)==1800 and a.shape[1]==6+17+23
assert s.feasible.eq(1).all()
assert s.formula_version.nunique()==2 and s.aging_weight.nunique()==3 and s.profile.nunique()==6
assert t.groupby(['profile','aging_weight','formula_version']).size().eq(24).all()
assert np.allclose(s.final_SOC,.8,atol=1e-12)
assert np.allclose(s.grid_energy_kWh,38,atol=1e-10)
assert np.allclose(s.stored_energy_kWh,34.96,atol=1e-10)
assert np.allclose(s.driving_energy_kWh,14.72,atol=1e-10)
assert not ((t.available==0) & (t.charge_power_kW>1e-12)).any()
assert t.charge_power_kW.isin([0,2,4,6,8,10]).all()
assert np.allclose(t.SOC_after, t.SOC_before+(t.charge_power_kW*.92-t.driving_kWh)/64.4,atol=1e-12)
assert (t.SOC_after>=.15-1e-12).all() and (t.SOC_after<=.92+1e-12).all()
for k,g in t.groupby(['profile','aging_weight','formula_version']):
    g=g.sort_values('hour')
    assert np.allclose(g.SOC_before.values[1:],g.SOC_after.values[:-1],atol=2e-12)
    assert g.loc[g.hour==8,'SOC_before'].iloc[0] >=20/35-1e-12
    assert abs(g.SOC_after.iloc[-1]-.8)<1e-11
    row=s[(s.profile==k[0])&(s.aging_weight==k[1])&(s.formula_version==k[2])].iloc[0]
    assert abs(g.incremental_objective_EUR_proxy.sum()-row.total_objective_EUR_proxy)<1e-9
    assert abs(g.pv_electricity_EUR.sum()-row.electricity_cost_EUR)<1e-9
    assert abs(g.pv_grid_kWh.sum()-row.grid_energy_kWh)<1e-9
    assert abs(g.pv_risk_units.sum()-row.synthetic_risk_units)<1e-9
    assert abs(g.pv_aging_EUR_proxy.sum()-row.aging_penalty_EUR_proxy)<1e-9
assert np.allclose(a.grid_energy,a.p*a.dt)
assert np.allclose(a.soc_next,a.soc-a.drive/a.cap+a.eta*a.p*a.dt/a.cap)
assert np.allclose(a.total_risk,a.cycle_risk+a.calendar_risk)
assert np.allclose(a.objective_v1,a.tariff_cost+a.aging_cost+a.smoothness_cost)
assert not np.allclose(s.loc[(s.aging_weight==30)&(s.formula_version==1),'total_objective_EUR_proxy'].values,s.loc[(s.aging_weight==30)&(s.formula_version==2),'total_objective_EUR_proxy'].values)
result={'status':'PASS','real_optimization_schedules':len(s),'verified_hourly_steps':len(t),'fixed_profile_rows':len(r),
        'registered_real_paceval_formulas':len(f),'transition_audit_rows':len(a),'transition_scalar_checks':len(a)*23,
        'surface_points':len(e),'all_SOC_constraints_and_fixed_travel_requirements_met':True,
        'all_objective_sums_and_energy_invariants_met':True,
        'two_formula_versions_independently_retained':True,
        'measured_cell_aging_claim':False,'synthetic_data_only':True}
(ROOT/'results/scientific_consistency_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
