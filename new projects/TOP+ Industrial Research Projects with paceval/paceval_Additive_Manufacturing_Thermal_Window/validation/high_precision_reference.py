#!/usr/bin/env python3
"""Independent 90-decimal reference for the analytical thermal surrogates.
No paceval formula strings are evaluated or interpreted here. Reconstruct exact IEEE754 input values.
"""
import sys, json,csv,math
from pathlib import Path
from mpmath import mp
mp.dps=90
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]

def exact(v):
    n,d=float(v).as_integer_ratio()
    return mp.mpf(n)/mp.mpf(d)

def reference(P,v,anisotropy=False,depth=True):
    # independent from the paceval formula generator; all input values interpreted as binary64.
    P=exact(P);speed=exact(v)
    k=exact(35);rho=exact(8200);cp=exact(500);absorptivity=exact(.3)
    base=exact(300); r0=exact(.00006);beta=exact(.85);gamma=exact(1.4)
    x,y,z=((exact(-.000015),exact(.00001),exact(.000045)) if depth else (exact(0),exact(0),exact(0)))
    if anisotropy:
        y=y/beta;z=z/gamma
    r=mp.sqrt(x*x+y*y+z*z+r0*r0)
    alpha=k/(rho*cp)
    return base+absorptivity*P/(2*mp.pi*k*r)*mp.exp(-speed*(x+r)/(2*alpha))

rows=list(csv.DictReader((root/'results/mcp_grid_reconstructed_from_recorded_endpoints.csv').open()))
errors={'temperature_surface_v1_K':mp.mpf(0),'temperature_depth_v1_K':mp.mpf(0),'temperature_depth_v2_K':mp.mpf(0),'combined_margin_v1_K':mp.mpf(0)}
flips=0
for row in rows:
    p,v=map(float,[row['power_W'],row['scan_speed_m_per_s']]);ts=reference(p,v,depth=False);td=reference(p,v,depth=True);td2=reference(p,v,True,True)
    predictions={'temperature_surface_v1_K':ts,'temperature_depth_v1_K':td,'temperature_depth_v2_K':td2,'combined_margin_v1_K':min(td-exact(1600),exact(3100)-ts)}
    names={'temperature_surface_v1_K':'surface_temperature_v1_K','temperature_depth_v1_K':'depth_temperature_v1_K','temperature_depth_v2_K':'depth_temperature_v2_K','combined_margin_v1_K':'combined_margin_v1_K'}
    for id,ref in predictions.items():errors[id]=max(errors[id],abs(exact(row[names[id]])-ref))
    margin=predictions['combined_margin_v1_K'];flips+=int((margin>=0)!=bool(int(row['window_flag_v1'])))
# Strict at the precision of transferred endpoints; rounding in captured tool text is expected.
assert len(rows)==81 and all(float(x)<5e-8 for x in errors.values()),errors
assert flips==0
anchor=json.loads((root/'results/mcp_anchor_record.json').read_text())
for test in anchor['transcription_checks']:
    match=next(r for r in rows if float(r['power_W'])==test['P'] and float(r['scan_speed_m_per_s'])==test['v'])
    for key,name in [('Ts1','surface_temperature_v1_K'),('Td1','depth_temperature_v1_K'),('Td2','depth_temperature_v2_K')]:
        assert abs(float(match[name])-test[key])<1e-7,(test,key)

interval_rows=list(csv.DictReader((root/'results/mcp_tinc_raw_record.csv').open()))
interval_checks=0
for row in interval_rows:
    P,v=float(row['P_W']),float(row['v_mps'])
    if row['graph']=='temperature_surface_K':ref=reference(P,v,depth=False)
    elif row['graph']=='temperature_depth_K':ref=reference(P,v,depth=True)
    else:ref=min(reference(P,v,depth=True)-exact(1600),exact(3100)-reference(P,v,depth=False))
    low,high=map(exact,[row['lower'],row['upper']]);assert low<=ref<=high,(row,ref)
    assert low<=exact(row['value'])<=high
    interval_checks+=1

report={'reference':'Independent mpmath 90 decimal places, exact binary64 input values; not a replay of the paceval expression strings.','grid_cases':len(rows),'grid_reconstructed_from_transcribed_endpoint_data':True,'independent_temperature_and_margin_checks':len(rows)*len(errors),'max_absolute_difference_after_transfer_rounding_K':{k:float(v) for k,v in errors.items()},'discrete_status_disagreements':flips,'tinc_inclusions_tested':interval_checks,'tinc_inclusions_passed':interval_checks,'global_interval_certification':False,'test_result':'PASS' }
(root/'results/high_precision_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
