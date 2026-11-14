#!/usr/bin/env python3
"""Independent high-precision oracle for recorded original paceval MCP 4.26 outputs.

All source inputs are reconstructed as exact IEEE-754 binary64 values before
running mathematically independent mpmath formulas. No paceval expression
strings are interpreted. This audit never invents remote results or asserts
global certification from pointwise tests.
"""
import csv,json,sys,pathlib,datetime
from mpmath import mp
mp.dps=90
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((root/'src/formula_manifest.json').read_text());names=manifest['variables']
def rows(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))
def as_exact_float(s):
 # Convert decimal to the same Python float (binary64) used in the remote JSON
 # request, then reconstruct that float without decimal rounding.
 p,q=float(s).as_integer_ratio();return mp.mpf(p)/q
def formula_values(row):
 p={k:as_exact_float(row[k]) for k in names}
 V,T,C,S=[p[k] for k in ('V','T','C','S')]
 t0,aC,aS,aT,aV,Vref,Tref=[p[k] for k in ('t0','aC','aS','aT','aV','Vref','Tref')]
 exponent,loadpow,aCT,aCS=[p[k] for k in ('p','q','aCT','aCS')]
 I0,bT,bV,bTT,bVT=[p[k] for k in ('I0','bT','bV','bTT','bVT')]
 Req,Arr,Ncells,Wire,Pcap,Pscale=[p[k] for k in ('Treq','Tarr','Ncells','Wire','Pcap','Pscale')]
 dt=T-Tref;dv=V-Vref;rv=Vref/V
 d1=t0+aC*C+aS*S+aT*dt+aV*mp.power(rv,exponent)
 d2=t0+aC*C*mp.power(rv,loadpow)+aS*S+aT*dt+aV*mp.power(rv,exponent)+aCT*C*dt+aCS*C*S
 i1=I0*mp.exp(bT*dt+bV*dv)
 i2=I0*mp.exp(bT*dt+bV*dv+bTT*dt*dt+bVT*dt*dv)
 p1=V*i1;p2=V*i2;path1=Ncells*d1+Wire;path2=Ncells*d2+Wire
 slack1=Req-Arr-path1;slack2=Req-Arr-path2
 margin1=Pcap-p1;margin2=Pcap-p2
 score1=min(slack1,Pscale*margin1);score2=min(slack2,Pscale*margin2)
 limits=p['Vmin']<=V<=p['Vmax'] and p['Tmin']<=T<=p['Tmax']
 out=[d1,d2,i1,i2,p1,p2,path1,path2,slack1,slack2,margin1,margin2,score1,score2,
      int(slack1>=0 and margin1>=0 and limits),int(slack2>=0 and margin2>=0 and limits),
      -aC*C*loadpow*mp.power(rv,loadpow)/V-aV*exponent*mp.power(rv,exponent)/V,
      aT+aCT*C,i2*(bT+2*bTT*dt+bVT*dv),d2-d1,p2-p1,p2/Pcap]
 return dict(zip((g['id'] for g in manifest['graphs']),out))
regular_checks=0;failed=[];worst_relative=mp.mpf(0);worst_abs=mp.mpf(0)
for source,records in [('grid',rows(root/'results/mcp_corner_grid_recorded_81.csv')),('snapshots',rows(root/'results/mcp_path_snapshots_recorded_16.csv'))]:
 originals=rows(root/('data/synthetic_corner_grid_81.csv' if source=='grid' else 'data/synthetic_path_snapshots_16.csv'))
 lookup={r['scenario_id']:r for r in originals}
 for r in records:
  expected=formula_values(lookup[r['id']])
  for key,txt in r.items():
   if key in ('id','V','T'):continue
   real=expected[key];got=mp.mpf(txt);delta=abs(real-got)
   atol=mp.mpf('2e-9')*(1+abs(real))
   if delta>atol:failed.append({'source':source,'id':r['id'],'field':key,'observed':txt,'expected':mp.nstr(real,30),'abs_error':mp.nstr(delta,10)})
   worst_relative=max(worst_relative,delta/(1+abs(real)));worst_abs=max(worst_abs,delta);regular_checks+=1
  if source=='grid':
   if r['V'] != lookup[r['id']]['V'] or r['T'] != lookup[r['id']]['T']:
    failed.append({'source':'grid','id':r['id'],'issue':'Grid operating conditions mismatch'})

# The interval endpoints are retained exactly as decimal text and compared
# against high-precision results for original binary64 input parameters.
tinc_checks=0;tinc_included=0;tinc_unresolved=[]
inputs={r['scenario_id']:r for f in ('synthetic_corner_grid_81.csv','synthetic_path_snapshots_16.csv') for r in rows(root/'data'/f)}
for r in rows(root/'results/mcp_tinc_recorded_24.csv'):
 expected=formula_values(inputs[r['scenario']])[r['function_id']]
 low=mp.mpf(r['paceval_printed_lower']);high=mp.mpf(r['paceval_printed_upper'])
 if int(r['error_code'])!=0 or high<low:failed.append({'source':'tinc','row':r['scenario'],'issue':'SDK error or inverted interval'})
 included=low<=expected<=high
 tinc_checks+=1;tinc_included+=int(included)
 if not included:tinc_unresolved.append({'scenario':r['scenario'],'function':r['function_id'],'low':r['paceval_printed_lower'],'high':r['paceval_printed_upper'],'reference':mp.nstr(expected,35)})
result={'source':'Actual paceval MCP v4.26 values stored as decimal text; independent binary64-input mpmath (90 dps)',
        'comparison_tolerance':'abs(reference - recorded) <= 2e-9*(1+abs(reference)) for truncated/transcribed numeric records',
        'status':'PASS' if not failed else 'FAIL','regular_graph_point_checks':regular_checks,'failed_regular_checks':len(failed),
        'max_regular_abs_difference_technical_only':mp.nstr(worst_abs,12),'max_regular_scaled_difference_technical_only':mp.nstr(worst_relative,12),
        'tinc_printed_interval_checks':tinc_checks,'tinc_printed_interval_inclusions':tinc_included,'tinc_printed_interval_unresolved':tinc_unresolved,
        'failures':failed[:100], 'local_sdk_runtime_test':'NOT EXECUTED: compatible shared library unavailable',
        'note':'TINC printed decimal inclusion at finite input points is not a proof of global interval arithmetic or of PVT uncertainty propagation.'}
(root/'results/high_precision_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('failures','tinc_printed_interval_unresolved')},indent=2))
if failed:print('FIRST FAIL',failed[:3]);raise SystemExit(1)
