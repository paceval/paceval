#!/usr/bin/env python3
"""Plot the actual original paceval C++ execution CSVs; never calculate PK output values."""
import argparse,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import cm
COL={'ink':'#442c39','coral':'#c34f35','rose':'#e28b72','sage':'#3e786f','gold':'#bb8c41','light':'#f8f5f1','slate':'#5c5962'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.grid':True,'grid.alpha':.15,'savefig.facecolor':'white'})
def load(path):
 with open(path,newline='') as f:return list(csv.DictReader(f))
def save(fig,folder,num,slug,title,caption,manifest):
 path=f'{num:02d}_{slug}';fig.savefig(folder/(path+'.png'),dpi=240,bbox_inches='tight',pad_inches=.20);fig.savefig(folder/(path+'.pdf'),bbox_inches='tight',pad_inches=.2)
 plt.close(fig);manifest.append((path,title,caption,'results/scenario_summary.csv; results/concentration_trajectories.csv; results/graph_probe.csv'))
def run(root,folder):
 folder.mkdir(exist_ok=True,parents=True)
 r=load(root/'results/scenario_summary.csv');t=load(root/'results/concentration_trajectories.csv')
 x={}
 for z in r:
  key=(int(z['virtual_profile_id']),int(z['model_version']),z['route']);x[key]=z
 trace={}
 for z in t:
  key=(int(z['virtual_profile_id']),int(z['model_version']),z['route']);trace.setdefault(key,[]).append(z)
 def num(rec,key):return float(rec[key])
 def scat(sub,key):return [num(z,key) for z in sub]
 manifest=[]
 # 01 workflow design: a schematic, not a computed measurement
 fig,ax=plt.subplots(figsize=(10.7,3.0));ax.set(xlim=(0,11.5),ylim=(0,3));ax.axis('off');ax.grid(False)
 labels=[('Virtual profiles','weight, covariate\nrate parameters'),('Dosing events','oral input or\nIV infusion rate'),('paceval graphs','CL, V, exact states\nAUC, scores'),('C++ controller','event schedule\nstate, aggregation'),('PK outputs','AUC, Cmax,\nsensitivity, guards')]
 for i,(h,b) in enumerate(labels):
  pos=.15+i*2.3
  ax.add_patch(FancyBboxPatch((pos,.78),2.03,1.48,boxstyle='round,pad=.10,rounding_size=.20',edgecolor=COL['coral'] if i==2 else COL['sage'],facecolor='#fff1eb' if i==2 else '#edf4f0',linewidth=1.6))
  ax.text(pos+1.02,1.78,h,ha='center',va='center',fontweight='bold',fontsize=10,color=COL['ink']);ax.text(pos+1.02,1.23,b,ha='center',va='center',fontsize=8.8,color=COL['slate'])
  if i<4:ax.add_patch(FancyArrowPatch((pos+2.13,1.5),(pos+2.29,1.5),arrowstyle='-|>',mutation_scale=16,color=COL['coral']))
 fig.suptitle('Research workflow: persistent mathematical kernels in a synthetic PK simulation',color=COL['ink'],fontweight='bold',fontsize=13)
 save(fig,folder,1,'application_workflow','Application workflow','Schematic separation of covariate inputs, exact paceval state formulas and host-managed events.',manifest)
 # 02 clinical-inspired concentration time series of one virtual profile
 fig,ax=plt.subplots(figsize=(9.0,5.3))
 for ver,route,co in [(1,'oral',COL['sage']),(2,'oral',COL['coral']),(2,'iv_infusion',COL['gold'])]:
  seq=trace[(19,ver,route)];ax.plot(scat(seq,'time_h'),scat(seq,'concentration_mg_per_L'),label=f'v{ver}, {route.replace("_"," ")}',linewidth=2,color=co)
 for tt in (24,48,72):ax.axvline(tt,color=COL['slate'],alpha=.23,linestyle=':')
 ax.set(title='Concentration-time profiles of a synthetic virtual subject',xlabel='Time since first administration (h)',ylabel='Modelled plasma concentration (mg/L)');ax.legend(frameon=False)
 save(fig,folder,2,'virtual_profile_concentration','Concentration time course','Four nominal administrations are modelled as oral input or two-hour IV infusions; no clinical drug is represented.',manifest)
 # 03 oral AUC vs renal factor for common weight 70 kg
 fig,ax=plt.subplots(figsize=(8.6,5.1))
 for v in (1,2):
  ss=sorted((z for z in r if int(z['model_version'])==v and z['route']=='oral' and float(z['weight_kg'])==70),key=lambda z:num(z,'renal_covariate_dimensionless'))
  ax.plot(scat(ss,'renal_covariate_dimensionless'),scat(ss,'AUC0_h_mg_h_per_L'),marker='o',color=COL['sage'] if v==1 else COL['coral'],label=f'Covariate model v{v}',linewidth=2.2)
 ax.set(title='Repeated-dose oral exposure and the renal covariate',xlabel='Synthetic renal multiplier (dimensionless)',ylabel='AUC 0–96 h (mg·h/L)');ax.legend(frameon=False)
 save(fig,folder,3,'exposure_by_renal_covariate','Renal multiplier and exposure','The two simultaneously available clearance graph versions produce different virtual exposure responses.',manifest)
 # 04 3D exposure surface 
 from mpl_toolkits.mplot3d import Axes3D # noqa
 f=plt.figure(figsize=(9.2,6.5));ax=f.add_subplot(111,projection='3d')
 ss=[z for z in r if int(z['model_version'])==2 and z['route']=='oral'];w=sorted({num(z,'weight_kg') for z in ss});q=sorted({num(z,'renal_covariate_dimensionless') for z in ss})
 X,Y=np.meshgrid(w,q,indexing='ij');dictz={(num(z,'weight_kg'),num(z,'renal_covariate_dimensionless')):num(z,'AUC0_h_mg_h_per_L') for z in ss};Z=np.array([[dictz[(a,b)] for b in q] for a in w]);surf=ax.plot_surface(X,Y,Z,cmap='Oranges',edgecolor='white',linewidth=.3,antialiased=True,alpha=.97)
 ax.view_init(elev=27,azim=-124);ax.set(xlabel='Weight (kg)',ylabel='Renal multiplier (1)',zlabel='AUC 0–96 h (mg·h/L)');ax.set_title('Model v2: repeated-dose exposure across virtual covariates',pad=17)
 f.colorbar(surf,ax=ax,shrink=.62,pad=.12,label='AUC 0–96 h (mg·h/L)');f.subplots_adjust(left=.01,right=.93,bottom=.05,top=.90)
 save(f,folder,4,'exposure_surface_3d','Three-dimensional exposure surface','The 42 values forming the surface are actual paceval evaluation results from the v2 oral cohort.',manifest)
 # 05 model revision surface differential data from two executed graphs/versions
 v1={(num(z,'weight_kg'),num(z,'renal_covariate_dimensionless')):num(z,'AUC0_h_mg_h_per_L') for z in r if int(z['model_version'])==1 and z['route']=='oral'}
 f,ax=plt.subplots(figsize=(8.5,5.6))
 D=np.array([[dictz[(a,b)]-v1[(a,b)] for b in q] for a in w])
 heat=ax.pcolormesh(X,Y,D,cmap='PuOr',shading='nearest')
 ax.set(title='Controlled model revision: oral AUC(v2) - AUC(v1)',xlabel='Weight (kg)',ylabel='Renal multiplier (dimensionless)')
 f.colorbar(heat,ax=ax,label='AUC difference (mg·h/L)')
 save(f,folder,5,'model_revision_exposure_map','Model revision difference','The difference is formed exclusively from v1 and v2 exposure values computed by paceval.',manifest)
 # 06 sampled peak by weight, for common renal factor
 f,ax=plt.subplots(figsize=(8.6,5.0))
 for route,c in [('oral',COL['coral']),('iv_infusion',COL['sage'])]:
  ss=sorted((z for z in r if int(z['model_version'])==2 and z['route']==route and float(z['renal_covariate_dimensionless'])==1.0),key=lambda z:num(z,'weight_kg'))
  ax.plot(scat(ss,'weight_kg'),scat(ss,'Cmax_sampled_mg_per_L'),marker='o',label=route.replace('_',' '),color=c,linewidth=2.2)
 ax.set(title='Sampled maximum concentration across body-weight scenarios',xlabel='Virtual body weight (kg)',ylabel='Sampled Cmax (mg/L)');ax.legend(frameon=False)
 save(f,folder,6,'peak_concentration_by_weight','Peak concentration and weight','Sampled peaks reflect the exact original paceval state graph evaluated at 0.25 h resolution.',manifest)
 # 07 time-series across 3 subjects
 f,ax=plt.subplots(figsize=(9,5.0))
 for i,c in [(1,COL['coral']),(19,COL['sage']),(42,COL['gold'])]:
  seq=trace[(i,2,'oral')];ax.plot(scat(seq,'time_h'),scat(seq,'concentration_mg_per_L'),label=f'Virtual profile {i}',color=c,linewidth=2)
 ax.set(title='Virtual-subject variability under one repeated oral regimen',xlabel='Time (h)',ylabel='Modelled concentration (mg/L)');ax.legend(frameon=False)
 save(f,folder,7,'virtual_subject_variability','Synthetic subject variability','Distinct profiles vary in weight, renal multiplier, fixed random effects, absorption and bioavailability.',manifest)
 # 08 AUC versus Cmax scatter
 f,ax=plt.subplots(figsize=(8.5,5.4))
 for route,c in [('oral',COL['coral']),('iv_infusion',COL['sage'])]:
  ss=[z for z in r if int(z['model_version'])==2 and z['route']==route]
  ax.scatter(scat(ss,'AUC0_h_mg_h_per_L'),scat(ss,'Cmax_sampled_mg_per_L'),s=38,alpha=.8,color=c,label=route.replace('_',' '))
 ax.set(title='Exposure and peak concentration are distinct readouts',xlabel='AUC 0–96 h (mg·h/L)',ylabel='Sampled Cmax (mg/L)');ax.legend(frameon=False)
 save(f,folder,8,'auc_peak_joint_distribution','Joint exposure and peak responses','AUC and sampled Cmax are generated by different reduction rules from the same paceval exact states.',manifest)
 # 09 CL model differences on 70kg
 f,ax=plt.subplots(figsize=(8.5,5.0))
 for v,c in [(1,COL['sage']),(2,COL['coral'])]:
  ss=sorted((z for z in r if int(z['model_version'])==v and z['route']=='oral' and float(z['weight_kg'])==70),key=lambda z:num(z,'renal_covariate_dimensionless'))
  ax.plot(scat(ss,'renal_covariate_dimensionless'),scat(ss,'CL_L_per_h'),marker='s',linewidth=2,color=c,label=f'Clearance v{v}')
 ax.set(title='Two retained virtual clearance-covariate formulas',xlabel='Synthetic renal multiplier (dimensionless)',ylabel='Clearance (L/h)');ax.legend(frameon=False)
 save(f,folder,9,'versioned_clearance_covariate','Versioned clearance response','The difference comes from the controlled v1 linear versus v2 quadratic covariate terms.',manifest)
 # 10 distance to illustrative concentration ceiling
 f,ax=plt.subplots(figsize=(9,5.0))
 for p,c in [(1,COL['coral']),(19,COL['sage']),(42,COL['gold'])]:
  seq=trace[(p,2,'oral')];ax.plot(scat(seq,'time_h'),scat(seq,'illustrative_upper_margin_mg_per_L'),label=f'Virtual profile {p}',color=c,linewidth=2)
 ax.axhline(0,linestyle='--',color=COL['slate'],linewidth=.9)
 ax.set(title='Numerical concentration margins (not clinical thresholds)',xlabel='Time (h)',ylabel='Illustrative 6 mg/L ceiling − C (mg/L)');ax.legend(frameon=False)
 save(f,folder,10,'illustrative_concentration_margin','Concentration guard margin','The 6 mg/L ceiling is an arbitrary numerical illustration, not an efficacy or toxicity boundary.',manifest)
 with (root/'results/figure_manifest.csv').open('w',newline='') as fp:
  wr=csv.writer(fp);wr.writerow(['figure_id','title','caption','data_provenance']);wr.writerows(manifest)
 print('FIGURES GENERATED',len(manifest),folder)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--figures',type=Path,default=None);a=p.parse_args();run(a.root,a.figures or a.root/'figures')
