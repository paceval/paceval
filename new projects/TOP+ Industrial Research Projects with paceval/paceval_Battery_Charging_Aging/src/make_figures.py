"""Scientific figures generated strictly from actual paceval SDK CSV exports.
No mathematical result is recomputed in this visualization script.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import ticker
from mpl_toolkits.mplot3d import Axes3D  # noqa
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
tr=pd.read_csv(ROOT/'examples/fixed_charging_and_driving_trace.csv')
sc=pd.read_csv(ROOT/'examples/optimized_schedule_comparison.csv')
ts=pd.read_csv(ROOT/'examples/optimized_schedule_timeseries.csv')
surf=pd.read_csv(ROOT/'examples/paceval_cost_aging_surface.csv')
plt.rcParams.update({'font.size':9.5,'axes.titlesize':12,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'figure.facecolor':'white','savefig.facecolor':'white','axes.grid':True,'grid.alpha':.18,'font.family':'DejaVu Sans'})

def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=185,bbox_inches='tight',pad_inches=.15)
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight',pad_inches=.15)
    plt.close(fig)

fig,ax=plt.subplots(figsize=(9.0,4.4))
for p,d in tr.groupby('scenario',sort=False):ax.plot(d.hour,d.tariff_EUR_per_kWh,label=p.replace('_',' '),lw=1.9)
ax.set(xlabel='Hour (synthetic day)',ylabel='Electricity price (EUR/kWh)',title='Six deterministic tariff profiles used in charging optimization',xlim=(0,23));ax.legend(loc='upper center',bbox_to_anchor=(.5,-.19),ncol=3,frameon=False,fontsize=8.1)
save(fig,'01_fixed_tariff_profiles')

n=int(np.sqrt(len(surf))); assert n*n==len(surf)
X=surf.power_kW.to_numpy().reshape(n,n);Y=surf.SOC.to_numpy().reshape(n,n)
Z=surf.paceval_total_v1_EUR_proxy.to_numpy().reshape(n,n)
fig=plt.figure(figsize=(8.6,5.1));ax=fig.add_subplot(111,projection='3d')
s=ax.plot_surface(X,Y,Z,cmap='viridis',linewidth=0,antialiased=True,alpha=.98)
ax.set(xlabel='Charge power (kW)',ylabel='Starting SOC',zlabel='Slot cost (EUR proxy)',title='3D composite slot objective, executed by paceval')
ax.view_init(elev=23,azim=-61);fig.colorbar(s,ax=ax,shrink=.62,pad=.1,label='Slot cost (EUR proxy)')
save(fig,'02_paceval_total_cost_surface_3d')

R=(surf.paceval_cycle_risk+surf.paceval_calendar_risk).to_numpy().reshape(n,n)
fig=plt.figure(figsize=(8.6,5.1));ax=fig.add_subplot(111,projection='3d')
s=ax.plot_surface(X,Y,R,cmap='plasma',linewidth=0,antialiased=True)
ax.set(xlabel='Charge power (kW)',ylabel='Starting SOC',zlabel='Synthetic risk units',title='3D synthetic cycle plus calendar aging surrogate')
ax.view_init(elev=25,azim=-61);fig.colorbar(s,ax=ax,shrink=.63,pad=.1,label='Synthetic risk units')
save(fig,'03_aging_surrogate_surface_3d')

fig,ax=plt.subplots(figsize=(8.5,4.7));c=ax.contourf(X,Y,Z,levels=24,cmap='viridis');ax.contour(X,Y,Z,levels=10,colors='k',linewidths=.35,alpha=.35)
ax.set(xlabel='Charge power (kW)',ylabel='Starting SOC',title='paceval composite cost: fixed synthetic temperature and tariff');fig.colorbar(c,ax=ax,label='EUR proxy / 1 h')
save(fig,'04_total_cost_contours')

s=ts[(ts.profile=='night_discount')&(ts.aging_weight==8)&(ts.formula_version==1)].sort_values('hour')
t=tr[tr.scenario=='night_discount'].sort_values('hour')
fig,ax=plt.subplots(figsize=(9.2,4.5));ax.bar(s.hour,s.charge_power_kW,alpha=.73,label='Optimized charging power (kW)')
ax.set(xlabel='Time slot (hour)',ylabel='Charge power (kW)',title='Tariff-aware 24-hour schedule, genuine paceval edge objectives',xlim=(-.7,23.7),ylim=(0,11.5))
a2=ax.twinx();a2.plot(t.hour,t.tariff_EUR_per_kWh,color='#c76b11',lw=2.4,marker='.',label='Synthetic price');a2.set_ylabel('Electricity price (EUR/kWh)');a2.set_ylim(0,.55)
ax.text(.05,.92,'Driving at 08:00 and 18:00',transform=ax.transAxes,fontsize=9)
save(fig,'05_optimized_charge_power_and_tariff')

fig,ax=plt.subplots(figsize=(9,4.5))
for profile in ['night_discount','evening_discount','wind_variation']:
 d=ts[(ts.profile==profile)&(ts.aging_weight==8)&(ts.formula_version==1)].sort_values('hour')
 hours=np.r_[0,d.hour.to_numpy()+1];soc=np.r_[d.SOC_before.iloc[0],d.SOC_after.to_numpy()]
 ax.step(hours,soc,where='post',label=profile.replace('_',' '),lw=2)
ax.axhline(.8,ls=':',lw=1.6,label='Terminal target 80%')
ax.axhline(.15,ls='--',lw=1,label='SOC lower limit 15%')
ax.set(xlabel='Hour',ylabel='State of charge (fraction)',title='24 h SOC trajectories, calculated by paceval transitions',xlim=(0,24),ylim=(.12,.94));ax.legend(loc='lower right',fontsize=8)
save(fig,'06_charge_schedule_soc_trajectories')

fig,ax=plt.subplots(figsize=(8.6,4.8))
for w,d in sc[sc.formula_version==1].groupby('aging_weight'):
 ax.scatter(d.electricity_cost_EUR,d.synthetic_risk_units,s=68,alpha=.88,label=f'Aging weight {w:g} EUR/risk')
for _,r in sc[(sc.formula_version==1)&(sc.aging_weight==30)].iterrows():ax.annotate(r.profile.replace('_',' '),(r.electricity_cost_EUR,r.synthetic_risk_units),xytext=(4,4),textcoords='offset points',fontsize=7)
ax.set(xlabel='Synthetic electricity cost (EUR)',ylabel='Synthetic risk units (not battery fade)',title='Electricity-cost vs synthetic aging-risk tradeoffs');ax.legend(loc='upper right',fontsize=8)
save(fig,'07_electricity_vs_aging_tradeoff')

piv=sc.pivot_table(index=['profile','aging_weight'],columns='formula_version',values='total_objective_EUR_proxy').reset_index();piv['diff']=piv[2]-piv[1]
fig,ax=plt.subplots(figsize=(8.9,4.4))
for w, d in piv.groupby('aging_weight'):ax.plot(d.profile,d['diff'],marker='o',lw=2,label=f'Weight {w:g}')
ax.set(xlabel='Synthetic price-profile family',ylabel='Version 2 minus V1 objective (EUR proxy)',title='Two simultaneously retained paceval cost-function versions')
plt.setp(ax.get_xticklabels(),rotation=23,ha='right');ax.legend(fontsize=8)
save(fig,'08_versioned_cost_functions')

m=surf[np.isclose(surf.SOC, surf.SOC.unique()[n//2])].sort_values('power_kW')
fig,ax=plt.subplots(figsize=(8.6,4.4));ax.plot(m.power_kW,m.paceval_marginal_cost_EUR_per_kW,lw=2.5)
ax.set(xlabel='Charge power (kW)',ylabel='dJ/dP (EUR proxy per kW)',title='Analytical marginal slot objective, directly evaluated by paceval')
save(fig,'09_analytical_marginal_cost')

sel=ts[(ts.aging_weight==8)&(ts.formula_version==1)].pivot(index='profile',columns='hour',values='charge_power_kW')
fig,ax=plt.subplots(figsize=(10,4.2));img=ax.imshow(sel.values,cmap='YlGnBu',aspect='auto',vmin=0,vmax=10)
ax.set(xticks=np.arange(0,24,2),yticks=np.arange(len(sel)),yticklabels=[x.replace('_',' ') for x in sel.index],xlabel='Hour of synthetic day',title='Optimized paceval-evaluated charging power, six price profiles')
ax.set_xticklabels(list(range(0,24,2)));fig.colorbar(img,ax=ax,label='Charge power (kW)')
save(fig,'10_optimized_schedules_heatmap')

print('Created 10 charts x 2 formats, all from actual C++/paceval CSV outputs.')
