#!/usr/bin/env python3
"""Independent 80-decimal-digit verification of paceval-supplied results.
No C++ formula strings are loaded. All expressions are redefined in mpmath.
"""
import csv,json
from pathlib import Path
import mpmath as m
m.mp.dps=80
root=Path(__file__).resolve().parent.parent
D=m.mpf

def evaluate(row):
 x={key:D(row[key]) for key in ('source_C','sink_C','plr','load_kw','rated_kw','aux_kw','price_eur_kwh','hours')}
 ts=x['source_C'];tk=x['sink_C']; l=x['plr'];load=x['load_kw'];rated=x['rated_kw'];aux=x['aux_kw'];price=x['price_eur_kwh'];hours=x['hours']
 lift=tk-35
 raw=D('4.4')+D('.065')*ts-D('.045')*lift-D('.0006')*lift**2+D('.002')*ts*lift
 raw2=D('4.35')+D('.069')*ts-D('.043')*lift-D('.00065')*lift**2+D('.0022')*ts*lift
 capmod=1+D('.014')*ts-D('.005')*lift
 avail=rated*capmod
 part=D('.82')+D('.18')*l-D('.06')*(1-l)**2
 deff=1-D('.08')*m.exp(-((ts-1)/3)**2)
 eff=raw*part*deff
 heat=avail*l
 pcomp=heat/eff
 pel=pcomp+aux
 sys=heat/pel
 source=heat-pcomp
 hm=heat-load
 pm=D('4.8')-pel
 copm=sys-D('2.5')
 shortage=max(load-heat,D('0'))
 pol1=D('.62')*pel/D('4.8')+D('.28')*shortage/10+D('.10')/sys
 pol2=D('.40')*pel/D('4.8')+D('.47')*shortage/10+D('.13')/sys
 ds=D('.065')+D('.002')*lift
 dt=-D('.045')-D('.0012')*lift+D('.002')*ts
 energy=heat*hours
 cost=pel*hours*price
 sys2=heat/(heat/(raw2*part*deff)+aux)
 names=('cop_map_v1','cop_map_v2','capacity_modifier','available_heat_kw','part_load_modifier',
  'synthetic_defrost_modifier','effective_cop_v1','delivered_heat_kw','compressor_electric_kw','total_electric_kw',
  'system_cop_v1','source_extracted_heat_kw','heat_demand_margin_kw','electric_limit_margin_kw',
  'cop_limit_margin','policy_score_v1','policy_score_v2','d_copmap_d_source','d_copmap_d_sink',
  'delivered_heat_kwh','electric_cost_eur','system_cop_v2')
 vals=(raw,raw2,capmod,avail,part,deff,eff,heat,pcomp,pel,sys,source,hm,pm,copm,pol1,pol2,ds,dt,energy,cost,sys2)
 return dict(zip(names,vals))

def main():
 path=root/'examples'/'operating_candidates.csv'
 rows=list(csv.DictReader(path.open()))
 picks=[rows[i] for i in range(0,len(rows), max(1,len(rows)//40))][:40]
 worst=D('0');passed=0
 for row in picks:
  expected=evaluate(row)
  for name,ref in expected.items():
   got=D(row[name]);delta=abs(got-ref); worst=max(worst,delta)
   if delta>D('2e-9')*(1+abs(ref)):
    raise AssertionError(f'Precision audit failed at candidate {row["candidate_id"]} {name} {m.nstr(delta,15)}')
   passed+=1
 audit={'status':'PASS','digits':80,'rows_verified':len(picks),'values_verified':passed,
        'maximum_absolute_difference':m.nstr(worst,17),'reference':'independent mpmath analytic implementation'}
 (root/'results'/'high_precision_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print('PASS: independent 80-digit mpmath audit',passed,'values')
if __name__=='__main__':main()
