"""Rebuild all scientific PNG/vector PDF figures from actual SDK-exported CSVs."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'savefig.facecolor':'white','figure.facecolor':'white'})
pol=list(csv.DictReader(open(ROOT/'examples/policy_summary.csv')))
o=list(csv.DictReader(open(ROOT/'examples/offers.csv')))
s=list(csv.DictReader(open(ROOT/'examples/bid_surface.csv')))
v=list(csv.DictReader(open(ROOT/'examples/formula_version.csv')))
def save(i,name):
 for suffix in ['png','pdf']:plt.savefig(OUT/f'{i:02d}_{name}.{suffix}',dpi=180,bbox_inches='tight',pad_inches=.18)
 plt.close()
# 01: computation boundaries, diagram is an explanatory schematic, not computed data.
fig,ax=plt.subplots(figsize=(10,3));ax.set(xlim=(0,10),ylim=(0,3));ax.axis('off')
labels=['Offer inputs\n(cost, volume, risk)','paceval formula\n(reusable handle)','Host bid policy\n(floor / ceiling)','Audit and CSV\n(independent check)']
for i,label in enumerate(labels):
 x=.1+i*2.55;ax.text(x+1.05,1.5,label,ha='center',va='center',bbox=dict(boxstyle='round,pad=.55',fc='#e9f1f3' if i%2==0 else '#eff3ef',ec='#497b8d'),fontsize=10)
 if i<3:ax.annotate('',xy=(x+2.45,1.5),xytext=(x+2.19,1.5),arrowprops=dict(arrowstyle='->',lw=1.7))
ax.set_title('Explicit execution boundary: mathematical formula versus procurement policy');save(1,'architecture')
x=np.arange(1,51)
def figure_line(idx,name,key,title,ylab):
 fig,ax=plt.subplots(figsize=(9,4.4));y=np.array([float(r[key]) for r in pol]);ax.plot(x,y,'o-',ms=3,lw=1.1)
 for p in [10,20,30,40]:ax.axvline(p+.5,color='.8',lw=.7)
 ax.set(xlabel='Versioned bid policy',ylabel=ylab,title=title);ax.grid(alpha=.25);save(idx,name)
figure_line(2,'unit_bid_policies','mean_unit_bid_eur','Mean proposed unit bid by policy','EUR / item')
figure_line(3,'buyer_ceiling_eligibility','eligible_fraction','Fraction of offers below buyer ceiling','Eligible fraction')
figure_line(4,'gross_margin','mean_gross_margin_fraction','Realized gross margin fraction after floor adjustment','Fraction of bid')
# actual 61x61 paceval-calculated surface
q=np.unique([float(r['quantity']) for r in s]);vol=np.unique([float(r['volatility']) for r in s]);Z=np.array([float(r['unit_bid_eur']) for r in s]).reshape(len(q),len(vol));X,Y=np.meshgrid(q,vol,indexing='ij')
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d');h=ax.plot_surface(X,Y,Z,cmap='viridis',linewidth=0,antialiased=True)
ax.set(xlabel='Quantity (items)',ylabel='Volatility (dimensionless)',zlabel='Unit bid (EUR)',title='Actual paceval unit-bid response surface');fig.colorbar(h,ax=ax,shrink=.65,pad=.15,label='EUR / item');save(5,'bid_response_surface')
fig,ax=plt.subplots(figsize=(8,5));h=ax.contourf(X,Y,Z,levels=22,cmap='viridis');fig.colorbar(h,ax=ax,label='Unit bid (EUR)');ax.set(xlabel='Quantity (items)',ylabel='Volatility (dimensionless)',title='Same actual paceval parameter sweep as contour map');save(6,'bid_contours')
fig,ax=plt.subplots(figsize=(8,4.5));ax.plot([float(r['quantity']) for r in v],[float(r['version_1_eur']) for r in v],label='Version 1');ax.plot([float(r['quantity']) for r in v],[float(r['version_2_eur']) for r in v],label='Version 2',linestyle='--');ax.set(xlabel='Quantity (items)',ylabel='Unit bid (EUR)',title='Formula versioning: simultaneous reuse of v1 and v2');ax.legend();ax.grid(alpha=.25);save(7,'versioned_rule')
fig,ax=plt.subplots(figsize=(8,4.5));cost=np.array([float(r['unit_cost_eur']) for r in o]);bid=np.array([float(r['final_unit_bid_eur']) for r in o]);elig=np.array([int(r['eligible']) for r in o],dtype=bool)
ax.scatter(cost[~elig],bid[~elig],s=3,alpha=.3,label='Above buyer ceiling');ax.scatter(cost[elig],bid[elig],s=3,alpha=.25,label='Eligible');ax.set(xlabel='Unit cost (EUR)',ylabel='Final unit bid (EUR)',title='10,000 synthetic bids: cost and buyer-ceiling outcome');ax.legend(markerscale=4);save(8,'cost_bid_scatter')
print('8 figure pairs generated')
