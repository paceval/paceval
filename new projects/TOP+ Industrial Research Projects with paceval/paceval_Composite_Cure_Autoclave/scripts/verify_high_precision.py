#!/usr/bin/env python3
"""Independent 90-decimal-digit mpmath verification of executed SDK data.
This code never parses or executes paceval expression strings: equations are
implemented independently. Detailed numerical residuals are technical audit only.
"""
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path
import mpmath as mp
mp.mp.dps=90

def check(a,b,unit,observed):
    if not (mp.isfinite(a) and mp.isfinite(b)):
        raise AssertionError(f'Nonfinite high precision check: {unit}')
    tol=mp.mpf('4e-8')*max(abs(a),abs(b))+mp.mpf('5e-6')
    deviation=abs(a-b)
    if deviation > tol:
        raise AssertionError(f'{unit}: observed={observed}, exact={mp.nstr(a,35)}, residual={mp.nstr(deviation,16)}, bound={mp.nstr(tol,16)}')
    return float(deviation)

def main(folder):
    folder=Path(folder)
    file=folder/'high_precision_samples.csv'
    assert file.is_file(),f'Missing real output {file}'
    count=0;worst=0;versions=defaultdict(int)
    with file.open(newline='',encoding='utf-8') as f:
      for r in csv.DictReader(f):
        p=lambda key:mp.mpf(r[key]);model=r['model'];versions[model]+=1
        T=p('T_K');a=p('alpha');left=p('left_K');right=p('right_K');Ta=p('air_K')
        dz=p('dz_m');cond=p('k_W_mK');h=p('h_W_m2K');boundary=p('boundary')
        rhoCp=p('rhoCp_J_m3K');rhoRes=p('rhoRes_kg_m3');Hc=p('Hc_J_kg')
        A1=p('Aone_1_s');A2=p('Atwo_1_s');E1=p('Eone_J_mol');E2=p('Etwo_J_mol')
        R=p('Rg_J_molK');m=p('mExp');n=p('nExp');tg0=p('TgZero_K')
        tgFull=p('TgFull_K');lam=p('lambda');width=p('width_K')
        k1=A1*mp.exp(-E1/(R*T));k2=A2*mp.exp(-E2/(R*T))
        tg=tg0+(tgFull-tg0)*lam*a/(1-(1-lam)*a)
        diffusion=mp.mpf(1) if model=='V1' else 1/(1+mp.exp((tg-T)/width))
        bare=(k1+k2*a**m)*(1-a)**n
        rate=bare*diffusion
        source=rhoRes*Hc*rate
        thermal_coeff=cond/(rhoCp*dz**2)
        boundary_coeff=h/(rhoCp*dz)
        dT=(cond*(left-2*T+right)/dz**2+boundary*h*(Ta-T)/dz+source)/rhoCp
        sensitivity=(k1*E1/(R*T*T)+k2*a**m*E2/(R*T*T))*(1-a)**n
        if model=='V2':sensitivity=sensitivity*diffusion+bare*diffusion*(1-diffusion)/width
        expected={'K1':k1,'K2':k2,'BASE_RATE':bare,'TG':tg,'DIFF_FACTOR':diffusion,'CURE_RATE':rate,
                  'HEAT_SOURCE':source,'HEAT_TEMPERATURE_RATE':source/rhoCp,
                  'THERMAL_COEFFICIENT':thermal_coeff,'SURFACE_COEFFICIENT':boundary_coeff,
                  'TEMPERATURE_RATE':dT,'SENS_T':sensitivity,'INTEGRATED_HEAT':rhoRes*Hc*a}
        for key,value in expected.items():
            e=check(value,p(key),model+':'+key,r[key]);count+=1;worst=max(worst,e)
    with (folder/'screening.csv').open(newline='',encoding='utf-8') as f:
        screening=list(csv.DictReader(f))
    assert len(screening)>0
    by_recipe=defaultdict(dict)
    for row in screening:
        m=row['model'];by_recipe[row['recipe_id']][m]=row
        a=mp.mpf(row['alpha_mean']);H=mp.mpf(row['released_enthalpy_J_m3'])
        for x,y,k in [(mp.mpf(610)*mp.mpf(250000)*a,H,'enthalpy balance'),
                      (mp.mpf(row['alpha_min'])-mp.mpf('0.88'),mp.mpf(row['margin_cure']),'cure margin'),
                      (mp.mpf('196')-mp.mpf(row['peak_T_C']),mp.mpf(row['margin_peak_T_K']),'temperature margin'),
                      (mp.mpf('32')-mp.mpf(row['peak_through_thickness_gradient_K']),mp.mpf(row['margin_gradient_K']),'gradient margin')]:
            e=check(x,y,k,str(y));worst=max(worst,e);count+=1
        status=(mp.mpf(row['margin_cure'])>=0 and mp.mpf(row['margin_peak_T_K'])>=0 and mp.mpf(row['margin_gradient_K'])>=0 and mp.mpf(row['pressure_bar'])>=mp.mpf('3.5'))
        assert status == (row['screening_guard']=='1'), 'Combined screening decision not conservative'
        assert mp.mpf(0)<=mp.mpf(row['alpha_min'])<=mp.mpf(row['alpha_max'])<=mp.mpf(1)
        count+=2
    with (folder/'model_comparison.csv').open(newline='',encoding='utf-8') as f:
        comps=list(csv.DictReader(f))
    for row in comps:
        a=by_recipe[row['recipe_id']]['V1'];b=by_recipe[row['recipe_id']]['V2']
        for key,x,y in [('delta_alpha','alpha_min','alpha_min'),('delta_peak_K','peak_T_C','peak_T_C'),('delta_heat_J_m3','released_enthalpy_J_m3','released_enthalpy_J_m3'),('delta_gradient_K','peak_through_thickness_gradient_K','peak_through_thickness_gradient_K')]:
            e=check(mp.mpf(b[y])-mp.mpf(a[x]),mp.mpf(row[key]),key,row[key]);worst=max(worst,e);count+=1
    # Check monotone conversion for all recorded nodes, within each model/recipe.
    last={}; monotone_checks=0
    with (folder/'cure_profiles.csv').open(newline='',encoding='utf-8') as f:
      for r in csv.DictReader(f):
        key=(r['recipe_id'],r['model'],r['node']);alpha=float(r['alpha']);T=float(r['part_C']);time=float(r['time_min'])
        assert math.isfinite(alpha) and math.isfinite(T) and 0<=alpha<=1 and -20<T<300
        if key in last:
          t0,a0=last[key];assert time>t0 and alpha>=a0-1e-12, f'Cure monotonicity violated at {key}'
          monotone_checks+=1
        last[key]=(time,alpha)
    audit={'method':'independent 90-digit mpmath equations (not a second paceval formula parser)',
           'source':'executed SDK csv samples, end-of-recipe tables, and state series',
           'sample_rows_by_version':dict(versions),'high_precision_endvalue_checks':count,
           'state_monotonicity_checks':monotone_checks,'maximum_absolute_observed_residual':worst,
           'status':'PASS','scope_limit':'High precision pointwise/endvalue checks and recorded-state invariants; no 90-digit ODE trajectory integration or validated industrial resin fit'}
    (folder/'high_precision_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf8')
    print('HIGH PRECISION PASS',count,'formula/endvalue assertions +',monotone_checks,'time monotonicity checks, 90 decimal digits')
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: verify_high_precision.py path/to/results')
    main(sys.argv[1])
