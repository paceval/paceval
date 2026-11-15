#!/usr/bin/env python3
"""Independent 85-digit financial ALM reference. No paceval strings are reused."""
import csv,sys,json
from pathlib import Path
from collections import defaultdict
import mpmath as mp
mp.mp.dps=85
D=mp.mpf

def load(path):
    with open(path,newline='',encoding='utf8') as f:return list(csv.DictReader(f))

def verify(input_path,results_path):
    root=Path(results_path)
    input_rows=load(input_path)
    valued=load(root/'cashflow_valuations.csv')
    assert len(valued)==2*len(input_rows), 'Unexpected output row count'
    valmap={(r['model'],r['scenario'],r['cashflow_id']):r for r in valued}
    assert len(valmap)==len(valued), 'Duplicate valuations'
    checks=0;maximum=D('0');errors=[]
    def assert_near(a,b,label,rel=D('0.000000001'),absolute=D('0.00000001')):
        nonlocal checks,maximum
        a=D(str(a));b=D(str(b));error=abs(a-b)
        maximum=max(maximum,error)
        checks+=1
        if error>absolute+rel*max(abs(a),abs(b)):
            if len(errors)<12:errors.append(f'{label}: found {a} expected {b}, abs_diff={error}')
    totals=defaultdict(lambda:defaultdict(D))
    bymodel={}
    for k,raw in enumerate(input_rows):
        t=D(raw['t_year']);amount=D(raw['amount_eur_m'])
        level=D(raw['rlevel']);slope=D(raw['rslope']);hump=D(raw['rhump']);tau=D(raw['tau'])
        par=D(raw['parallel']);short=D(raw['shortshock']);long=D(raw['longshock'])
        ex=mp.exp(-t/tau);base=level+slope*(1-ex)+hump*(t/tau)*ex
        ew=mp.exp(-t/4)
        sign=1 if raw['side']=='ASSET' else -1
        for mi,model in enumerate(('V1','V2')):
            row=valmap[model,raw['scenario'],raw['cashflow_id']]
            assert row['scenario']==raw['scenario'] and row['cashflow_id']==raw['cashflow_id'] and row['model']==model, 'Row order mismatch'
            rate=base+par+(short*ew+long*(1-ew) if model=='V2' else D(0))
            df=mp.exp(-t*rate);pv=amount*df;deriv=-t*pv
            for key,v in [('zero_rate',rate),('discount_factor',df),('pv_eur_m',pv),('signed_pv_eur_m',sign*pv),('dpv_dparallel_eur_m',deriv),('short_deriv_eur_m',(-t*ew*pv if model=='V2' else D(0))),('long_deriv_eur_m',(-t*(1-ew)*pv if model=='V2' else D(0)))]:
                assert_near(row[key],v,model+'/'+raw['cashflow_id']+'/'+key,rel=D('0.00000000004'),absolute=D('0.000000001'))
            a=totals[model,raw['scenario']]
            side='a' if sign==1 else 'l'
            for name,value in [('pv',pv),('dur',t*pv),('par',deriv),('conv',t*t*pv),('short',(-t*ew*pv if model=='V2' else D(0))),('long',(-t*(1-ew)*pv if model=='V2' else D(0)))]:a[side+name]+=value
    summary=load(root/'scenario_summary.csv')
    assert len(summary)==16
    refs={}
    for (model,scenario),a in totals.items():
        apv=a['apv'];lpv=a['lpv'];refs[model,scenario]=(apv,lpv)
    for row in summary:
        model,scenario=row['model'],row['scenario'];a=totals[model,scenario];apv,lpv=refs[model,scenario]
        baseA,baseL=refs[model,'BASE'];basegap=baseA-baseL;gap=apv-lpv
        expected={'asset_pv_eur_m':apv,'liability_pv_eur_m':lpv,'net_gap_eur_m':gap,'asset_duration_years':a['adur']/apv,'liability_duration_years':a['ldur']/lpv,'duration_mismatch_years':a['adur']/apv-a['ldur']/lpv,'net_dv01_eur_m_per_bp':D('0.0001')*(a['apar']-a['lpar']),'net_convexity_num_eur_m':a['aconv']-a['lconv'],'short_dv01_eur_m_per_bp':D('0.0001')*(a['ashort']-a['lshort']),'long_dv01_eur_m_per_bp':D('0.0001')*(a['along']-a['llong']),'delta_eve_eur_m':gap-basegap,'loss_margin_eur_m':20-(basegap-gap)}
        for key,val in expected.items():assert_near(row[key],val,model+'/'+scenario+'/'+key,rel=D('0.00000000008'),absolute=D('0.000000008'))
        assert D(row['loss_guard'])==(1 if basegap-gap<=20 else 0)
        checks+=1
    # Check selected points of the genuine paceval-generated two-dimensional
    # surface, without copying its graph formula strings.
    surface=load(root/'stress_surface.csv');assert len(surface)==81
    for k in [0,1,8,9,20,36,40,50,63,72,80]:
        s=surface[k];par=D(s['parallel_shock']);sh=D(s['short_shock']);total=D(0)
        for raw in input_rows[:1024]:
            t=D(raw['t_year']);a=D(raw['amount_eur_m']);tau=D(raw['tau']);w=mp.exp(-t/4);f=mp.exp(-t/tau)
            rate=D(raw['rlevel'])+D(raw['rslope'])*(1-f)+D(raw['rhump'])*(t/tau)*f+par+sh*w
            total+=(1 if raw['side']=='ASSET' else -1)*a*mp.exp(-t*rate)
        assert_near(s['net_gap_eur_m'],total,'surface/'+str(k),rel=D('0.00000000008'),absolute=D('0.00000002'))
    audit={'status':'passed' if not errors else 'failed','mpmath_decimal_digits':mp.mp.dps,'independent_comparisons':checks,'reference_model':'fixed deterministic EUR cashflows, analytic continuously compounded rates; mpmath independently authored','max_absolute_numeric_difference':str(maximum),'failed_examples':errors,'full_cashflow_rows_checked':len(input_rows),'stress_surface_points_checked':11}
    (root/'high_precision_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    if errors:raise AssertionError('\n'.join(errors))
    print('PASS mpmath 85 digits: ',checks,'comparisons, including complete input portfolio and 11 stress surface points')
if __name__=='__main__':
    verify(Path(sys.argv[1]),Path(sys.argv[2]))
