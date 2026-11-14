#!/usr/bin/env python3
"""Independent analytic, array and arbitrary precision audit of recorded paceval results.
It does not evaluate paceval graph text. This independent program implements the stated
mathematical model from its own equations and verifies final pointwise outputs and summaries.
"""
import sys,json,math,os
from pathlib import Path
import numpy as np
import pandas as pd
from mpmath import mp
ROOT=Path(__file__).resolve().parents[1]
D=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results'
small='--small' in sys.argv
A=pd.read_csv(D/'wafer_points.csv');S=pd.read_csv(D/'recipe_summary.csv');e=json.loads((D/'execution_evidence.json').read_text())
expected=int(e['total_model_point_rows']);assert len(A)==expected and len(S)==2*e['recipe_count']
assert len(A.groupby(['recipe','version']))==len(S)
X=A.x.to_numpy();Y=A.y.to_numpy();T=A.tempK.to_numpy();P=A.pressureMTorr.to_numpy();B=A.biasIndex.to_numpy();C=A.chemistryIndex.to_numpy();et=A.etchMinutes.to_numpy();v=A.version.to_numpy()
R=X*X+Y*Y;ring=np.exp(-((R-.64)/.18)**2)
bf=np.where(v==1,33000.,34000.)*np.exp(-12800/(8.314462618*T))*(P/30)**.34*(1+.12*(C-1))*(1+.08*(B-1))
bm=np.where(v==1,7000.,7300.)*np.exp(-13800/(8.314462618*T))*(P/30)**.20*(1+.035*(C-1))*(1+.10*(B-1))
sf=np.where(v==1,1+.025*R-.012*X+.010*Y+.004*X*Y,1+.015*R-.008*X+.009*Y+.004*X*Y+.025*ring)
sm=np.where(v==1,1+.012*R+.006*X-.003*Y,1+.016*R+.004*X-.005*Y+.006*ring)
film=bf*sf;mask=bm*sm;center=bf*np.where(v==1,1,1+.025*np.exp(-((0-.64)/.18)**2))
dx=bf*np.where(v==1,.05*X-.012+.004*Y,.03*X-.008+.004*Y+.025*ring*(-2*(R-.64)/(.18**2))*2*X)
dy=bf*np.where(v==1,.05*Y+.010+.004*X,.03*Y+.009+.004*X+.025*ring*(-2*(R-.64)/(.18**2))*2*Y)
dT=film*12800/(8.314462618*T*T);dP=film*.34/P;dC=film*.12/(1+.12*(C-1))
# The original deterministic recipe definition is reimplemented independently here.
recipe=A.recipe.to_numpy();target=540+15*((recipe*3)%9);smin=6.5+.15*(recipe%7)
depth=film*et;maskLoss=mask*et;select=film/np.maximum(mask,1e-8);delta=(film-center)/center
maskRemain=160-maskLoss;filmRemain=1050-depth;res=depth-target
marginDepth=48-np.abs(res);marginS=select-smin;marginM=maskRemain-79;marginU=.08-np.abs(delta)
q=.48*(res/target)**2+.23*(delta/.08)**2+.18*(np.maximum(0,smin-select)/smin)**2+.11*(maskLoss/160)**2
qm=.10-q;gate=np.logical_and.reduce([R<=1,marginS>=0,marginM>=0,marginDepth>=0,marginU>=0,qm>=0]).astype(float)
checks={"filmRateNmPerMin":film,"maskRateNmPerMin":mask,"centerRateNmPerMin":center,"filmDepthNm":depth,"maskErosionNm":maskLoss,"selectivity":select,"relativeDeviation":delta,"filmRemainingNm":filmRemain,"maskRemainingNm":maskRemain,"depthResidualNm":res,"depthMarginNm":marginDepth,"selectivityMargin":marginS,"maskMarginNm":marginM,"uniformityMargin":marginU,"qualityScore":q,"qualityMargin":qm,"booleanGate":gate,"gradientX":dx,"gradientY":dy,"sensitivityTemp":dT,"sensitivityPressure":dP,"sensitivityChemistry":dC}
max_abs={};number=0
for c,ref in checks.items():
 measured=A[c].to_numpy();diff=np.abs(measured-ref)
 # CSV uses the original paceval double-to-string converter with limited precision.
 assert np.isfinite(measured).all(),f'{c}: nonfinite values'
 if c=='booleanGate':
  assert np.array_equal(measured,ref),f'{c}: discrete classification does not match';
 else:
  assert np.allclose(measured,ref,rtol=1e-10,atol=2e-10),f'{c}: first failing index {np.argmax(diff)} / {diff.max()}'
 max_abs[c]=float(diff.max());number+=len(A)
# Audit all area-sampled wafer summary rows independently.
summaryChecks=0
for (recipe,ver),g in A.groupby(['recipe','version']):
 entry=S[(S.recipe==recipe)&(S.version==ver)].iloc[0];r=g.filmRateNmPerMin.to_numpy()
 means={"meanFilmRateNmPerMin":np.mean(r),"minFilmRateNmPerMin":np.min(r),"maxFilmRateNmPerMin":np.max(r),"nonuniformityPct":100*(np.max(r)-np.min(r))/(2*np.mean(r)),"coefficientVariationPct":100*np.std(r,ddof=0)/np.mean(r),"meanSelectivity":g.selectivity.mean(),"meanDepthNm":g.filmDepthNm.mean(),"meanMaskRemainingNm":g.maskRemainingNm.mean(),"meanQualityScore":g.qualityScore.mean(),"passFraction":g.booleanGate.mean()}
 for c,r in means.items():
  assert np.isclose(entry[c],r,rtol=1e-9,atol=5e-7),f'Summary {recipe},{ver},{c}: {entry[c]} vs {r}';summaryChecks+=1
# Independent mpmath 80-digit calculation on a representative deterministic selection.
mp.dps=80
indexes=np.linspace(0,len(A)-1,min(512,len(A)),dtype=int)
high_precision=0;hi_max=0.
for k in indexes:
 row=A.iloc[int(k)];x=mp.mpf(str(row.x));y=mp.mpf(str(row.y));t=mp.mpf(str(row.tempK));p=mp.mpf(str(row.pressureMTorr));b=mp.mpf(str(row.biasIndex));c=mp.mpf(str(row.chemistryIndex));v=int(row.version)
 r=x*x+y*y;rr=mp.exp(-((r-mp.mpf('.64'))/mp.mpf('.18'))**2)
 film0=(mp.mpf('33000') if v==1 else mp.mpf('34000'))*mp.exp(-mp.mpf('12800')/(mp.mpf('8.314462618')*t))*(p/30)**mp.mpf('.34')*(1+mp.mpf('.12')*(c-1))*(1+mp.mpf('.08')*(b-1))
 mask0=(mp.mpf('7000') if v==1 else mp.mpf('7300'))*mp.exp(-mp.mpf('13800')/(mp.mpf('8.314462618')*t))*(p/30)**mp.mpf('.20')*(1+mp.mpf('.035')*(c-1))*(1+mp.mpf('.10')*(b-1))
 sf=(1+mp.mpf('.025')*r-mp.mpf('.012')*x+mp.mpf('.010')*y+mp.mpf('.004')*x*y) if v==1 else (1+mp.mpf('.015')*r-mp.mpf('.008')*x+mp.mpf('.009')*y+mp.mpf('.004')*x*y+mp.mpf('.025')*rr)
 sm=(1+mp.mpf('.012')*r+mp.mpf('.006')*x-mp.mpf('.003')*y) if v==1 else (1+mp.mpf('.016')*r+mp.mpf('.004')*x-mp.mpf('.005')*y+mp.mpf('.006')*rr)
 f=film0*sf;m=mask0*sm
 for key,value in [('filmRateNmPerMin',f),('maskRateNmPerMin',m),('selectivity',f/m),('filmDepthNm',f*mp.mpf(str(row.etchMinutes)))]:
  diff=abs(float(value)-float(row[key]));hi_max=max(hi_max,diff)
  assert diff<=3e-10*max(1,abs(float(value))),f'80-digit check failed {key} row={k}';high_precision+=1
summary={'status':'PASS','source':'Independent NumPy vectorized model and explicit mpmath model, not paceval expression parsing','point_rows':len(A),'functions_checked':len(checks),'elementwise_function_checks':number,'summary_checks':summaryChecks,'high_precision_80_digit_values':high_precision,'max_abs_differences_in_private_audit':max_abs,'max_abs_high_precision_in_private_audit':hi_max,'models':sorted(A.version.unique().tolist()),'recipes':int(A.recipe.nunique()),'quality_accept_count':int((A.booleanGate==1).sum()),'quality_reject_count':int((A.booleanGate==0).sum())}
(D/'independent_reference_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print('INDEPENDENT_VERIFICATION_PASS',len(A),number,summaryChecks,high_precision,'discreteAccept',summary['quality_accept_count'])
