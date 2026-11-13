#!/usr/bin/env python3
"""Independent file and physical-accounting checks of complete original-SDK run."""
import csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(s):return list(csv.DictReader((ROOT/s).open()))
sumry=json.loads((ROOT/'results/execution_summary.json').read_text())
p=read('examples/paceval_operating_sweep.csv');surf=read('examples/paceval_operating_surface.csv');tr=read('examples/paceval_operating_trace.csv');vers=read('examples/paceval_formula_version_profile.csv');reg=read('examples/formula_registry.csv')
assert len(reg)==sumry['paceval_graphs']==86
assert len(p)==sumry['sweep_points']==6000
assert len(surf)==sumry['operating_surface_points']==3721
assert len(tr)==sumry['hourly_trace_points']==48 and len(vers)==20
count=0
for r in p:
 f=lambda k:float(r[k]); q=f('q_m3s');hp=f('head_pump_m');h=f('head_system_m')
 assert abs(hp-h-f('residual_m'))<1e-9
 assert abs(f('branch_a_m3s')+f('branch_b_m3s')-q)<1e-12
 assert .35 < f('efficiency_base') < .85
 assert abs(f('electric_power_base_kW')*f('efficiency_base')*.94-f('hydraulic_power_kW'))<1e-8
 assert f('electric_power_v1_kW')>0 and f('electric_power_v20_kW')>0
 count+=7
for r in surf:
 f=lambda k:float(r[k]);q=f('q_operating_m3s')
 assert abs(f('pump_head_m')-f('system_head_m'))<1e-10
 assert abs(f('hydraulic_residual_m'))<1e-10
 assert abs(f('branch_a_m3s')+f('branch_b_m3s')-q)<1e-12
 assert .35 < f('eta_base') < .85
 count+=4
for r in vers:
 f=lambda k:float(r[k]);assert .35<f('efficiency')<.85
 assert abs(f('cost_per_hour')-.21*f('power_kW'))<1e-9
 count+=2
energy=cost=e1=e20=0
for r in tr:
 f=lambda k:float(r[k]);energy+=f('elec_base_kW');e1+=f('elec_version_1_kW');e20+=f('elec_version_20_kW');cost+=f('hourly_cost_base')
 assert abs(f('cumulative_base_energy_kWh')-energy)<5e-9
 assert abs(f('cumulative_version1_energy_kWh')-e1)<5e-9
 assert abs(f('cumulative_version20_energy_kWh')-e20)<5e-9
 assert f('head_m')>0 and .35<f('eta_base')<.85
 count+=5
assert abs(energy-sumry['energy_base_kWh'])<1e-7
assert abs(cost-sumry['cost_base_currency'])<1e-7
assert sumry['max_head_residual_m']<1e-10
prec=json.loads((ROOT/'results/high_precision_validation.json').read_text());assert prec['status']=='passed' and prec['checked_values']>3000
report={'status':'passed','tested_physical_and_accounting_checks':count,'sweep_points':len(p),'operating_points':len(surf),'trace_points':len(tr),'formula_versions':len(vers),'paceval_graphs':len(reg)}
(ROOT/'results/result_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
