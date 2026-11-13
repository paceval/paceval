#!/usr/bin/env python3
"""Recreate publication figures ONLY from the executed paceval output CSVs.
Hero is a separate concept illustration. Architecture is a static schematic.
"""
import argparse,csv,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
NAVY='#16314d'; TEAL='#087e87'; ORANGE='#d58c36'; INK='#1e3040'; PALE='#d7e7e9'
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,
 'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.edgecolor':'#738b9a',
 'axes.labelcolor':INK,'text.color':INK,'savefig.facecolor':'white','grid.alpha':.24,'lines.linewidth':1.8})
CAPTIONS={
 '01_workflow_architecture':'Schematic calculation chain. Building inputs and model parameters enter persistent paceval graphs; host-side orchestration and independent verification complete the workflow.',
 '02_observed_and_predicted_temperature':'Teacher-forced one-step indoor-temperature forecasts over 96 synthetic hours, using the v2-selected parameter tuple for both model versions.',
 '03_residual_by_model':'One-step temperature residuals for both revision formulas against the same deterministic synthetic observations.',
 '04_parameter_cost_surface_3d':'Actual paceval calibration-loss surface for version 2 at C = 7.2 MJ/K and alpha = 0.65, across envelope and wind-dependent conductance parameters.',
 '05_parameter_cost_contours':'Contour map of the same executed calibration grid; the low-cost region indicates potential parameter trade-offs, not parameter uniqueness.',
 '06_heat_demand_proxy':'Signed instantaneous equilibrium heating demand proxy from both graph versions. This is not measured HVAC power nor an optimized controller command.',
 '07_temperature_guard_margins':'Version-2 one-step forecast margins to the illustrative 18–25 °C acceptable indoor-temperature band.',
 '08_weighted_cost_versions':'Fifteen simultaneous cost graph variants per model evaluated at an identical v2-selected parameter tuple. Variant 01 is a residual-only baseline.',
 '09_calibration_sensitivity':'Analytical derivative of the version-2 baseline squared-residual score with respect to the envelope conductance UA.',
 '10_selected_cost_by_heat_capacity':'Minimum squared-residual score by thermal capacitance on the executed grid, separately optimizing other grid parameters for each model version.'}

def data(path):
 with path.open() as f:return list(csv.DictReader(f))
def save(fig,out,name):
 fig.savefig(out/f'{name}.png',dpi=235,bbox_inches='tight',pad_inches=.17)
 fig.savefig(out/f'{name}.pdf',bbox_inches='tight',pad_inches=.17)
 plt.close(fig)
def main(root,out):
 out.mkdir(parents=True,exist_ok=True)
 s=data(root/'results/time_series.csv');sw=data(root/'results/model_sweep.csv');v=data(root/'results/score_variants.csv');
 log=(root/'results/sdk_execution.txt').read_text();assert 'original paceval SDK execution SUCCESS' in log
 t=np.arange(len(s))*.25
 vals=lambda c:np.array([float(r[c]) for r in s]);
 # A schematic is not an executed result and is labelled as such.
 fig,ax=plt.subplots(figsize=(9.8,2.8));ax.set(xlim=(0,10),ylim=(0,3));ax.axis('off')
 labels=[('Weather + HVAC\nZone observations',0.0),('18-input\nscenario rows',2.1),('62 paceval\nexecution graphs',4.3),('Model outputs\n+ score variants',6.5),('Host ranking\n+ independent audit',8.6)]
 for j,(label,x) in enumerate(labels):
  color=NAVY if j in (0,4) else TEAL
  ax.add_patch(plt.Rectangle((x,.8),1.5,1.25,facecolor=color,edgecolor='none',zorder=2))
  ax.text(x+.75,1.43,label,ha='center',va='center',color='white',fontsize=9,weight='bold',zorder=3)
  if j<len(labels)-1:ax.annotate('',(x+2.05,1.42),(x+1.53,1.42),arrowprops=dict(arrowstyle='-|>',color=ORANGE,lw=2))
 ax.set_title('Schematic: building thermal-twin calculation workflow',loc='left',pad=14)
 save(fig,out,'01_workflow_architecture')
 # Temperatures
 fig,ax=plt.subplots(figsize=(9.7,4.3));ax.plot(t,vals('observed_degC'),color=INK,alpha=.9,label='Synthetic observation');ax.plot(t,vals('pred_v1_degC'),color=ORANGE,label='Version 1 (fixed envelope)');ax.plot(t,vals('pred_v2_degC'),color=TEAL,label='Version 2 (wind + shading)');ax.set(xlabel='Time (h)',ylabel='Indoor temperature (°C)',title='One-step indoor-temperature predictions');ax.grid(True);ax.legend(ncol=3,fontsize=8.5,loc='upper right');save(fig,out,'02_observed_and_predicted_temperature')
 fig,ax=plt.subplots(figsize=(9.3,4.1));ax.plot(t,vals('residual_v1_K'),color=ORANGE,label='Version 1');ax.plot(t,vals('residual_v2_K'),color=TEAL,label='Version 2');ax.axhline(0,color=INK,ls=':',lw=1);ax.set(xlabel='Time (h)',ylabel='Prediction − observation (K)',title='Calibration residuals across the synthetic sequence');ax.grid(True);ax.legend();save(fig,out,'03_residual_by_model')
 # Cost grid on capacity C=7.2e6, exact dataset
 sub=[r for r in sw if r['version']=='v2' and abs(float(r['C_JperK'])-7200000)<1];u=sorted({float(r['UA_WperK']) for r in sub});k=sorted({float(r['kwind_WperKmps']) for r in sub});z=np.full((len(k),len(u)),np.nan)
 for r in sub:z[k.index(float(r['kwind_WperKmps'])),u.index(float(r['UA_WperK']))]=float(r['mean_squared_residual_K2'])
 assert np.isfinite(z).all() and z.size>=25
 U,K=np.meshgrid(u,k)
 fig=plt.figure(figsize=(9.1,5.8));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(U,K,z,cmap='viridis',edgecolor='white',linewidth=.35,alpha=.98);ax.set(xlabel='UA (W/K)',ylabel='Wind coefficient (W/K per m/s)',zlabel='Mean residual² (K²)',title='Executed model-v2 calibration grid (C = 7.2 MJ/K)');ax.view_init(elev=26,azim=-125);fig.colorbar(surf,ax=ax,shrink=.67,pad=.15,label='Mean squared residual (K²)');save(fig,out,'04_parameter_cost_surface_3d')
 fig,ax=plt.subplots(figsize=(8.8,4.9));cf=ax.contourf(U,K,z,levels=20,cmap='viridis');ax.contour(U,K,z,levels=8,linewidths=.4,colors='#f5fafb',alpha=.7);ax.scatter([210],[50],color='white',edgecolor='black',s=73,label='Grid-selected v2 candidate',zorder=3);fig.colorbar(cf,ax=ax,label='Mean squared residual (K²)');ax.set(xlabel='UA (W/K)',ylabel='Wind coefficient (W/K per m/s)',title='Cost map: wind transfer versus envelope conductance');ax.legend(fontsize=9);save(fig,out,'05_parameter_cost_contours')
 fig,ax=plt.subplots(figsize=(9.5,4.0));ax.plot(t,vals('required_heat_v1_W')/1000,color=ORANGE,label='Version 1');ax.plot(t,vals('required_heat_v2_W')/1000,color=TEAL,label='Version 2');ax.axhline(0,color=INK,ls=':');ax.set(xlabel='Time (h)',ylabel='Signed demand proxy (kW)',title='Equilibrium heating demand proxy (illustrative setpoint)');ax.grid(True);ax.legend();save(fig,out,'06_heat_demand_proxy')
 fig,ax=plt.subplots(figsize=(9.5,4.1));ax.plot(t,vals('lower_margin_v2_K'),color=ORANGE,label='Above 18 °C floor');ax.plot(t,vals('upper_margin_v2_K'),color=TEAL,label='Below 25 °C ceiling');ax.axhline(0,color=INK,ls='--');ax.set(xlabel='Time (h)',ylabel='One-step margin (K)',title='Temperature-constraint margins computed by paceval');ax.grid(True);ax.legend();save(fig,out,'07_temperature_guard_margins')
 score=lambda mod:[float(next(r['mean_cost'] for r in v if r['function_id']==f'score_{mod}_{i:02d}')) for i in range(1,16)]
 fig,ax=plt.subplots(figsize=(9.7,4.7));xx=np.arange(1,16);ax.plot(xx,score('v1'),marker='o',ms=4,color=ORANGE,label='Version 1');ax.plot(xx,score('v2'),marker='s',ms=4,color=TEAL,label='Version 2');ax.set(xlabel='Cost-formula variant',ylabel='Mean weighted score (arbitrary units)',title='Versioned objective functions on a common parameter set');ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.grid(True);ax.legend();save(fig,out,'08_weighted_cost_versions')
 fig,ax=plt.subplots(figsize=(9.5,4.1));ax.plot(t,vals('ds_dUA_v2'),color=TEAL);ax.axhline(0,color=INK,lw=1,ls=':');ax.set(xlabel='Time (h)',ylabel='∂(residual²)/∂UA (K² /(W/K))',title='Executed analytic calibration-loss sensitivity');ax.grid(True);save(fig,out,'09_calibration_sensitivity')
 fig,ax=plt.subplots(figsize=(9.2,4.4));
 for ver,col in [('v1',ORANGE),('v2',TEAL)]:
  caps=sorted(set(float(x['C_JperK'])/1e6 for x in sw if x['version']==ver))
  mins=[min(float(x['mean_squared_residual_K2']) for x in sw if x['version']==ver and abs(float(x['C_JperK'])/1e6-c)<1e-8) for c in caps]
  ax.plot(caps,mins,marker='o',label='Version '+ver[1:],color=col)
 ax.set(xlabel='Thermal capacitance C (MJ/K)',ylabel='Best grid mean residual² (K²)',title='Calibration-loss sensitivity to thermal capacitance');ax.grid(True);ax.legend();save(fig,out,'10_selected_cost_by_heat_capacity')
 for n,cap in CAPTIONS.items():
  assert (out/(n+'.png')).is_file() and (out/(n+'.pdf')).is_file()
 (root/'results/figure_manifest.csv').write_text('figure,provenance,caption\n'+''.join(f'{n},'+('schematic_not_computed' if n.startswith('01_') else 'executed_paceval_csv')+',"'+cap+'"\n' for n,cap in CAPTIONS.items()))
 print('Generated',len(CAPTIONS),'pairs of vector PDF/high-resolution PNG figures from paceval data')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--figures',type=Path,default=Path('figures'));a=p.parse_args();main(a.root,a.figures)
