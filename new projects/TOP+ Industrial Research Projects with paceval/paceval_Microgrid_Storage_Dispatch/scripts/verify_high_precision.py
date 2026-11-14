#!/usr/bin/env python3
"""Independent 85-decimal-place physical reference on original decimal-input floats.

The mathematical functions below are written independently rather than by
parsing or reusing the expression strings registered with paceval.
"""
import csv,json,sys,math,pathlib
from collections import defaultdict
import mpmath as mp
mp.mp.dps=85
M=lambda v:mp.mpf(float(v))  # preserve exactly the binary64 values used by the reference

def loadcsv(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
def close(a,b,rel=mp.mpf('3e-8'),abs_=mp.mpf('3e-7')):
 return abs(a-b)<=abs_+rel*max(abs(a),abs(b))
def verify(resultdir,inputdir,write=True):
 resultdir=pathlib.Path(resultdir);inputdir=pathlib.Path(inputdir)
 param={x['parameter']:M(x['value']) for x in loadcsv(inputdir/'parameters.csv')}
 records=loadcsv(inputdir/'dispatch_candidates.csv');recordmap={(x['scenario'],x['schedule_id'],int(x['hour'])):x for x in records}
 steps=loadcsv(resultdir/'dispatch_timeseries.csv');summaries={(x['scenario'],x['schedule_id'],x['model']):x for x in loadcsv(resultdir/'schedule_summary.csv')}
 scenario_ids=sorted({(s,k) for s,k,h in recordmap})
 selected={pair for i,pair in enumerate(scenario_ids) if i%11==0 or pair[1] in ('0000','0001','0359')}
 states={};costs=defaultdict(lambda:mp.mpf('0'));minres={};guards={};max_errors={};checks=0;fails=[]
 def test(name,got,ref):
  nonlocal checks
  checks+=1
  gap=float(abs(got-ref));max_errors[name]=max(max_errors.get(name,0),gap)
  if not close(got,ref): fails.append({'name':name,'actual':str(got),'reference':str(ref)})
 for x in steps:
  key=(x['scenario'],x['schedule_id'])
  if key not in selected:continue
  mod=x['model'];k=(key[0],key[1],mod);h=int(x['hour']);v=1 if mod=='V1' else 2
  row=recordmap[(key[0],key[1],h)]
  z={col:M(row[col]) for col in ('pv_kW','load_kW','gen_kW','charge_kW','discharge_kW','import_kW','export_kW','curtail_kW','shed_kW','buy_USD_per_kWh')}
  E=states.get(k,param['einitial']);ch=z['charge_kW'];dis=z['discharge_kW'];
  efc=param['etaC'];efd=param['etaD']; frac=E/param['emax']-mp.mpf('.5')
  if v==2:
   efc*=1-param['etaSlope']*frac**2
   efd*=1-mp.mpf('.5')*param['etaSlope']*frac**2
  nextE=E+param['dt']*(efc*ch-dis/efd)
  balance=z['pv_kW']-z['curtail_kW']+z['gen_kW']+dis+z['import_kW']-ch-z['export_kW']-z['load_kW']+z['shed_kW']
  prevGen=M(recordmap[(key[0],key[1],h-1)]['gen_kW']) if h else z['gen_kW']
  aging=param['cage']*(ch+dis) if v==2 else mp.mpf('0')
  stepCost=param['dt']*(param['fuel']*z['gen_kW']+z['buy_USD_per_kWh']*z['import_kW']-param['sell']*z['export_kW']+param['ccurt']*z['curtail_kW']+param['cshed']*z['shed_kW']+aging+param['ramp']*abs(z['gen_kW']-prevGen))
  de=mp.mpf('1')
  if v==2:
   dc=-2*param['etaC']*param['etaSlope']*frac/param['emax']
   dd=-param['etaD']*param['etaSlope']*frac/param['emax']
   de+=param['dt']*(dc*ch+dis*dd/(efd*efd))
  vals=[('energy',nextE,'E_next_kWh'),('balance',balance,'balance_kW'),('step_cost',stepCost,'step_cost_USD'),('reserve',nextE-param['eres'],'reserve_margin_kWh'),('eta_charge',efc,'charge_eff'),('eta_discharge',efd,'discharge_eff'),('charge_sensitivity',param['dt']*efc,'dEnext_dPch_h'),('discharge_sensitivity',-param['dt']/efd,'dEnext_dPdis_h'),('energy_sensitivity',de,'dEnext_dE')]
  for label,ref,col in vals:test(label,M(x[col]),ref)
  gates=[abs(balance)<=param['tol'],nextE>=param['emin']-param['tol'],nextE<=param['emax']+param['tol'],nextE>=param['eres']-param['tol'],ch<=param['chmax']+param['tol'],dis<=param['dismax']+param['tol'],z['gen_kW']<=param['genmax']+param['tol'],z['import_kW']<=param['impmax']+param['tol'],z['export_kW']<=param['expmax']+param['tol'],z['curtail_kW']<=z['pv_kW']+param['tol'],z['load_kW']-z['shed_kW']>=mp.mpf('.62')*z['load_kW']-param['tol'],abs(z['gen_kW']-prevGen)<=param['rampmax']+param['tol'],ch==0 or dis==0,key[0]!='island_outage' or (z['import_kW']==0 and z['export_kW']==0)]
  expected_guard=mp.mpf(1 if all(gates) else 0)
  test('compound_guard',M(x['step_guard']),expected_guard)
  costs[k]+=stepCost;minres[k]=min(minres.get(k,nextE-param['eres']),nextE-param['eres']);guards[k]=guards.get(k,True) and bool(expected_guard)
  states[k]=nextE
 for k,e in states.items():
  s=summaries[k];test('full_day_final_energy',M(s['final_energy_kWh']),e);test('full_day_total_cost',M(s['total_cost_USD']),costs[k]);test('full_day_min_reserve',M(s['min_reserve_margin_kWh']),minres[k]);
  expected=int(guards[k] and e>=param['goal']-param['tol']);test('full_day_guard',M(s['full_schedule_feasible']),mp.mpf(expected))
 outcome={'type':'independent native mpmath reference, 85 decimal digits','reference_input':'binary64 CSV literals converted independently','sampled_complete_24h_schedules':len(selected),'sampled_model_schedule_chains':len(states),'reference_assertions':checks,'all_passed':not fails,'failures':fails[:15],'maximum_absolute_differences_internal':max_errors,'caution':'Finite sample of scenarios, not a proof of control-system or grid-code compliance'}
 if write:
  with (resultdir/'high_precision_audit.json').open('w') as f:json.dump(outcome,f,indent=2,sort_keys=True)
 if fails:raise ValueError(f'{len(fails)} of {checks} checks failed, first={fails[0]}')
 print(f'HIGH-PRECISION PASS: {checks} independent 85-digit checks, {len(states)} complete model-schedule chains')
 return outcome
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('verify_high_precision.py results/ input/')
 verify(sys.argv[1],sys.argv[2])
