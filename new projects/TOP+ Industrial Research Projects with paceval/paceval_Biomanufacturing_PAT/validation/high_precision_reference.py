#!/usr/bin/env python3
"""Independent 90-digit mathematical reference; never substitutes paceval execution."""
import csv,json,sys
from pathlib import Path
import mpmath as mp
mp.mp.dps=90
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
F=mp.mpf

def binary(x):return F(float(x)) # exact binary64 value, not decimal intent

def compute(v):
 S,D,X,um,Ks,Ko,Ki,Y,qo,qg,k,ds,feed,V,Sf,dmin,tau,cap=[binary(z) for z in v]
 ma=um*(S/(Ks+S))*(D/(Ko+D));mb=um*(S/(Ks+S+S*S/Ki))*(D/(Ko+D))
 oa=qo*X;ob=(qo+qg*mb)*X; tr=k*(ds-D)
 one=tr-oa;two=tr-ob
 return {'mu1':ma,'mu2':mb,'OUR1':oa,'OUR2':ob,'OTR':tr,'dDO1':tr-oa-(feed/V)*D,
 'dDO2':tr-ob-(feed/V)*D,'dS2':(feed/V)*(Sf-S)-mb*X/Y,'dX2':(mb-feed/V)*X,
 'margin1':one,'margin2':two,'score1':min(D-dmin,tau*one),'score2':min(D-dmin,tau*two),
 'flag1':F(1 if D>=dmin and one>=0 else 0),'flag2':F(1 if D>=dmin and two>=0 else 0),
 'dkla':ds-D,'kLaReq':ob/(ds-D),
 'sensitivity_muS':um*D/(Ko+D)*(Ks-S*S/Ki)/(Ks+S+S*S/Ki)**2}

def close(ref,raw):
 actual=F(raw)
 tol=F('1e-10')*(1+abs(ref)) # recorded results rounded to 13 significant digits
 return abs(ref-actual)<=tol,abs(ref-actual)

report=[];checked=0;bad=[];maxerr=F(0)
inputs=list(csv.DictReader((root/'data'/'synthetic_sensor_snapshots.csv').open()))
rows=list(csv.DictReader((root/'results'/'mcp_timeseries_24graphs_excerpt.csv').open()))
assert len(inputs)==len(rows)==16
keys={'mu1':'mu1','mu2':'mu2','OUR1':'OUR1','OUR2':'OUR2','OTR':'OTR','dDO1':'dDO1','dDO2':'dDO2','dS2':'dS2','dX2':'dX2','margin1':'margin1','margin2':'margin2','score1':'score1','score2':'score2','flag1':'flag1','flag2':'flag2','dkla':'dkla','kLaReq':'kLaReq'}
for inp,record in zip(inputs,rows):
 p=compute([float(inp[x]) for x in ['S','DO','X','umax','Ks','Ko','Ki','Yxs','qO2','qG','kLa','DOstar','F','V','Sfeed','DOmin','tau','OURcap']])
 for col,key in keys.items():
  ok,e=close(p[key],record[col]);checked+=1;maxerr=max(maxerr,e)
  if not ok:bad.append(('replay',inp['time_h'],col,mp.nstr(e,10)))
  report.append(('time_series',inp['time_h'],col,record[col],mp.nstr(p[key],26),mp.nstr(e,12),'PASS' if ok else 'FAIL'))
# The independently-coded formulas are applied to the entire 81 point grid.
grid_inputs=list(csv.DictReader((root/'data'/'synthetic_state_grid.csv').open()))
grid_rows=list(csv.DictReader((root/'results'/'mcp_grid_scores_81.csv').open()))
assert len(grid_rows)==len(grid_inputs)==81
for i,(inp,out) in enumerate(zip(grid_inputs,grid_rows)):
 p=compute([float(inp[x]) for x in ['S','DO','X','umax','Ks','Ko','Ki','Yxs','qO2','qG','kLa','DOstar','F','V','Sfeed','DOmin','tau','OURcap']])
 for key,col in [('margin2','oxygen_margin_v2_gO2_per_L_per_h'),('score2','score_v2_gO2_per_L'),('flag2','guard_v2')]:
  ok,e=close(p[key],out[col]);checked+=1;maxerr=max(maxerr,e)
  if not ok:bad.append(('grid',i,col,mp.nstr(e,10)))
  report.append(('grid',str(i),key,out[col],mp.nstr(p[key],26),mp.nstr(e,12),'PASS' if ok else 'FAIL'))
# Check TINC inclusion of high-precision calculation evaluated at the EXACT supplied binary64 numbers.
tinc_rows=list(csv.DictReader((root/'results'/'mcp_tinc_18_checks.csv').open()))
for i,row in enumerate(tinc_rows):
 v=[float(row['S_gL']),float(row['DO_gO2L']),float(row['X_gDWL']),.4,.6,.0015,5,.48,.04,.06,float(row['kLa_per_h']),.008,float(row['F_Lh']),3,40,.0015,.2,.2]
 p=compute(v)
 ref=p[{'v2_oxygen_margin':'margin2','v2_score':'score2','v2_growth':'mu2'}[row['function_id']]]
 lo,hi=F(row['paceval_tinc_lower']),F(row['paceval_tinc_upper'])
 ok=lo<=ref<=hi;checked+=1
 if not ok:bad.append(('tinc',i,row['function_id'],mp.nstr(ref,22)))
 report.append(('tinc',str(i),row['function_id'],row['paceval_value'],mp.nstr(ref,26),mp.nstr(min(ref-lo,hi-ref),12),'PASS' if ok else 'FAIL'))
# Reference-only limits and model properties. These are not counted as executed paceval checks.
for S,DO in [(0,.003),(2,0),(100,.003),(1,.0015)]:
 inp=[S,DO,2,.4,.6,.0015,5,.48,.04,.06,55,.008,.04,3,40,.0015,.2,.2]
 out=compute(inp)
 assert out['mu2']>=0 and out['OTR']>0
# Audit data are technical; no C++/paceval deviation tables are published in PDF/README.
p=root/'results'/'independent_numerical_audit.csv'
with p.open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['origin','scenario','function','paceval_record','reference_90_digit','absolute_difference_or_interval_slack','verdict']);w.writerows(report)
summary={'reference_precision_decimal_digits':90,'audit_checks':checked,'audit_failures':len(bad),'regular_numerical_checks':checked-len(tinc_rows),'tinc_samples':len(tinc_rows),'tinc_reported_decimal_inclusions':len(tinc_rows)-sum(b[0]=='tinc' for b in bad),'tinc_ambiguous_or_noninclusive_reported_bounds':sum(b[0]=='tinc' for b in bad),'recorded_outputs_rounded_significant_digits':13,'maximum_absolute_recorded_decimal_difference':mp.nstr(maxerr,12),'status':'PARTIAL (rounded TINC outputs require typed-double verification)' if bad else 'PASS','failures':bad[:15], 'note':'Reference uses exact IEEE binary64 inputs. Three returned TINC score intervals collapse to identical printed decimal endpoints and do not enclose the exact binary-input mathematical value when interpreted literally; typed SDK bounds may differ and require local execution.'}
(root/'results'/'independent_validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
if any(e[0]!='tinc' for e in bad):raise SystemExit(1)
