#!/usr/bin/env python3
"""Render research charts exclusively from exported paceval CSV values."""
from pathlib import Path
import csv, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'figures';F.mkdir(exist_ok=True)
def rows(name):
 with (ROOT/'examples'/name).open(newline='') as f:return list(csv.DictReader(f))
P=rows('policy_metrics.csv');S=rows('scenario_samples.csv');T=rows('replenishment_surface.csv');R=rows('policy_registry.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.grid':True,'grid.alpha':.16,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(fig,key):
 fig.savefig(F/(key+'.png'),dpi=175,bbox_inches='tight');fig.savefig(F/(key+'.pdf'),bbox_inches='tight');plt.close(fig)
# 1 architecture
fig,ax=plt.subplots(figsize=(11,3));ax.axis('off')
labels=['Frozen SKU and\ndemand paths','30 versioned\npolicy pairs','60 reusable\npaceval graphs','C++ discrete\nstock simulator','Independent\nformula and KPI audit']
colors=['#e5edf2','#e5edf2','#c9edea','#e5edf2','#e5edf2']
for i,(t,co) in enumerate(zip(labels,colors)):
 x=.015+i*.204;ax.text(x+.085,.52,t,ha='center',va='center',transform=ax.transAxes,fontsize=10,fontweight='medium',bbox=dict(boxstyle='round,pad=.7',fc=co,ec='#267286'))
 if i<4: ax.annotate('',xy=(x+.196,.52),xytext=(x+.174,.52),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#d58350',lw=2))
ax.set_title('Explicit execution and validation boundary',fontweight='bold',pad=22);save(fig,'01_execution_architecture')
# 2 service distribution
by={i:[] for i in range(1,31)}
for r in P:by[int(r['policy_id'])].append(float(r['fill_rate']))
fig,ax=plt.subplots(figsize=(10,4.3));v=[np.mean(by[i]) for i in by]
ax.bar(list(by),v,color='#227d85');ax.set_ylim(0,1);ax.set_xlabel('Versioned reorder policy');ax.set_ylabel('Mean immediate-demand fill rate');ax.set_title('Observed synthetic 120-day lost-sales fill rate, 48 SKUs per policy');save(fig,'02_fill_rate_by_policy')
# 3 stock position / target difference
fig,ax=plt.subplots(figsize=(9.6,4.4));a=[r for r in S if int(r['policy_id']) in [1,15,30]]
for pid,color in [(1,'#187d8b'),(15,'#d87a43'),(30,'#3c566e')]:
 pts=[r for r in a if int(r['policy_id'])==pid];ax.scatter([float(r['inventory_position_units']) for r in pts],[float(r['target_minus_position_units']) for r in pts],s=11,alpha=.6,label=f'Policy {pid}',color=color)
ax.axhline(0,color='gray',lw=1);ax.set_xlabel('Initial inventory position (units)');ax.set_ylabel('Unrounded order-up-to gap (units)');ax.set_title('Scenario-level paceval formula evaluations');ax.legend();save(fig,'03_order_gap_by_inventory')
# 4 3D mathematically evaluated surface
x=np.array([float(r['mean_units_per_day']) for r in T]).reshape(61,61);y=np.array([float(r['sigma_units_per_day']) for r in T]).reshape(61,61);z=np.array([float(r['order_units']) for r in T]).reshape(61,61)
fig=plt.figure(figsize=(11,7));ax=fig.add_subplot(111,projection='3d');surf=ax.plot_surface(x,y,z,cmap='viridis',edgecolor='none',antialiased=True);ax.set_xlabel('Mean demand (units/day)',labelpad=5);ax.set_ylabel('Demand SD (units/day)',labelpad=5);ax.set_zlabel('Order units',labelpad=5);ax.set_title('Policy 15: 3,721 paceval-evaluated replenishment points');fig.colorbar(surf,shrink=.65,pad=.13,label='Rounded order units');save(fig,'04_replenishment_3d_surface')
# 5 contours
fig,ax=plt.subplots(figsize=(10,5));p=ax.contourf(x,y,z,levels=25,cmap='viridis');fig.colorbar(p,ax=ax,label='Rounded order units');ax.set_xlabel('Daily mean demand (units/day)');ax.set_ylabel('Daily demand SD (units/day)');ax.set_title('Replenishment response contour map (policy 15)');save(fig,'05_replenishment_contours')
# 6 trade-off
fig,ax=plt.subplots(figsize=(9.7,5));xx=np.array([float(q['average_onhand_units']) for q in P]);yy=np.array([float(q['fill_rate']) for q in P]);c=np.array([int(q['policy_id']) for q in P]);sc=ax.scatter(xx,yy,c=c,cmap='plasma',s=13,alpha=.5);fig.colorbar(sc,label='Policy ID');ax.set_ylim(0,1);ax.set_xlabel('Mean on-hand stock (units)');ax.set_ylabel('Demand fill rate');ax.set_title('Synthetic service–inventory trade-off across 1,440 simulation pairs');save(fig,'06_inventory_service_tradeoff')
# 7 policy comparison controls
fig,ax=plt.subplots(figsize=(10,4.6));ids=[int(q['policy_id']) for q in R];zz=[float(q['z_buffer_factor']) for q in R];rev=[int(q['review_days']) for q in R];ax.plot(ids,zz,'o-',color='#157d94',label='Safety factor z');ax.set_xlabel('Policy ID');ax.set_ylabel('Safety-stock multiplier z');ax2=ax.twinx();ax2.step(ids,rev,where='mid',color='#c06d36',label='Review period');ax2.set_ylabel('Review interval (days)');ax.set_title('30 explicitly registered policy configurations');save(fig,'07_policy_registry')
print('Rendered 7 numbered PNG/PDF scientific figures.')
