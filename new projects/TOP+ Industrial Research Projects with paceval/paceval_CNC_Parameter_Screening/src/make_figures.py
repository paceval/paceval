"""Generate all scientific figures ONLY from the published paceval-output CSVs."""
from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
R=Path(__file__).resolve().parents[1];F=R/'figures';E=R/'examples';F.mkdir(exist_ok=True)
c=pd.read_csv(E/'screening_candidates.csv');s=pd.read_csv(E/'cnc_response_surface.csv');v=pd.read_csv(E/'formula_revision.csv')
plt.rcParams.update({'font.size':9,'axes.titlesize':12,'axes.labelsize':9,'figure.facecolor':'white','savefig.facecolor':'white','savefig.dpi':190})
def save(name):
 plt.savefig(F/(name+'.png'),bbox_inches='tight',pad_inches=.22)
 plt.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.22)
 plt.close()
def surface(z,name,title,zlabel):
 x=s.vc_m_min.to_numpy().reshape(61,61);y=s.fz_mm_tooth.to_numpy().reshape(61,61);z=s[z].to_numpy().reshape(61,61)
 fig=plt.figure(figsize=(8.5,5.7));ax=fig.add_subplot(projection='3d');mesh=ax.plot_surface(x,y,z,cmap='viridis',linewidth=0,antialiased=True,alpha=.97)
 ax.set_xlabel('Cutting speed (m/min)',labelpad=10);ax.set_ylabel('Feed / tooth (mm)',labelpad=10);ax.set_zlabel(zlabel,labelpad=10)
 ax.view_init(elev=28,azim=-125);ax.set_title(title,pad=14);fig.colorbar(mesh,shrink=.65,aspect=20,pad=.12);save(name)
surface('mrr_cm3_min','01_mrr_surface','Material removal rate | synthetic milling sweep','MRR (cm³/min)')
surface('motor_kW','02_power_surface','Estimated spindle demand | synthetic sweep','Motor power (kW)')
surface('life_proxy_min','03_tool_life_surface','Illustrative tool-life response | not calibrated','Life proxy (min)')
fig,ax=plt.subplots(figsize=(8.3,5.1));z=s.motor_kW.to_numpy().reshape(61,61);cs=ax.contourf(s.vc_m_min.to_numpy().reshape(61,61),s.fz_mm_tooth.to_numpy().reshape(61,61),z,levels=19,cmap='viridis');fig.colorbar(cs,ax=ax,label='Motor power (kW)');ax.set(xlabel='Cutting speed (m/min)',ylabel='Feed per tooth (mm)',title='Power contour map | direct paceval data');save('04_power_contours')
fig,axs=plt.subplots(1,2,figsize=(10.1,4));c.feasible.value_counts().reindex([1,0],fill_value=0).plot.bar(ax=axs[0],color=['#218377','#B76A44']);axs[0].set_xticklabels(['Feasible','Screened out'],rotation=0);axs[0].set(ylabel='Candidates',title='Synthetic constraint decisions');axs[1].scatter(c.loc[c.feasible==0,'mrr_cm3_min'],c.loc[c.feasible==0,'motor_kW'],s=4,alpha=.25,label='Screened out',color='#b86b49');axs[1].scatter(c.loc[c.feasible==1,'mrr_cm3_min'],c.loc[c.feasible==1,'motor_kW'],s=4,alpha=.3,label='Feasible',color='#168888');axs[1].set(xlabel='MRR (cm³/min)',ylabel='Motor power (kW)',title='Candidate trade-off');axs[1].legend(fontsize=8);save('05_screening_decisions')
fig,ax=plt.subplots(figsize=(8.3,4.6));ax.scatter(c.mrr_cm3_min,c.life_proxy_min,c=c.feasible,cmap='coolwarm',s=5,alpha=.6);ax.axhline(18,color='black',lw=1,ls='--',label='Illustrative life-proxy threshold');ax.set(xlabel='MRR (cm³/min)',ylabel='Life proxy (min)',title='Throughput versus illustrative tool-life constraint');ax.set_ylim(0,175);ax.legend();save('06_life_tradeoff')
fig,ax=plt.subplots(figsize=(8.3,4.8));ax.plot(v.vc_m_min,v.cost_v1,label='Original cost expression',lw=2);ax.plot(v.vc_m_min,v.cost_v2,label='Revision (new graph)',lw=2);ax.set(xlabel='Cutting speed (m/min)',ylabel='Dimensionless cost',title='Controlled immutable cost-formula revision');ax.legend();save('07_formula_revision')
fig,ax=plt.subplots(figsize=(8.3,4.8));groups=[c[c.rule_id.between(k*10,(k+1)*10-1)].cost for k in range(5)];ax.boxplot(groups,tick_labels=['F1','F2','F3','F4','F5'],showfliers=False);ax.set(xlabel='Score-expression family',ylabel='Dimensionless score (not comparable between families)',title='Five separately normalized illustrative score families');save('08_cost_family_distribution')
fig,ax=plt.subplots(figsize=(8.3,4.8));x=s.vc_m_min.to_numpy().reshape(61,61);y=s.fz_mm_tooth.to_numpy().reshape(61,61);z=s.life_proxy_min.to_numpy().reshape(61,61);cs=ax.contourf(x,y,z,levels=16,cmap='cividis');ax.contour(x,y,z,levels=[18],colors='red',linewidths=1.5);fig.colorbar(cs,ax=ax,label='Life proxy (min)');ax.set(xlabel='Cutting speed (m/min)',ylabel='Feed / tooth (mm)',title='Illustrative wear constraint boundary (red = 18 min)');save('09_tool_life_boundary')
print('PASS nine scientific figures generated from actual paceval CSV exports')
