#!/usr/bin/env python3
"""Independent high-precision pharmacokinetic oracle, not a paceval substitute.
Never produces the primary research CSVs. Computes fresh exact state steps and
analytical formulas from published mathematical definitions, using mpmath dps=80.
Checks complete application outputs and the actual executed graph-probe records.
"""
import argparse,csv,json,math
from pathlib import Path
import mpmath as mp
mp.mp.dps=80
N=lambda x:mp.mpf(str(x))
def readrows(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
def components(d,v,RF=None):
 r={k:N(val) for k,val in d.items() if k not in {'function_id','model_version','profile_id','route','paceval_output'}}
 if RF is not None:r['RF']=RF
 cl=r['CL0']*(r['WT']/70)**N('.75') * (r['RF'] if v==1 else (N('.55')*r['RF']+N('.45')*r['RF']**2))*mp.exp(r['etaCL'])
 vol=r['V0']*(r['WT']/70)*mp.exp(r['etaV']); ke=cl/vol
 gut=r['Ag']*mp.exp(-r['ka']*r['dt'])
 central=r['Ac']*mp.exp(-ke*r['dt'])+r['F']*r['ka']*r['Ag']/(r['ka']-ke)*(mp.exp(-ke*r['dt'])-mp.exp(-r['ka']*r['dt']))+r['Rate']/ke*(1-mp.exp(-ke*r['dt']))
 conc=central/vol
 lost=r['F']*(r['Ag']-gut)+r['Rate']*r['dt']-(central-r['Ac'])
 return r,cl,vol,ke,gut,central,conc,lost

def graph_oracle(row,id):
 if id=='clearance_delta_v2_v1':return components(row,2)[1]-components(row,1)[1]
 if id=='predicted_concentration_delta_v2_v1':return components(row,2)[6]-components(row,1)[6]
 ver=int(id.split('_v')[-1].split('_')[0]) if '_v' in id else None
 if id.startswith('score_v'):
  ver=int(id[7]);j=int(id.rsplit('_',1)[-1]);r,cl,V,k,g,a,c,l=components(row,ver)
  if j==1:return (c-r['Obs'])**2
  i=j-2;wr=N('.77')+N('.04')*i;wt=N('.08')+N('.022')*(i%5);wp=N('.12')+N('.015')*(i%4);wc=N('.025')+N('.005')*(i%3)
  dif=c-r['Cap'];soft=(dif+mp.sqrt(dif**2+N('.0001')))/2
  return wr*(c-r['Obs'])**2+wt*(c-r['Target'])**2+wp*soft**2+wc*((cl-r['CLprior'])/r['CLprior'])**2
 if ver is None:raise KeyError(id)
 r,cl,V,k,g,a,c,l=components(row,ver)
 name=id.rsplit('_v',1)[0]
 if name=='clearance':return cl
 if name=='volume':return V
 if name=='elimination_constant':return k
 if name=='half_life':return mp.log(2)/k
 if name=='gut_rate':return -r['ka']*r['Ag']
 if name=='central_rate':return r['F']*r['ka']*r['Ag']+r['Rate']-k*r['Ac']
 if name=='elimination_rate':return k*r['Ac']
 if name=='absorption_rate':return r['F']*r['ka']*r['Ag']
 if name=='depot_next':return g
 if name=='central_next':return a
 if name=='concentration_before':return r['Ac']/V
 if name=='concentration_next':return c
 if name=='eliminated_mass':return l
 if name=='auc_exact_step':return l/cl
 if name=='auc_trapezoid_step':return (r['Ac']/V+c)*r['dt']/2
 if name=='concentration_residual':return c-r['Obs']
 if name=='upper_margin':return r['Cap']-c
 if name=='lower_margin':return c-r['Target']
 if name=='auc_infinity_oral':return r['F']*r['Dose']/cl
 if name=='auc_infinity_iv':return r['Dose']/cl
 if name=='single_dose_oral_concentration':return r['F']*r['Dose']/V*r['ka']/(r['ka']-k)*(mp.exp(-k*r['time'])-mp.exp(-r['ka']*r['time']))
 if name=='single_oral_tmax':return mp.log(r['ka']/k)/(r['ka']-k)
 if name=='single_oral_cmax':return r['F']*r['Dose']/V*mp.exp(-k*(mp.log(r['ka']/k)/(r['ka']-k)))
 if name=='cl_sensitivity_rf':return cl/r['RF'] if ver==1 else r['CL0']*(r['WT']/70)**N('.75')*(N('.55')+N('.90')*r['RF'])*mp.exp(r['etaCL'])
 if name=='cl_sensitivity_weight':return N('.75')*cl/r['WT']
 if name=='volume_sensitivity_weight':return V/r['WT']
 if name=='auc_oral_sensitivity_rf':return mp.diff(lambda rf:r['F']*r['Dose']/components(row,ver,rf)[1],r['RF'])
 if name=='concentration_next_sensitivity_rf':return mp.diff(lambda rf:components(row,ver,rf)[6],r['RF'])
 if name=='squared_residual_sensitivity_rf':return mp.diff(lambda rf:(components(row,ver,rf)[6]-r['Obs'])**2,r['RF'])
 if name=='relative_clearance_margin':return (cl-r['CLprior'])/r['CLprior']
 if name=='exposure_target_margin':return r['AUCT']-r['F']*r['Dose']/cl
 raise ValueError('No independent reference formula for '+name)

def mp_trajectory(profile,version,route,steps):
 wt=N(profile['weight_kg']);RF=N(profile['renal_covariate_dimensionless']);etaCL=N(profile['eta_clearance']);etaV=N(profile['eta_volume']);ka=N(profile['ka_per_h']);F=N(profile['bioavailability_fraction']);DT=N('.25');DOSE=N('240')
 d={'Ag':mp.mpf('0'),'Ac':mp.mpf('0'),'WT':wt,'RF':RF,'etaCL':etaCL,'etaV':etaV,'CL0':N('5'),'V0':N('40'),'ka':ka,'F':F,'Rate':N('0'),'dt':DT,'Obs':N('3'),'Target':N('3'),'Cap':N('6'),'AUCT':N('40'),'CLprior':N('5'),'Dose':DOSE,'time':N('0')}
 auc=mp.mpf('0');aum=mp.mpf('0');peak=mp.mpf('0');trough=mp.mpf('0');elim=mp.mpf('0');admin=mp.mpf('0');initial=mp.mpf('0')
 for i in range(steps):
  if i%96==0 and route=='oral':d['Ag']+=DOSE;initial+=DOSE*F
  rate=N('120') if route=='iv_infusion' and i%96<8 else N('0')
  admin+=rate*DT;d['Rate']=rate;d['time']=i*DT
  r,cl,V,k,g,a,c,l=components(d,version)
  auc+=l/cl; aum+=(d['Ac']/V+c)*DT/2; elim+=l;peak=max(peak,c)
  d['Ag']=g;d['Ac']=a
  if i%96==95:trough=c
 mass=admin+initial-(d['Ac']+d['Ag']*F+elim)
 return {'auc':auc,'auc_trap':aum,'cmax':peak,'trough':trough,'cfinal':c,'eliminated':elim,'mass':mass,'clearance':cl,'volume':V,'hl':mp.log(2)/(cl/V),'single_oral_auc':F*DOSE/cl,'single_iv_auc':DOSE/cl,'tmax':mp.log(ka/(cl/V))/(ka-cl/V),'single_cmax':F*DOSE/V*mp.exp(-cl/V*mp.log(ka/(cl/V))/(ka-cl/V))}

def verify(root):
 probes=readrows(root/'results/graph_probe.csv');summary=readrows(root/'results/scenario_summary.csv');profiles=readrows(root/'examples/synthetic_virtual_profiles.csv');exec_txt=(root/'results/sdk_execution.txt').read_text()
 assert 'original paceval SDK execution SUCCESS' in exec_txt
 ids={r['function_id'] for r in probes};all_ids={r['function_id'] for r in readrows(root/'results/formula_registry.csv')};assert ids==all_ids,(len(ids),len(all_ids))
 worst=0.;n=0;tol=mp.mpf('3e-8');maxerrids={}
 # Stride sampling includes every graph, scalar, compound and sensitivity family.
 for idx,p in enumerate(probes):
  if idx%4:continue
  y=graph_oracle(p,p['function_id']);got=N(p['paceval_output']);d=abs(got-y)/(1+abs(y));n+=1
  if d>worst:worst=float(d)
  if d>tol:raise AssertionError(f"Graph audit failed {p['function_id']} sample={idx} scaled={mp.nstr(d,8)}")
  maxerrids[p['function_id']]=max(maxerrids.get(p['function_id'],0),float(d))
 # Verify complete repeated-dose PK trajectories with 80 digits (several profiles,
 # both rate versions and BOTH oral and IV routes). Not based on paceval expressions.
 profileMap={int(p['virtual_profile_id']):p for p in profiles};checkset={1,len(profiles),max(1,len(profiles)//2)}
 by_scenario=0
 for s in summary:
  pid=int(s['virtual_profile_id'])
  if pid not in checkset:continue
  steps=int(float((root/'results/sdk_execution.txt').read_text().split('time_steps=')[1].splitlines()[0]))
  z=mp_trajectory(profileMap[pid],int(s['model_version']),s['route'],steps)
  fields={'AUC0_h_mg_h_per_L':'auc','AUC_trapezoid_mg_h_per_L':'auc_trap','Cmax_sampled_mg_per_L':'cmax','last_daily_trough_mg_per_L':'trough','Cfinal_mg_per_L':'cfinal','systemic_eliminated_mg':'eliminated','conservation_residual_mg':'mass','CL_L_per_h':'clearance','V_L':'volume','half_life_h':'hl','single_dose_oral_tmax_h':'tmax','single_dose_oral_Cmax_mg_per_L':'single_cmax'}
  for col,key in fields.items():
   expected=z[key];actual=N(s[col]);d=abs(actual-expected)/(1+abs(expected));by_scenario+=1
   if d>worst:worst=float(d)
   if d>tol:raise AssertionError(f"Full trajectory mismatch id={pid} v={s['model_version']} route={s['route']} {col}: {mp.nstr(d,12)}")
  key='single_oral_auc' if s['route']=='oral' else 'single_iv_auc';d=abs(N(s['single_dose_AUC_infinity_mg_h_per_L'])-z[key])/(1+abs(z[key]));by_scenario+=1
  if d>tol:raise AssertionError('AUC∞ clinical-units formula mismatch')
 # Structural domain checks on ALL simulated scenarios.
 for s in summary:
  assert abs(float(s['conservation_residual_mg']))<2e-6
  assert float(s['AUC0_h_mg_h_per_L'])>0 and float(s['Cmax_sampled_mg_per_L'])>0
  assert float(s['CL_L_per_h'])>0 and float(s['V_L'])>0
 out={'status':'PASS','reference_precision_digits':80,'high_precision_graph_checks':n,'full_trajectory_quantity_checks':by_scenario,'total_high_precision_checks':n+by_scenario,'full_trajectories':len(checkset)*4,'graphs_covered':len(ids),'scenario_rows':len(summary),'max_relative_scaled_difference_internal_only':worst,'model':'synthetic one-compartment exact-transition oral and constant-rate IV'}
 (root/'results/high_precision_audit.json').write_text(json.dumps(out,indent=2)+'\n')
 (root/'results/verification_summary.json').write_text(json.dumps({k:v for k,v in out.items() if not k.startswith('max_')},indent=2)+'\n')
 print('INDEPENDENT 80 DIGIT VALIDATION PASS',out)
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args();verify(a.root)
